import os
import cv2
import tempfile
import numpy as np
from pathlib import Path
from stabilization import TemporalStabilizer
from restoration import FaceRestorer
from ffmpeg_utils import extract_audio, mux_frames_and_audio
from identity import IdentityAggregator, get_face_app
from swapper import swap_face

class JobProcessor:
    def __init__(self):
        self.stabilizer = TemporalStabilizer()
        self.restorer = FaceRestorer()
        self.identity_aggregator = IdentityAggregator()

    @staticmethod
    def _restore_face_region(image, bbox, restorer):
        h, w = image.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2-x1, 1), max(y2-y1, 1)
        mx, my = max(int(fw*.35),16), max(int(fh*.45),16)
        rx1, ry1, rx2, ry2 = max(0,x1-mx), max(0,y1-my), min(w,x2+mx), min(h,y2+my)
        if rx2 <= rx1 or ry2 <= ry1: return image
        crop = image[ry1:ry2, rx1:rx2].copy()
        restored = restorer.restore(crop)
        if restored is None or restored.shape != crop.shape: return image
        mask = np.zeros(crop.shape[:2], dtype=np.float32)
        cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.58),8),max(int(fh*.72),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.08,2))[...,None]
        image[ry1:ry2,rx1:rx2] = (restored.astype(np.float32)*mask + crop.astype(np.float32)*(1-mask)).clip(0,255).astype(np.uint8)
        return image

    @staticmethod
    def _preserve_target_detail(original, swapped, bbox, strength=0.72):
        """Transfer only high-frequency target texture onto the swapped face.
        This keeps the new identity while recovering pores, hairline detail and
        local contrast that are lost when the 128px swap model reconstructs the face.
        """
        h, w = original.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2-x1,1), max(y2-y1,1)
        mx, my = max(int(fw*.22),10), max(int(fh*.28),10)
        rx1, ry1 = max(0,x1-mx), max(0,y1-my)
        rx2, ry2 = min(w,x2+mx), min(h,y2+my)
        if rx2 <= rx1 or ry2 <= ry1: return swapped

        src = original[ry1:ry2,rx1:rx2].astype(np.float32)
        dst = swapped[ry1:ry2,rx1:rx2].astype(np.float32)

        # Use luminance detail only, so target colour/identity is not reintroduced.
        src_y = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_BGR2YCrCb)[...,0].astype(np.float32)
        dst_ycc = cv2.cvtColor(dst.astype(np.uint8), cv2.COLOR_BGR2YCrCb).astype(np.float32)
        src_low = cv2.GaussianBlur(src_y,(0,0),1.35)
        detail = src_y - src_low
        detail = cv2.GaussianBlur(detail,(0,0),0.35)

        # Avoid transferring compression/noise too aggressively.
        detail = np.clip(detail, -22.0, 22.0)
        dst_ycc[...,0] = np.clip(dst_ycc[...,0] + detail * strength, 0, 255)
        detailed = cv2.cvtColor(dst_ycc.astype(np.uint8), cv2.COLOR_YCrCb2BGR)

        mask = np.zeros((ry2-ry1,rx2-rx1), dtype=np.float32)
        cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.62),8),max(int(fh*.78),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.055,1.5))[...,None]
        dst = dst*(1-mask) + detailed.astype(np.float32)*mask
        swapped[ry1:ry2,rx1:rx2] = np.clip(dst,0,255).astype(np.uint8)
        return swapped

    @staticmethod
    def _sharpen_face_region(image, bbox):
        h, w = image.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2-x1,1), max(y2-y1,1)
        mx, my = max(int(fw*.18),8), max(int(fh*.18),8)
        rx1, ry1, rx2, ry2 = max(0,x1-mx), max(0,y1-my), min(w,x2+mx), min(h,y2+my)
        crop = image[ry1:ry2,rx1:rx2].copy()
        if crop.size == 0: return image
        blur = cv2.GaussianBlur(crop,(0,0),1.05)
        sharp = cv2.addWeighted(crop,1.32,blur,-0.32,0)
        mask = np.zeros(crop.shape[:2],dtype=np.float32)
        cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.62),8),max(int(fh*.76),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.07,1.5))[...,None]
        image[ry1:ry2,rx1:rx2] = (sharp.astype(np.float32)*mask + crop.astype(np.float32)*(1-mask)).clip(0,255).astype(np.uint8)
        return image

    def process_job(self, job_payload, target_file, reference_files, progress_cb):
        media_type = job_payload.get('media_type','image')
        out_dir = Path(tempfile.mkdtemp(prefix='studio_proc_'))
        progress_cb(10.0,'ANALYZING','Aggregating reference angles')
        ref_images = [cv2.imread(str(p)) for p in reference_files]
        identity = self.identity_aggregator.build_unified_identity(ref_images)
        if identity is None: raise ValueError('Could not build an identity from the uploaded reference photos')
        source_face = identity['source_face']
        identity_msg = f"Used {identity['num_references_used']}/{len(ref_images)} reference photos for identity"
        print(f'[Identity] {identity_msg}')
        progress_cb(12.0,'ANALYZING',identity_msg,warning=identity_msg)

        if media_type == 'image':
            progress_cb(30.0,'PROCESSING','Applying face transformation')
            tgt = cv2.imread(str(target_file))
            if tgt is None: raise ValueError('Could not read target image')
            faces = get_face_app().get(tgt)
            if not faces: raise ValueError('No face detected in the target image')
            bbox = job_payload.get('target_face_bbox')
            if bbox:
                tc=((bbox['x1']+bbox['x2'])/2,(bbox['y1']+bbox['y2'])/2)
                target_face=min(faces,key=lambda f:((f.bbox[0]+f.bbox[2])/2-tc[0])**2+((f.bbox[1]+f.bbox[3])/2-tc[1])**2)
            else:
                target_face=max(faces,key=lambda f:(f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            swapped=swap_face(tgt,target_face,source_face)
            # First recover target-image micro-detail, then optionally restore facial structure.
            swapped=self._preserve_target_detail(tgt,swapped,target_face.bbox,strength=0.78)
            if job_payload.get('face_restoration',False):
                swapped=self._restore_face_region(swapped,target_face.bbox,self.restorer)
            swapped=self._sharpen_face_region(swapped,target_face.bbox)
            res_path=out_dir/'result.png'
            cv2.imwrite(str(res_path),swapped,[cv2.IMWRITE_PNG_COMPRESSION,3])
            progress_cb(100.0,'COMPLETED','Image Transformation Complete')
            return res_path

        progress_cb(15.0,'ANALYZING','Extracting video frames and audio')
        audio_path=out_dir/'audio.aac'; extract_audio(target_file,audio_path)
        frames_dir=out_dir/'frames'; frames_dir.mkdir(parents=True,exist_ok=True)
        cap=cv2.VideoCapture(str(target_file))
        if not cap.isOpened(): raise ValueError('Could not open target video')
        fps=cap.get(cv2.CAP_PROP_FPS) or 30.0; total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        app=get_face_app(); bbox=job_payload.get('target_face_bbox'); prev_center=None
        if bbox: prev_center=((bbox['x1']+bbox['x2'])/2,(bbox['y1']+bbox['y2'])/2)
        frame_idx=0; swapped_count=0
        while True:
            ok,frame=cap.read()
            if not ok: break
            faces=app.get(frame); chosen=None
            if faces:
                if prev_center is not None:
                    chosen=min(faces,key=lambda f:((f.bbox[0]+f.bbox[2])/2-prev_center[0])**2+((f.bbox[1]+f.bbox[3])/2-prev_center[1])**2)
                else: chosen=max(faces,key=lambda f:(f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                prev_center=((chosen.bbox[0]+chosen.bbox[2])/2,(chosen.bbox[1]+chosen.bbox[3])/2)
            if chosen is not None:
                out_frame=swap_face(frame,chosen,source_face); swapped_count+=1
                out_frame=self._preserve_target_detail(frame,out_frame,chosen.bbox,strength=0.78)
                if job_payload.get('face_restoration',False): out_frame=self._restore_face_region(out_frame,chosen.bbox,self.restorer)
                out_frame=self._sharpen_face_region(out_frame,chosen.bbox)
            else: out_frame=frame
            cv2.imwrite(str(frames_dir/f'frame_{frame_idx:06d}.png'),out_frame); frame_idx+=1
            if total_frames: progress_cb(min(20.0+60.0*frame_idx/total_frames,80.0),'PROCESSING',f'Swapping frame {frame_idx}/{total_frames}')
        cap.release()
        swap_msg=f'Swapped face in {swapped_count}/{frame_idx} frames'; print(f'[JobProcessor] {swap_msg}')
        progress_cb(82.0,'ENCODING',swap_msg,warning=swap_msg)
        final_mp4=out_dir/'result.mp4'; progress_cb(85.0,'ENCODING','Multiplexing H.264 video with original audio')
        mux_frames_and_audio(str(frames_dir/'frame_%06d.png'),audio_path,final_mp4,fps)
        progress_cb(100.0,'COMPLETED','Video Generated Successfully')
        return final_mp4
