import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any

def analyze_media_file(filepath: Path) -> Dict[str, Any]:
    ext = filepath.suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        img = cv2.imread(str(filepath))
        if img is None:
            raise ValueError("Unable to decode image")
        h, w = img.shape[:2]
        return {
            "media_type": "image",
            "width": w,
            "height": h,
            "duration_sec": 0.0,
            "has_audio": False,
            "fps": None,
            "frame_count": 1,
            "codec": ext.replace(".", "")
        }
    else:
        cap = cv2.VideoCapture(str(filepath))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0.0
        cap.release()
        return {
            "media_type": "video",
            "width": width,
            "height": height,
            "duration_sec": round(duration, 2),
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "has_audio": True,
            "codec": "h264"
        }

def assess_reference_quality(img_path: Path) -> Dict[str, Any]:
    img = cv2.imread(str(img_path))
    if img is None:
        return {"detected": False, "quality_score": 0.0, "estimated_angle": "Unknown", "warnings": ["Failed to decode"]}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    score = min(100.0, max(10.0, (sharpness / 2.5) + 40.0))
    return {
        "detected": True,
        "quality_score": round(score, 1),
        "estimated_angle": "Front / Angle",
        "sharpness": round(sharpness, 1),
        "warnings": []
    }
