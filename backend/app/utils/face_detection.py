import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict

_cascade = None

def _get_cascade():
    global _cascade
    if _cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _cascade = cv2.CascadeClassifier(cascade_path)
        if _cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade face detector")
    return _cascade

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
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = _get_cascade()
    detections = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60)
    )

    faces = sorted(detections, key=lambda d: d[2] * d[3], reverse=True)

    results = []
    for i, (x, y, fw, fh) in enumerate(faces):
        results.append({
            "id": f"face_{i}",
            "label": f"Face {i + 1}" + (" (Primary Target)" if i == 0 else ""),
            "confidence": 0.9,
            "bbox": {"x1": float(x), "y1": float(y), "x2": float(x + fw), "y2": float(y + fh)},
        })
    return results
