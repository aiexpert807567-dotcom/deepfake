import numpy as np

class TemporalStabilizer:
    def __init__(self, alpha: float = 0.8):
        self.alpha = alpha
        self.previous_frame = None

    def smooth_frame(self, frame: np.ndarray) -> np.ndarray:
        if self.previous_frame is None:
            self.previous_frame = frame.astype(np.float32)
            return frame
        smoothed = self.alpha * self.previous_frame + (1.0 - self.alpha) * frame.astype(np.float32)
        self.previous_frame = smoothed
        return np.clip(smoothed, 0, 255).astype(np.uint8)

    def reset(self):
        self.previous_frame = None
