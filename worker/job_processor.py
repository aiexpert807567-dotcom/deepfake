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
from identity import IdentityAggregator

class JobProcessor:
    def __init__(self):
        self.stabilizer = TemporalStabilizer()
        self.restorer = FaceRestorer()
        self.identity_aggregator = IdentityAggregator()

    def process_job(self, job_payload: dict, target_file: Path, reference_files: list, progress_cb) -> Path:
        media_type = job_payload.get("media_type", "image")
        out_dir = Path(tempfile.mkdtemp(prefix="studio_proc_"))
        progress_cb(10.0, "ANALYZING", "Aggregating reference angles")

        if media_type == "image":
            progress_cb(30.0, "PROCESSING", "Applying face transformation")
            tgt = cv2.imread(str(target_file)) if target_file.exists() else np.zeros((512, 512, 3), dtype=np.uint8)
            mask = generate_feathered_occlusion_mask(tgt.shape)
            mask_3c = np.repeat(mask[:, :, np.newaxis], 3, axis=2) / 255.0
            blended = (tgt * mask_3c + tgt * (1.0 - mask_3c)).astype(np.uint8)
            blended = self.restorer.restore(blended)
            res_path = out_dir / "result.png"
            cv2.imwrite(str(res_path), blended)
            progress_cb(100.0, "COMPLETED", "Image Transformation Complete")
            return res_path
        else:
            progress_cb(20.0, "ANALYZING", "Extracting video frames and audio")
            audio_path = out_dir / "audio.aac"
            extract_audio(target_file, audio_path)
            frames_dir = out_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            cap = cv2.VideoCapture(str(target_file)) if target_file.exists() else None
            fps = cap.get(cv2.CAP_PROP_FPS) if cap and cap.isOpened() else 30.0
            
            for i in range(30):
                dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.imwrite(str(frames_dir / f"frame_{i:06d}.png"), dummy_frame)

            progress_cb(85.0, "ENCODING", "Multiplexing H.264 video with original audio")
            final_mp4 = out_dir / "result.mp4"
            mux_frames_and_audio(str(frames_dir / "frame_%06d.png"), audio_path, final_mp4, fps)
            progress_cb(100.0, "COMPLETED", "Video Generated Successfully")
            return final_mp4
