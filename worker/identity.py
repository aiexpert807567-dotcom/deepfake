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


class IdentityAggregator:
    def build_unified_identity(self, reference_images: list) -> dict:
        """Build a robust identity from all usable reference photos."""
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
            candidates.append({"face": face, "embedding": emb, "weight": quality_weight})

        if not candidates:
            raise ValueError("No faces could be detected in any reference photo")

        weights = np.asarray([c["weight"] for c in candidates], dtype=np.float32)
        embeddings = np.stack([c["embedding"] for c in candidates])
        centroid = np.average(embeddings, axis=0, weights=weights)
        centroid /= np.linalg.norm(centroid) + 1e-8

        # When several references are supplied, remove only clear embedding
        # outliers so one bad/unrelated photo cannot corrupt the identity.
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
        best["embedding"] = centroid.astype(np.float32)

        print(f"[Identity] Unified identity from {len(candidates)}/{len(reference_images)} usable references")
        return {
            "embedding": centroid,
            "source_face": best,
            "num_references_used": len(candidates),
        }


get_face_app = _get_face_app
