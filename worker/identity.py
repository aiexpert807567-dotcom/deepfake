import numpy as np
import cv2

_face_app = None


def _get_face_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app


def estimate_face_pose(face):
    """Estimate yaw/pitch/roll in degrees from the five facial landmarks."""
    kps = getattr(face, "kps", None)
    if kps is None:
        kps = getattr(face, "landmark_5", None)
    if kps is None:
        return np.zeros(3, dtype=np.float32)

    image_points = np.asarray(kps, dtype=np.float32).reshape(5, 2)
    model_points = np.array([
        [-30.0, -30.0, 30.0],
        [30.0, -30.0, 30.0],
        [0.0, 0.0, 0.0],
        [-25.0, 30.0, 20.0],
        [25.0, 30.0, 20.0],
    ], dtype=np.float32)

    x1, y1, x2, y2 = [float(v) for v in face.bbox]
    width = max(x2 - x1, 1.0)
    height = max(y2 - y1, 1.0)
    focal = max(width, height) * 1.8
    center = ((x1 + x2) * 0.5, (y1 + y2) * 0.5)
    camera = np.array([
        [focal, 0.0, center[0]],
        [0.0, focal, center[1]],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

    try:
        ok, rvec, _ = cv2.solvePnP(
            model_points, image_points, camera, np.zeros((4, 1), dtype=np.float32),
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            raise ValueError("solvePnP failed")
        rotation, _ = cv2.Rodrigues(rvec)
        sy = float(np.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2))
        if sy > 1e-6:
            pitch = np.degrees(np.arctan2(rotation[2, 1], rotation[2, 2]))
            yaw = np.degrees(np.arctan2(-rotation[2, 0], sy))
            roll = np.degrees(np.arctan2(rotation[1, 0], rotation[0, 0]))
        else:
            pitch = np.degrees(np.arctan2(-rotation[1, 2], rotation[1, 1]))
            yaw = np.degrees(np.arctan2(-rotation[2, 0], sy))
            roll = 0.0
        return np.array([yaw, pitch, roll], dtype=np.float32)
    except Exception:
        return np.zeros(3, dtype=np.float32)


class IdentityAggregator:
    def build_unified_identity(self, reference_images: list) -> dict:
        """Build a robust identity plus pose-aware reference candidates."""
        if not reference_images:
            return None

        app = _get_face_app()
        candidates = []

        for index, img in enumerate(reference_images):
            if img is None:
                continue
            faces = app.get(img)
            if not faces:
                print(f"[Identity] Reference {index + 1}: no face detected")
                continue

            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            emb = np.asarray(face.normed_embedding, dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm < 1e-8:
                continue
            emb /= norm

            area = max((face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]), 1.0)
            confidence = float(getattr(face, "det_score", 1.0))
            quality_weight = float(np.sqrt(area) * max(confidence, 0.5))
            pose = estimate_face_pose(face)
            candidates.append({
                "face": face,
                "embedding": emb,
                "weight": quality_weight,
                "pose": pose,
                "index": index,
            })

        if not candidates:
            raise ValueError("No faces could be detected in any reference photo")

        weights = np.asarray([c["weight"] for c in candidates], dtype=np.float32)
        embeddings = np.stack([c["embedding"] for c in candidates])
        centroid = np.average(embeddings, axis=0, weights=weights)
        centroid /= np.linalg.norm(centroid) + 1e-8

        if len(candidates) >= 3:
            similarity = embeddings @ centroid
            threshold = max(0.35, float(np.median(similarity) - 0.12))
            keep = similarity >= threshold
            if np.count_nonzero(keep) >= 2:
                candidates = [c for c, k in zip(candidates, keep) if k]
                weights = np.asarray([c["weight"] for c in candidates], dtype=np.float32)
                embeddings = np.stack([c["embedding"] for c in candidates])
                centroid = np.average(embeddings, axis=0, weights=weights)
                centroid /= np.linalg.norm(centroid) + 1e-8

        best = max(candidates, key=lambda c: c["weight"])["face"]
        best.embedding = centroid.astype(np.float32)

        # Keep the original embeddings for angle-aware selection. The unified
        # centroid remains the fallback when no pose-specific reference wins.
        reference_candidates = []
        for candidate in candidates:
            source = candidate["face"]
            source.embedding = candidate["embedding"].astype(np.float32)
            reference_candidates.append({
                "face": source,
                "embedding": candidate["embedding"].astype(np.float32),
                "pose": candidate["pose"].astype(np.float32),
                "weight": float(candidate["weight"]),
                "index": int(candidate["index"]),
            })

        print(f"[Identity] Unified identity from {len(candidates)}/{len(reference_images)} usable references")
        return {
            "embedding": centroid,
            "source_face": best,
            "reference_candidates": reference_candidates,
            "num_references_used": len(candidates),
        }


get_face_app = _get_face_app
