import cv2
import urllib.request
import numpy as np
from pathlib import Path
from typing import List, Dict

_MODEL_PATH = Path(__file__).resolve().parent / "_models" / "face_detection_yunet.onnx"
_MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

def _ensure_model() -> Path:
    _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _MODEL_PATH.exists():
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    return _MODEL_PATH

def _create_detector(model_path: Path, size):
    if hasattr(cv2, "FaceDetectorYN_create"):
        return cv2.FaceDetectorYN_create(str(model_path), "", size, 0.7, 0.3, 5000)
    return cv2.FaceDetectorYN.create(str(model_path), "", size, 0.7, 0.3, 5000)

def _load_representative_frame(path: Path) -> np.ndarray:
    ext = path.suffix.lower()
    if ext in [".mp4", ".mov", ".webm", ".avi"]:
        cap = cv2.VideoCapture(str(path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mid = max(total // 2, 0)
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise ValueError("Could not read a frame from the uploaded video")
        return frame
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError("Could not read the uploaded image")
    return img

def detect_faces_in_media(path: Path) -> List[Dict]:
    frame = _load_representative_frame(path)
    h, w = frame.shape[:2]
    model_path = _ensure_model()
    detector = _create_detector(model_path, (w, h))
    _, faces = detector.detect(frame)

    if faces is None:
        return []

    faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)

    results = []
    for i, f in enumerate(faces_sorted):
        x, y, fw, fh = [float(v) for v in f[0:4]]
        conf = float(f[14]) if len(f) > 14 else 0.9
        results.append({
            "id": f"face_{i}",
            "label": f"Face {i + 1}" + (" (Primary Target)" if i == 0 else ""),
            "confidence": round(conf, 4),
            "bbox": {"x1": x, "y1": y, "x2": x + fw, "y2": y + fh},
        })
    return results
