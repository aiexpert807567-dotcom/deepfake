import cv2
import numpy as np

class FaceRestorer:
    def __init__(self, strength: float = 0.85):
        self.strength = strength

    def restore(self, face_rgb: np.ndarray) -> np.ndarray:
        gaussian = cv2.GaussianBlur(face_rgb, (0, 0), 2.0)
        unsharp = cv2.addWeighted(face_rgb, 1.5, gaussian, -0.5, 0)
        return cv2.addWeighted(unsharp, self.strength, face_rgb, 1.0 - self.strength, 0)
