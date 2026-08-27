import cv2
import numpy as np

def generate_feathered_occlusion_mask(frame_shape: tuple, feather_radius: int = 15) -> np.ndarray:
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2)
    axes = (w // 3, h // 3)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return cv2.GaussianBlur(mask, (feather_radius * 2 + 1, feather_radius * 2 + 1), feather_radius / 2)
