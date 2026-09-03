import cv2
import tempfile
import copy
import numpy as np
from pathlib import Path
from stabilization import TemporalStabilizer
from restoration import FaceRestorer
from ffmpeg_utils import extract_audio, mux_frames_and_audio
from identity import IdentityAggregator, get_face_app, estimate_face_pose
from swapper import swap_face
from color_matching import match_face_region
from occlusion import blend_with_occlusion_protection

class JobProcessor:
    def __init__(self):
        self.stabilizer = TemporalStabilizer(alpha=0.10)
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
        crop = image[ry1:ry2,rx1:rx2].copy()
        restored = restorer.restore(crop)
        if restored is None or restored.shape != crop.shape: return image
        mask = np.zeros(crop.shape[:2], dtype=np.float32)
        cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.58),8),max(int(fh*.72),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.08,2))[...,None]
        image[ry1:ry2,rx1:rx2] = (restored.astype(np.float32)*mask + crop.astype(np.float32)*(1-mask)).clip(0,255).astype(np.uint8)
        return image

    @staticmethod
    def _preserve_target_detail(original, swapped, bbox, strength=0.22):
        h, w = original.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2-x1,1), max(y2-y1,1)
        mx, my = max(int(fw*.22),10), max(int(fh*.28),10)
        rx1, ry1 = max(0,x1-mx), max(0,y1-my); rx2, ry2 = min(w,x2+mx), min(h,y2+my)
        if rx2 <= rx1 or ry2 <= ry1: return swapped
        src = original[ry1:ry2,rx1:rx2].astype(np.float32); dst = swapped[ry1:ry2,rx1:rx2].astype(np.float32)
        src_y = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_BGR2YCrCb)[...,0].astype(np.float32)
        dst_ycc = cv2.cvtColor(dst.astype(np.uint8), cv2.COLOR_BGR2YCrCb).astype(np.float32)
        detail = np.clip(cv2.GaussianBlur(src_y-cv2.GaussianBlur(src_y,(0,0),1.35),(0,0),0.35),-18.0,18.0)
        dst_ycc[...,0] = np.clip(dst_ycc[...,0] + detail*strength,0,255)
        detailed = cv2.cvtColor(dst_ycc.astype(np.uint8), cv2.COLOR_YCrCb2BGR)
        mask = np.zeros((ry2-ry1,rx2-rx1),dtype=np.float32)
        cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.62),8),max(int(fh*.78),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.055,1.5))[...,None]
        swapped[ry1:ry2,rx1:rx2] = np.clip(dst*(1-mask)+detailed.astype(np.float32)*mask,0,255).astype(np.uint8)
        return swapped

    @staticmethod
    def _sharpen_face_region(image, bbox):
        h, w = image.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2-x1,1), max(y2-y1,1); mx, my = max(int(fw*.18),8), max(int(fh*.18),8)
        rx1, ry1, rx2, ry2 = max(0,x1-mx), max(0,y1-my), min(w,x2+mx), min(h,y2+my)
        crop = image[ry1:ry2,rx1:rx2].copy()
        if crop.size == 0: return image
        blur = cv2.GaussianBlur(crop,(0,0),1.05); sharp = cv2.addWeighted(crop,1.18,blur,-0.18,0)
        mask = np.zeros(crop.shape[:2],dtype=np.float32); cx, cy = ((x1+x2)/2)-rx1, ((y1+y2)/2)-ry1
        cv2.ellipse(mask,(int(cx),int(cy)),(max(int(fw*.62),8),max(int(fh*.76),8)),0,0,360,1.0,-1)
        mask = cv2.GaussianBlur(mask,(0,0),max(fw*.07,1.5))[...,None]
        image[ry1:ry2,rx1:rx2] = (sharp.astype(np.float32)*mask + crop.astype(np.float32)*(1-mask)).clip(0,255).astype(np.uint8)
        return image

    @staticmethod
    def _smooth_bbox(previous, current, alpha=0.72):
        if previous is None: return np.asarray(current,dtype=np.float32)
        return alpha*np.asarray(previous,dtype=np.float32)+(1-alpha)*np.asarray(current,dtype=np.float32)

    @staticmethod
    def _pose_distance(a,b):
        delta=np.asarray(a,dtype=np.float32)-np.asarray(b,dtype=np.float32)
        delta[0]=((delta[0]+180)%360)-180
        return float(np.sqrt((delta[0]/45)**2+(delta[1]/35)**2+(delta[2]/25)**2))

    @staticmethod
    def _select_reference(reference_candidates,target_face,previous_index=None):
        if not reference_candidates: return None,None
        target_pose=estimate_face_pose(target_face); scored=[]
        for c in reference_candidates:
            distance=JobProcessor._pose_distance(target_pose,c['pose'])
            quality_bonus=min(float(c.get('weight',1))/100,2)*0.03
            hysteresis=0.18 if previous_index is not None and c['index']==previous_index else 0.0
            scored.append((distance-quality_bonus-hysteresis,c))
        scored.sort(key=lambda x:x[0]); best_score,best=scored[0]
        if previous_index is not None:
            prev=next((c for c in reference_candidates if c['index']==previous_index),None)
            if prev is not None and JobProcessor._pose_distance(target_pose,prev['pose']) <= best_score+0.18: best=prev
        selected=best['face']
        if len(scored)>1 and scored[1][0]-best_score<0.10:
            second=scored[1][1]; emb=0.65*best['embedding']+0.35*second['embedding']; emb/=np.linalg.norm(emb)+1e-8
            base_face=best['face']
            selected=type(base_face)(base_face)  # Face's copy protocol is broken (__setstate__ resolves to None); rebuild via its own dict-like constructor instead
            selected['embedding']=emb.astype(np.float32)
        return selected,best['index']

    def _finish_frame(self, original, swapped, bbox, payload, temporal=False):
        if payload.get('color_matching',True):
            swapped=match_face_region(swapped,original,bbox,strength=0.55)
        # _preserve_target_detail intentionally removed: it re-injected the
        # TARGET's own facial structure/luminance detail back into the swap,
        # which directly fights identity transfer and was pulling jawline/
        # face shape back toward the target instead of the reference.
        if payload.get('face_restoration',False): swapped=self._restore_face_region(swapped,bbox,self.restorer)
        swapped=self._sharpen_face_region(swapped,bbox)
        if temporal: swapped=self.stabilizer.smooth_face(swapped,bbox)
        return swapped

    def process_job(self, job_payload, target_file, reference_files, progress_cb):
        media_type=job_payload.get('media_type','image'); out_dir=Path(tempfile.mkdtemp(prefix='studio_proc_'))
        progress_cb(10.0,'ANALYZING','Aggregating reference angles')
        ref_images=[cv2.imread(str(p)) for p in reference_files]
        identity=self.identity_aggregator.build_unified_identity(ref_images)
        if identity is None: raise ValueError('Could not build an identity from the uploaded reference photos')
        source_face=identity['source_face']; reference_candidates=identity.get('reference_candidates',[])
        identity_msg=f"Used {identity['num_references_used']}/{len(ref_images)} reference photos; angle-aware matching enabled"
        progress_cb(12.0,'ANALYZING',identity_msg,warning=identity_msg)

        if media_type=='image':
            progress_cb(30.0,'PROCESSING','Matching reference angle and applying high-quality 512px transformation')
            tgt=cv2.imread(str(target_file));
            if tgt is None: raise ValueError('Could not read target image')
            faces=get_face_app().get(tgt)
            if not faces: raise ValueError('No face detected in the target image')
            bbox=job_payload.get('target_face_bbox')
            if bbox:
                tc=((bbox['x1']+bbox['x2'])/2,(bbox['y1']+bbox['y2'])/2); target_face=min(faces,key=lambda f:((f.bbox[0]+f.bbox[2])/2-tc[0])**2+((f.bbox[1]+f.bbox[3])/2-tc[1])**2)
                target_face.bbox=np.array([bbox['x1'],bbox['y1'],bbox['x2'],bbox['y2']],dtype=np.float32)
            else: target_face=max(faces,key=lambda f:(f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            selected,_=self._select_reference(reference_candidates,target_face)
            if selected is None: selected=source_face
            swapped=swap_face(tgt,target_face,selected)
            swapped=self._finish_frame(tgt,swapped,target_face.bbox,job_payload,False)
            res_path=out_dir/'result.png'; cv2.imwrite(str(res_path),swapped,[cv2.IMWRITE_PNG_COMPRESSION,3])
            progress_cb(100.0,'COMPLETED','High-quality image transformation complete'); return res_path

        progress_cb(15.0,'ANALYZING','Extracting video frames and audio')
        audio_path=out_dir/'audio.aac'; extract_audio(target_file,audio_path)
        frames_dir=out_dir/'frames'; frames_dir.mkdir(parents=True,exist_ok=True)
        cap=cv2.VideoCapture(str(target_file))
        if not cap.isOpened(): raise ValueError('Could not open target video')
        fps=cap.get(cv2.CAP_PROP_FPS) or 30.0; total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        app=get_face_app(); bbox=job_payload.get('target_face_bbox'); prev_center=None; prev_bbox=None; prev_ref_index=None
        if bbox:
            prev_center=((bbox['x1']+bbox['x2'])/2,(bbox['y1']+bbox['y2'])/2); prev_bbox=np.array([bbox['x1'],bbox['y1'],bbox['x2'],bbox['y2']],dtype=np.float32)
        self.stabilizer.reset(); frame_idx=0; swapped_count=0
        while True:
            ok,frame=cap.read()
            if not ok: break
            faces=app.get(frame); chosen=None
            if faces:
                if prev_center is not None: chosen=min(faces,key=lambda f:((f.bbox[0]+f.bbox[2])/2-prev_center[0])**2+((f.bbox[1]+f.bbox[3])/2-prev_center[1])**2)
                else: chosen=max(faces,key=lambda f:(f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                smooth=self._smooth_bbox(prev_bbox,np.asarray(chosen.bbox,dtype=np.float32),0.72); chosen.bbox=smooth; prev_bbox=smooth; prev_center=((smooth[0]+smooth[2])/2,(smooth[1]+smooth[3])/2)
            if chosen is not None:
                selected,prev_ref_index=self._select_reference(reference_candidates,chosen,prev_ref_index)
                if selected is None: selected=source_face
                out_frame=swap_face(frame,chosen,selected); swapped_count+=1
                out_frame=self._finish_frame(frame,out_frame,chosen.bbox,job_payload,bool(job_payload.get('temporal_stabilization',True)))
            else:
                self.stabilizer.reset(); out_frame=frame
            cv2.imwrite(str(frames_dir/f'frame_{frame_idx:06d}.png'),out_frame); frame_idx+=1
            if total_frames: progress_cb(min(20+60*frame_idx/total_frames,80),'PROCESSING',f'Swapping frame {frame_idx}/{total_frames}')
        cap.release(); swap_msg=f'Swapped face in {swapped_count}/{frame_idx} frames with angle-aware tracking'
        progress_cb(82.0,'ENCODING',swap_msg,warning=swap_msg)
        final_mp4=out_dir/'result.mp4'; progress_cb(85.0,'ENCODING','Encoding high-quality H.264 video with original audio')
        if not mux_frames_and_audio(str(frames_dir/'frame_%06d.png'),audio_path,final_mp4,fps): raise RuntimeError('FFmpeg failed while encoding the final video')
        progress_cb(100.0,'COMPLETED','High-quality video generated successfully'); return final_mp4
