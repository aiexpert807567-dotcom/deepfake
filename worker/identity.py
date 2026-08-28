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
        """
        reference_images: list of np.ndarray (BGR images, as read by cv2.imread)
        Returns a dict with an averaged, L2-normalized embedding plus one
        representative source face crop for the swapper model to use.
        """
        if not reference_images:
            return None

        app = _get_face_app()
        embeddings = []
        best_face = None
        best_face_area = 0

        for img in reference_images:
            if img is None:
                continue
            faces = app.get(img)
            if not faces:
                continue
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            embeddings.append(face.normed_embedding)

            area = (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])
            if area > best_face_area:
                best_face_area = area
                best_face = face

        if not embeddings:
            raise ValueError("No faces could be detected in any reference photo")

        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / (np.linalg.norm(avg_embedding) + 1e-8)

        # inswapper reads the embedding directly off source_face.normed_embedding,
        # which is a computed property derived from the raw "embedding" field —
        # so we set the underlying field, not the property itself, and overwrite
        # it with our multi-photo average instead of whichever single reference
        # photo happened to have the largest face.
        best_face["embedding"] = avg_embedding.astype(np.float32)

        return {
            "embedding": avg_embedding,
            "source_face": best_face,
            "num_references_used": len(embeddings),
        }

# Reusable across modules so we don't load buffalo_l twice
get_face_app = _get_face_app
