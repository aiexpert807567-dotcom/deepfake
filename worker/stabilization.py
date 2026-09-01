import cv2
import numpy as np


class TemporalStabilizer:
    """Stabilize only the selected face ROI to avoid whole-frame ghosting."""
    def __init__(self, alpha: float = 0.10, max_motion_ratio: float = 0.30):
        self.alpha = float(np.clip(alpha, 0.0, 0.5))
        self.max_motion_ratio = float(max_motion_ratio)
        self.previous_bbox = None
        self.previous_crop = None

    def smooth_face(self, frame: np.ndarray, bbox) -> np.ndarray:
        if bbox is None:
            return frame
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return frame

        crop = frame[y1:y2, x1:x2].copy()
        if self.previous_bbox is not None and self.previous_crop is not None:
            px1, py1, px2, py2 = self.previous_bbox
            pcx, pcy = (px1 + px2) * 0.5, (py1 + py2) * 0.5
            ccx, ccy = (x1 + x2) * 0.5, (y1 + y2) * 0.5
            diag = max(np.hypot(x2 - x1, y2 - y1), 1.0)
            motion = np.hypot(ccx - pcx, ccy - pcy) / diag
            if motion <= self.max_motion_ratio:
                previous = cv2.resize(self.previous_crop, (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_LINEAR)
                blended = cv2.addWeighted(crop, 1.0 - self.alpha, previous, self.alpha, 0.0)
                mask = np.zeros(crop.shape[:2], dtype=np.float32)
                cv2.ellipse(mask, (crop.shape[1] // 2, crop.shape[0] // 2),
                            (max(crop.shape[1] // 2 - 2, 1), max(crop.shape[0] // 2 - 2, 1)),
                            0, 0, 360, 1.0, -1)
                mask = cv2.GaussianBlur(mask, (0, 0), max(min(crop.shape[:2]) * 0.05, 1.0))[..., None]
                frame[y1:y2, x1:x2] = np.clip(
                    crop.astype(np.float32) * (1.0 - mask) + blended.astype(np.float32) * mask,
                    0, 255
                ).astype(np.uint8)

        self.previous_bbox = np.array([x1, y1, x2, y2], dtype=np.float32)
        self.previous_crop = frame[y1:y2, x1:x2].copy()
        return frame

    def reset(self):
        self.previous_bbox = None
        self.previous_crop = None
