import json
import os
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"


def _force_kaggle_resources_enabled() -> None:
    """Make every GPU start request use a Kaggle GPU session with Internet."""
    metadata_path = KERNEL_DIR / "kernel-metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("Kaggle kernel-metadata.json not found")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["enable_gpu"] = True
    metadata["enable_tpu"] = False
    metadata["enable_internet"] = True
    metadata["machine_shape"] = "NvidiaTeslaT4"
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


def trigger_kaggle_run() -> dict:
    """
    Starts a fresh Kaggle execution with BOTH GPU and Internet enabled.
    The resource flags are enforced immediately before kernels_push so a
    future config change cannot accidentally start an offline CPU session.
    """
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        raise RuntimeError("KAGGLE_USERNAME / KAGGLE_KEY not configured on this backend")

    from kaggle.api.kaggle_api_extended import KaggleApi

    if not KERNEL_DIR.exists():
        raise RuntimeError(f"kaggle_kernel directory not found at {KERNEL_DIR}")

    _force_kaggle_resources_enabled()

    api = KaggleApi()
    api.authenticate()
    result = api.kernels_push(str(KERNEL_DIR))
    return {
        "triggered": True,
        "gpu_enabled": True,
        "internet_enabled": True,
        "machine_shape": "NvidiaTeslaT4",
        "result": str(result),
    }
