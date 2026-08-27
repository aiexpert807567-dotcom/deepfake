import cv2
import numpy as np

def match_color_reinhard(source_rgb: np.ndarray, target_rgb: np.ndarray) -> np.ndarray:
    src_lab = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

    src_mean, src_std = np.mean(src_lab.reshape(-1, 3), axis=0), np.std(src_lab.reshape(-1, 3), axis=0) + 1e-6
    tgt_mean, tgt_std = np.mean(tgt_lab.reshape(-1, 3), axis=0), np.std(tgt_lab.reshape(-1, 3), axis=0) + 1e-6

    res_lab = np.zeros_like(src_lab)
    for i in range(3):
        res_lab[..., i] = ((src_lab[..., i] - src_mean[i]) * (tgt_std[i] / src_std[i])) + tgt_mean[i]

    return cv2.cvtColor(np.clip(res_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
