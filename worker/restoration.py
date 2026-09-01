import sys
import types
from pathlib import Path
import urllib.request
import cv2
import numpy as np


def _patch_torchvision_shim():
    try:
        import torchvision.transforms.functional_tensor  # noqa: F401
    except ImportError:
        import torchvision.transforms.functional as F
        shim = types.ModuleType("torchvision.transforms.functional_tensor")
        shim.rgb_to_grayscale = F.rgb_to_grayscale
        sys.modules["torchvision.transforms.functional_tensor"] = shim


_patch_torchvision_shim()

_MODEL_PATH = Path(__file__).resolve().parent / "models" / "GFPGANv1.4.pth"
_MODEL_URL = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"

_restorer = None


def _ensure_model() -> Path:
    _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _MODEL_PATH.exists():
        print("[Restoration] Downloading GFPGANv1.4.pth (~350MB)...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    return _MODEL_PATH


def _get_restorer():
    global _restorer
    if _restorer is None:
        from gfpgan import GFPGANer
        model_path = _ensure_model()
        _restorer = GFPGANer(
            model_path=str(model_path),
            upscale=2,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=None,
        )
    return _restorer


class FaceRestorer:
    def __init__(self, strength: float = 1.0):
        self.strength = 1.0

    def restore(self, face_bgr: np.ndarray) -> np.ndarray:
        try:
            if face_bgr is None or face_bgr.size == 0:
                return face_bgr

            h, w = face_bgr.shape[:2]
            if min(h, w) < 64:
                return face_bgr

            restorer = _get_restorer()
            _, _, restored = restorer.enhance(
                face_bgr,
                has_aligned=False,
                only_center_face=True,
                paste_back=True,
            )
            if restored is None:
                return face_bgr

            if restored.shape[:2] != face_bgr.shape[:2]:
                restored = cv2.resize(
                    restored,
                    (w, h),
                    interpolation=cv2.INTER_LANCZOS4,
                )

            restored = np.clip(restored, 0, 255).astype(np.uint8)

            # Maximum restoration: use the full GFPGAN result rather than
            # blending it back with the lower-resolution swap crop.
            result = restored

            # Maximum local micro-contrast recovery.
            blur = cv2.GaussianBlur(result, (0, 0), 0.55)
            result = cv2.addWeighted(result, 1.22, blur, -0.22, 0)
            return np.clip(result, 0, 255).astype(np.uint8)
        except Exception as exc:
            print(f"[Restoration] GFPGAN failed, returning original crop: {exc}")
            return face_bgr
