import cv2
import urllib.request
import numpy as np
from pathlib import Path
from typing import List, Dict

_MODEL_DIR = Path(__file__).resolve().parent / "_models"
_PROTO_PATH = _MODEL_DIR / "deploy.prototxt"
_MODEL_PATH = _MODEL_DIR / "res10_300x300_ssd_iter_140000.caffemodel"

_PROTO_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
_MODEL_URL = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

_net = None

def _get_net():
    global _net
    if _net is None:
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        if not _PROTO_PATH.exists():
            urllib.request.urlretrieve(_PROTO_URL, _PROTO_PATH)
        if not _MODEL_PATH.exists():
            urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        _net = cv2.dnn.readNetFromCaffe(str(_PROTO_PATH), str(_MODEL_PATH))
    return _net

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

def detect_faces_in_media(path: Path, conf_threshold: float = 0.6) -> List[Dict]:
    frame = _load_representative_frame(path)
    h, w = frame.shape[:2]
    net = _get_net()
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    faces = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < conf_threshold:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(float)
        faces.append({"confidence": confidence, "bbox": (x1, y1, x2, y2)})

    faces.sort(key=lambda f: (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]), reverse=True)

    results = []
    for i, f in enumerate(faces):
        x1, y1, x2, y2 = f["bbox"]
        results.append({
            "id": f"face_{i}",
            "label": f"Face {i + 1}" + (" (Primary Target)" if i == 0 else ""),
            "confidence": round(f["confidence"], 4),
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        })
    return results
