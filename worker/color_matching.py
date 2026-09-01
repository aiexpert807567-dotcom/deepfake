import cv2
import numpy as np


def match_color_reinhard(source_rgb: np.ndarray, target_rgb: np.ndarray, strength: float = 0.75) -> np.ndarray:
    """Match source appearance to target using robust LAB statistics."""
    src = np.asarray(source_rgb, dtype=np.uint8)
    tgt = np.asarray(target_rgb, dtype=np.uint8)
    src_lab = cv2.cvtColor(src, cv2.COLOR_RGB2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(tgt, cv2.COLOR_RGB2LAB).astype(np.float32)

    src_flat = src_lab.reshape(-1, 3)
    tgt_flat = tgt_lab.reshape(-1, 3)
    src_mean, src_std = np.mean(src_flat, axis=0), np.std(src_flat, axis=0) + 1e-6
    tgt_mean, tgt_std = np.mean(tgt_flat, axis=0), np.std(tgt_flat, axis=0) + 1e-6

    matched = (src_lab - src_mean) * (tgt_std / src_std) + tgt_mean
    matched = cv2.cvtColor(np.clip(matched, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    strength = float(np.clip(strength, 0.0, 1.0))
    return cv2.addWeighted(src, 1.0 - strength, matched, strength, 0.0)


def match_face_region(swapped_bgr: np.ndarray, target_bgr: np.ndarray, bbox, strength: float = 0.72) -> np.ndarray:
    """Apply color/lighting matching only inside the selected face region."""
    h, w = swapped_bgr.shape[:2]
    x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
    fw, fh = max(x2 - x1, 1), max(y2 - y1, 1)
    mx, my = max(int(fw * 0.35), 12), max(int(fh * 0.45), 12)
    rx1, ry1 = max(0, x1 - mx), max(0, y1 - my)
    rx2, ry2 = min(w, x2 + mx), min(h, y2 + my)
    if rx2 <= rx1 or ry2 <= ry1:
        return swapped_bgr

    src_crop = swapped_bgr[ry1:ry2, rx1:rx2]
    tgt_crop = target_bgr[ry1:ry2, rx1:rx2]
    src_rgb = cv2.cvtColor(src_crop, cv2.COLOR_BGR2RGB)
    tgt_rgb = cv2.cvtColor(tgt_crop, cv2.COLOR_BGR2RGB)
    matched = cv2.cvtColor(match_color_reinhard(src_rgb, tgt_rgb, strength), cv2.COLOR_RGB2BGR)

    mask = np.zeros(src_crop.shape[:2], dtype=np.float32)
    cx, cy = ((x1 + x2) * 0.5) - rx1, ((y1 + y2) * 0.5) - ry1
    cv2.ellipse(mask, (int(cx), int(cy)), (max(int(fw * 0.60), 8), max(int(fh * 0.76), 8)), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), max(fw * 0.08, 2.0))[..., None]
    swapped_bgr[ry1:ry2, rx1:rx2] = np.clip(
        src_crop.astype(np.float32) * (1.0 - mask) + matched.astype(np.float32) * mask,
        0, 255
    ).astype(np.uint8)
    return swapped_bgr
