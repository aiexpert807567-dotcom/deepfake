import cv2
import numpy as np


def generate_feathered_occlusion_mask(frame_shape: tuple, bbox=None, feather_radius: int = 15) -> np.ndarray:
    """Create a soft face mask that protects surrounding hair/background pixels."""
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    if bbox is None:
        center = (w // 2, h // 2)
        axes = (max(w // 3, 1), max(h // 3, 1))
    else:
        x1, y1, x2, y2 = [float(v) for v in bbox]
        center = (int((x1 + x2) * 0.5), int((y1 + y2) * 0.5))
        axes = (max(int((x2 - x1) * 0.62), 1), max(int((y2 - y1) * 0.76), 1))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    sigma = max(float(feather_radius), 1.0)
    mask = cv2.GaussianBlur(mask, (0, 0), sigma)
    return np.clip(mask, 0.0, 1.0)


def blend_with_occlusion_protection(original: np.ndarray, swapped: np.ndarray, bbox, feather_radius: int = 15) -> np.ndarray:
    """Blend the swapped face while keeping the surrounding target frame untouched."""
    mask = generate_feathered_occlusion_mask(original.shape, bbox, feather_radius)[..., None]
    return np.clip(
        original.astype(np.float32) * (1.0 - mask) + swapped.astype(np.float32) * mask,
        0, 255
    ).astype(np.uint8)
