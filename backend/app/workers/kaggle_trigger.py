import json
import os
import time
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
    """Start a Kaggle execution with GPU + Internet, tolerating transient JSON API errors."""
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        raise RuntimeError("KAGGLE_USERNAME / KAGGLE_KEY not configured on this backend")

    from kaggle.api.kaggle_api_extended import KaggleApi

    if not KERNEL_DIR.exists():
        raise RuntimeError(f"kaggle_kernel directory not found at {KERNEL_DIR}")

    _force_kaggle_resources_enabled()

    api = KaggleApi()
    api.authenticate()

    last_error = None
    for attempt in range(1, 4):
        try:
            result = api.kernels_push(str(KERNEL_DIR))
            return {
                "triggered": True,
                "gpu_enabled": True,
                "internet_enabled": True,
                "machine_shape": "NvidiaTeslaT4",
                "attempt": attempt,
                "result": str(result),
            }
        except json.JSONDecodeError as exc:
            last_error = exc
            print(f"[Kaggle Trigger] JSON response error on attempt {attempt}/3: {exc}")
            if attempt < 3:
                time.sleep(3 * attempt)
                continue
            raise RuntimeError(
                "Kaggle returned an invalid JSON response after 3 startup attempts. "
                "This is a Kaggle API/server response problem, not a GPU configuration problem."
            ) from last_error

    raise RuntimeError("Kaggle GPU startup failed")
