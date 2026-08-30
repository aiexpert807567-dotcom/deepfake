import os
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"

def trigger_kaggle_run() -> dict:
    """
    Pushes a new version of the Kaggle notebook, which starts a fresh
    execution (a fresh GPU session) on Kaggle's infrastructure.
    Requires KAGGLE_USERNAME and KAGGLE_KEY set as environment variables
    on this backend (Render dashboard, not in code).
    """
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        raise RuntimeError("KAGGLE_USERNAME / KAGGLE_KEY not configured on this backend")

    from kaggle.api.kaggle_api_extended import KaggleApi

    if not KERNEL_DIR.exists():
        raise RuntimeError(f"kaggle_kernel directory not found at {KERNEL_DIR}")

    api = KaggleApi()
    api.authenticate()
    result = api.kernels_push(str(KERNEL_DIR))
    return {"triggered": True, "result": str(result)}
