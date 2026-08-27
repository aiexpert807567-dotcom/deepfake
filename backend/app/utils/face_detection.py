import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict

_face_app = None

def _get_face_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=-1, det_size=(640, 640))
    return _face_app

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
    app = _get_face_app()
    faces = app.get(frame)
    faces_sorted = sorted(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
        reverse=True,
    )
    results = []
    for i, f in enumerate(faces_sorted):
        x1, y1, x2, y2 = [float(v) for v in f.bbox]
        results.append({
            "id": f"face_{i}",
            "label": f"Face {i + 1}" + (" (Primary Target)" if i == 0 else ""),
            "confidence": round(float(f.det_score), 4),
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        })
    return results
