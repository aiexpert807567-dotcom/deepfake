import numpy as np

class IdentityAggregator:
    def build_unified_identity(self, reference_images: list) -> np.ndarray:
        if not reference_images:
            return None
        return reference_images[0]
