import os
import cv2
import tempfile
import numpy as np
from pathlib import Path
from color_matching import match_color_reinhard
from occlusion import generate_feathered_occlusion_mask
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

    def process_job(self, job_payload: dict, target_file: Path, reference_files: list, progress_cb) -> Path:
        media_type = job_payload.get("media_type", "image")
        out_dir = Path(tempfile.mkdtemp(prefix="studio_proc_"))

        progress_cb(10.0, "ANALYZING", "Aggregating reference angles")
        ref_images = [cv2.imread(str(p)) for p in reference_files]
        identity = self.identity_aggregator.build_unified_identity(ref_images)
        if identity is None:
            raise ValueError("Could not build an identity from the uploaded reference photos")
        source_face = identity["source_face"]
        print(f"[Identity] Built embedding from {identity['num_references_used']}/{len(ref_images)} reference photos")

        if media_type == "image":
            progress_cb(30.0, "PROCESSING", "Applying face transformation")
            tgt = cv2.imread(str(target_file)) if target_file.exists() else np.zeros((512, 512, 3), dtype=np.uint8)
            app = get_face_app()
            faces = app.get(tgt)
            if not faces:
                raise ValueError("No face detected in the target image")
            target_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            swapped = swap_face(tgt, target_face, source_face)
            if job_payload.get("face_restoration", True):
                swapped = self.restorer.restore(swapped)
            res_path = out_dir / "result.png"
            cv2.imwrite(str(res_path), swapped)
            progress_cb(100.0, "COMPLETED", "Image Transformation Complete")
            return res_path

        else:
            progress_cb(15.0, "ANALYZING", "Extracting video frames and audio")
            audio_path = out_dir / "audio.aac"
            extract_audio(target_file, audio_path)
            frames_dir = out_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            cap = cv2.VideoCapture(str(target_file))
            if not cap.isOpened():
                raise ValueError("Could not open target video")
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

            app = get_face_app()
            bbox = job_payload.get("target_face_bbox")
            prev_center = None
            if bbox:
                prev_center = ((bbox["x1"] + bbox["x2"]) / 2.0, (bbox["y1"] + bbox["y2"]) / 2.0)

            self.stabilizer.reset()
            frame_idx = 0
            swapped_count = 0

            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                faces = app.get(frame)
                chosen = None
                if faces:
                    if prev_center is not None:
                        chosen = min(
                            faces,
                            key=lambda f: ((f.bbox[0] + f.bbox[2]) / 2 - prev_center[0]) ** 2
                            + ((f.bbox[1] + f.bbox[3]) / 2 - prev_center[1]) ** 2,
                        )
                    else:
                        chosen = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    prev_center = ((chosen.bbox[0] + chosen.bbox[2]) / 2, (chosen.bbox[1] + chosen.bbox[3]) / 2)

                if chosen is not None:
                    out_frame = swap_face(frame, chosen, source_face)
                    swapped_count += 1

                    # NOTE: FaceRestorer is currently a placeholder unsharp-mask filter,
                    # not real GFPGAN restoration. Sharpening a raw swap seam tends to
                    # amplify artifacts rather than fix them, so it's disabled here until
                    # Stage 4 wires in real GFPGAN.
                    # if job_payload.get("face_restoration", True):
                    #     ...

                    if job_payload.get("temporal_stabilization", True):
                        x1, y1, x2, y2 = [int(v) for v in chosen.bbox]
                        x1, y1 = max(x1, 0), max(y1, 0)
                        x2, y2 = min(x2, out_frame.shape[1]), min(y2, out_frame.shape[0])
                        if x2 > x1 and y2 > y1:
                            out_frame[y1:y2, x1:x2] = self.stabilizer.smooth_frame(out_frame[y1:y2, x1:x2])
                else:
                    out_frame = frame

                cv2.imwrite(str(frames_dir / f"frame_{frame_idx:06d}.png"), out_frame)
                frame_idx += 1
                if total_frames:
                    pct = 20.0 + 60.0 * (frame_idx / total_frames)
                    progress_cb(min(pct, 80.0), "PROCESSING", f"Swapping frame {frame_idx}/{total_frames}")

            cap.release()
            print(f"[JobProcessor] Swapped face in {swapped_count}/{frame_idx} frames")

            progress_cb(85.0, "ENCODING", "Multiplexing H.264 video with original audio")
            final_mp4 = out_dir / "result.mp4"
            mux_frames_and_audio(str(frames_dir / "frame_%06d.png"), audio_path, final_mp4, fps)
            progress_cb(100.0, "COMPLETED", "Video Generated Successfully")
            return final_mp4
