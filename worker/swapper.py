import os
import glob
from pathlib import Path
import urllib.request

_KAGGLE_INPUT_DIRS = ["/kaggle/input/inswapper", "/kaggle/input/inswapper-128", "/kaggle/input/inswapper_128"]
_FALLBACK_URL = "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx"
_LOCAL_MODEL_PATH = Path(__file__).resolve().parent / "models" / "inswapper_128.onnx"

_swapper = None

def _find_model_path() -> str:
    for d in _KAGGLE_INPUT_DIRS:
        if os.path.isdir(d):
            matches = glob.glob(os.path.join(d, "**", "*.onnx"), recursive=True)
            if matches:
                print(f"[Swapper] Using Kaggle dataset model: {matches[0]}")
                return matches[0]
    if _LOCAL_MODEL_PATH.exists():
        return str(_LOCAL_MODEL_PATH)
    _LOCAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("[Swapper] Kaggle dataset not found — downloading inswapper_128.onnx (~550MB) from fallback URL...")
    urllib.request.urlretrieve(_FALLBACK_URL, _LOCAL_MODEL_PATH)
    return str(_LOCAL_MODEL_PATH)

def get_swapper():
    global _swapper
    if _swapper is None:
        import insightface
        import onnxruntime
        print(f"[Swapper] onnxruntime available providers: {onnxruntime.get_available_providers()}")
        model_path = _find_model_path()
        _swapper = insightface.model_zoo.get_model(
            model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
    return _swapper

def swap_face(frame, target_face, source_face):
    swapper = get_swapper()
    return swapper.get(frame, target_face, source_face, paste_back=True)
