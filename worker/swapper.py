import os
import glob
import urllib.request
from pathlib import Path

import cv2
import numpy as np

_KAGGLE_INPUT_DIRS = [
    "/kaggle/input/simswap",
    "/kaggle/input/simswap-512",
    "/kaggle/input/inswapper",
    "/kaggle/input/inswapper-128",
    "/kaggle/input/inswapper_128",
]

_ASSET_BASE = "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0"
_SIMSWAP_URL = f"{_ASSET_BASE}/simswap_unofficial_512.onnx"
_SIMSWAP_CONVERTER_URL = f"{_ASSET_BASE}/arcface_converter_simswap.onnx"
_INSWAPPER_URL = "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx"

_MODEL_DIR = Path(__file__).resolve().parent / "models"
_SIMSWAP_PATH = _MODEL_DIR / "simswap_unofficial_512.onnx"
_SIMSWAP_CONVERTER_PATH = _MODEL_DIR / "arcface_converter_simswap.onnx"
_INSWAPPER_PATH = _MODEL_DIR / "inswapper_128.onnx"

_swapper_session = None
_converter_session = None
_inswapper = None
_template = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def _download(url: str, path: Path, label: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1024 * 1024:
        return str(path)
    print(f"[Swapper] Downloading {label}...")
    tmp = path.with_suffix(path.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(path)
    return str(path)


def _find_kaggle_model(name: str):
    for d in _KAGGLE_INPUT_DIRS:
        if not os.path.isdir(d):
            continue
        matches = glob.glob(os.path.join(d, "**", name), recursive=True)
        if matches:
            return matches[0]
    return None


def _resolve_simswap_paths():
    model = _find_kaggle_model("simswap_unofficial_512.onnx")
    converter = _find_kaggle_model("arcface_converter_simswap.onnx")
    if model:
        print(f"[Swapper] Using Kaggle SimSwap 512 model: {model}")
    else:
        model = _download(_SIMSWAP_URL, _SIMSWAP_PATH, "SimSwap 512 model (~239 MB)")
    if converter:
        print(f"[Swapper] Using Kaggle SimSwap ArcFace converter: {converter}")
    else:
        converter = _download(_SIMSWAP_CONVERTER_URL, _SIMSWAP_CONVERTER_PATH, "SimSwap ArcFace converter (~21 MB)")
    return model, converter


def _get_sessions():
    global _swapper_session, _converter_session
    if _swapper_session is None or _converter_session is None:
        import onnxruntime as ort
        providers = [p for p in ["CUDAExecutionProvider", "CPUExecutionProvider"] if p in ort.get_available_providers()]
        model_path, converter_path = _resolve_simswap_paths()
        print(f"[Swapper] ONNX providers: {providers}")
        _swapper_session = ort.InferenceSession(model_path, providers=providers)
        _converter_session = ort.InferenceSession(converter_path, providers=providers)
        print("[Swapper] High-quality SimSwap 512 loaded")
    return _swapper_session, _converter_session


def _aligned_crop(frame, face, size=512):
    kps = getattr(face, "kps", None)
    if kps is None:
        kps = getattr(face, "landmark_5", None)
    if kps is None:
        x1, y1, x2, y2 = [float(v) for v in face.bbox]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        side = max(x2 - x1, y2 - y1) * 1.55
        src = np.array([
            [cx - side * 0.22, cy - side * 0.18],
            [cx + side * 0.22, cy - side * 0.18],
            [cx, cy],
            [cx - side * 0.18, cy + side * 0.23],
            [cx + side * 0.18, cy + side * 0.23],
        ], dtype=np.float32)
    else:
        src = np.asarray(kps, dtype=np.float32).reshape(5, 2)

    dst = _template * (float(size) / 112.0)
    matrix, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)
    if matrix is None:
        raise ValueError("Could not align target face")
    crop = cv2.warpAffine(frame, matrix, (size, size), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return crop, matrix


def _paste_back(frame, swapped_rgb, matrix, face, size=512):
    h, w = frame.shape[:2]
    inv = cv2.invertAffineTransform(matrix)
    swapped_bgr = cv2.cvtColor(np.clip(swapped_rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)

    warped = cv2.warpAffine(swapped_bgr, inv, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_TRANSPARENT)

    # A wider mask lets the swap's actual bone structure/jawline come through
    # (not just the target's outline) — professional tools rely on Poisson
    # blending precisely so a wider mask like this doesn't produce a seam.
    mask_small = np.zeros((size, size), dtype=np.uint8)
    cv2.ellipse(mask_small, (size // 2, int(size * 0.56)), (int(size * 0.47), int(size * 0.58)), 0, 0, 360, 255, -1)
    mask_full = cv2.warpAffine(mask_small, inv, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    ys, xs = np.where(mask_full > 10)
    if len(xs) == 0:
        mask = (mask_full.astype(np.float32) / 255.0)[..., None]
        result = frame.astype(np.float32) * (1.0 - mask) + warped.astype(np.float32) * mask
        return np.clip(result, 0, 255).astype(np.uint8)

    center = (int(xs.mean()), int(ys.mean()))
    try:
        result = cv2.seamlessClone(warped, frame, mask_full, center, cv2.NORMAL_CLONE)
        return result
    except Exception:
        mask = (mask_full.astype(np.float32) / 255.0)[..., None]
        mask = cv2.GaussianBlur(mask, (0, 0), size * 0.02)
        result = frame.astype(np.float32) * (1.0 - mask) + warped.astype(np.float32) * mask
        return np.clip(result, 0, 255).astype(np.uint8)


def _simswap_face(frame, target_face, source_face):
    swapper, converter = _get_sessions()
    embedding = np.asarray(source_face.embedding, dtype=np.float32).reshape(1, -1)
    converted = converter.run(None, {converter.get_inputs()[0].name: embedding})[0]
    converted = converted.reshape(1, -1).astype(np.float32)
    norm = np.linalg.norm(converted, axis=1, keepdims=True) + 1e-8
    converted = converted / norm

    crop, matrix = _aligned_crop(frame, target_face, 512)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    inp = rgb.transpose(2, 0, 1)[None].astype(np.float32)

    inputs = {}
    for item in swapper.get_inputs():
        if item.name == "source":
            inputs[item.name] = converted
        elif item.name == "target":
            inputs[item.name] = inp
    if len(inputs) != 2:
        raise RuntimeError(f"Unexpected SimSwap inputs: {[i.name for i in swapper.get_inputs()]}")

    output = swapper.run(None, inputs)[0][0]
    if output.shape[0] == 3:
        output = output.transpose(1, 2, 0)
    output = np.clip(output, 0.0, 1.0) * 255.0
    return _paste_back(frame, output, matrix, target_face, 512)


def _get_inswapper():
    global _inswapper
    if _inswapper is None:
        from insightface.model_zoo.inswapper import INSwapper
        import onnxruntime
        if not _INSWAPPER_PATH.exists():
            _download(_INSWAPPER_URL, _INSWAPPER_PATH, "Inswapper 128 fallback (~550 MB)")
        providers = [p for p in ["CUDAExecutionProvider", "CPUExecutionProvider"] if p in onnxruntime.get_available_providers()]
        print(f"[Swapper] Fallback providers: {providers}")
        _inswapper = INSwapper(model_file=str(_INSWAPPER_PATH))
        if _inswapper is None:
            raise RuntimeError("Inswapper 128 model failed to load (got None) — the .onnx file may be corrupted or truncated; delete worker/models/inswapper_128.onnx and retry")
    return _inswapper


def swap_face(frame, target_face, source_face):
    try:
        return _simswap_face(frame, target_face, source_face)
    except Exception as exc:
        print(f"[Swapper] SimSwap 512 failed; falling back to Inswapper 128: {exc}")
        return _get_inswapper().get(frame, target_face, source_face, paste_back=True)
