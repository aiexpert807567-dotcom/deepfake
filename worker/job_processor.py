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
    def _restore_face_region(image: np.ndarray, bbox, restorer: FaceRestorer) -> np.ndarray:
        """Restore only the swapped face, with margin, then blend it back."""
        h, w = image.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        fw, fh = max(x2 - x1, 1), max(y2 - y1, 1)
        margin_x = max(int(fw * 0.35), 16)
        margin_y = max(int(fh * 0.45), 16)
        rx1, ry1 = max(0, x1 - margin_x), max(0, y1 - margin_y)
        rx2, ry2 = min(w, x2 + margin_x), min(h, y2 + margin_y)
        if rx2 <= rx1 or ry2 <= ry1:
            return image

        crop = image[ry1:ry2, rx1:rx2].copy()
        restored = restorer.restore(crop)
        if restored is None or restored.shape != crop.shape:
            return image

        # Blend only around the actual face bbox, keeping hair/background details
        # from the original swapped frame untouched.
        mask = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.float32)
        cx = ((x1 + x2) / 2.0) - rx1
        cy = ((y1 + y2) / 2.0) - ry1
        ax = max((x2 - x1) * 0.58, 8)
        ay = max((y2 - y1) * 0.72, 8)
        cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 1.0, -1)
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=max(fw * 0.08, 2), sigmaY=max(fh * 0.08, 2))
        mask = mask[..., None]
        image[ry1:ry2, rx1:rx2] = (
            restored.astype(np.float32) * mask
            + crop.astype(np.float32) * (1.0 - mask)
        ).clip(0, 255).astype(np.uint8)
        return image

    def process_job(self, job_payload: dict, target_file: Path, reference_files: list, progress_cb) -> Path:
        media_type = job_payload.get("media_type", "image")
        out_dir = Path(tempfile.mkdtemp(prefix="studio_proc_"))

        progress_cb(10.0, "ANALYZING", "Aggregating reference angles")
        ref_images = [cv2.imread(str(p)) for p in reference_files]
        identity = self.identity_aggregator.build_unified_identity(ref_images)
        if identity is None:
            raise ValueError("Could not build an identity from the uploaded reference photos")
        source_face = identity["source_face"]
        identity_msg = f"Used {identity['num_references_used']}/{len(ref_images)} reference photos for identity"
        print(f"[Identity] {identity_msg}")
        progress_cb(12.0, "ANALYZING", identity_msg, warning=identity_msg)

        if media_type == "image":
            progress_cb(30.0, "PROCESSING", "Applying face transformation")
            tgt = cv2.imread(str(target_file)) if target_file.exists() else np.zeros((512, 512, 3), dtype=np.uint8)
            app = get_face_app()
            faces = app.get(tgt)
            if not faces:
                raise ValueError("No face detected in the target image")

            bbox = job_payload.get("target_face_bbox")
            if bbox:
                target_center = ((bbox["x1"] + bbox["x2"]) / 2.0, (bbox["y1"] + bbox["y2"]) / 2.0)
                target_face = min(
                    faces,
                    key=lambda f: ((f.bbox[0] + f.bbox[2]) / 2 - target_center[0]) ** 2
                    + ((f.bbox[1] + f.bbox[3]) / 2 - target_center[1]) ** 2,
                )
            else:
                target_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

            # Keep the original full-resolution target as the base. InsightFace
            # performs the geometric swap and pastes it back into this image.
            swapped = swap_face(tgt, target_face, source_face)

            # Do NOT run GFPGAN on the whole image: that softens the entire photo
            # and makes the swapped face look blurry. Restore only the face region.
            if job_payload.get("face_restoration", True):
                swapped = self._restore_face_region(swapped, target_face.bbox, self.restorer)

            res_path = out_dir / "result.png"
            cv2.imwrite(str(res_path), swapped, [cv2.IMWRITE_PNG_COMPRESSION, 3])
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

                    if job_payload.get("face_restoration", True):
                        out_frame = self._restore_face_region(out_frame, chosen.bbox, self.restorer)

                    # Whole-frame EMA blending is intentionally not used here;
                    # it causes visible ghosting and reduces sharpness.
                else:
                    out_frame = frame

                cv2.imwrite(str(frames_dir / f"frame_{frame_idx:06d}.png"), out_frame)
                frame_idx += 1
                if total_frames:
                    pct = 20.0 + 60.0 * (frame_idx / total_frames)
                    progress_cb(min(pct, 80.0), "PROCESSING", f"Swapping frame {frame_idx}/{total_frames}")

            cap.release()
            swap_msg = f"Swapped face in {swapped_count}/{frame_idx} frames"
            print(f"[JobProcessor] {swap_msg}")
            progress_cb(82.0, "ENCODING", swap_msg, warning=swap_msg)

            progress_cb(85.0, "ENCODING", "Multiplexing H.264 video with original audio")
            final_mp4 = out_dir / "result.mp4"
            mux_frames_and_audio(str(frames_dir / "frame_%06d.png"), audio_path, final_mp4, fps)
            progress_cb(100.0, "COMPLETED", "Video Generated Successfully")
            return final_mp4
