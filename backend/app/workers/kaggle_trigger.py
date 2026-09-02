import os
from pathlib import Path

import requests

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"

KAGGLE_PUSH_URL = "https://www.kaggle.com/api/v1/kernels/push"
KERNEL_SLUG = "aiexpert80756/deepfake"
KERNEL_ID = 132245566


def trigger_kaggle_run():
    token = os.getenv("KAGGLE_API_TOKEN")
    if not token:
        raise RuntimeError("KAGGLE_API_TOKEN is not configured")

    source_file = KERNEL_DIR / "worker_start.py"
    if not source_file.exists():
        raise RuntimeError(f"Missing Kaggle worker file: {source_file}")

    payload = {
        "id": KERNEL_ID,
        "slug": KERNEL_SLUG,
        "newTitle": "deepfake",
        "text": source_file.read_text(encoding="utf-8"),
        "language": "python",
        "kernelType": "script",
        "isPrivate": True,
        "enableInternet": True,
        "enableGpu": True,
        "machineShape": "NvidiaTeslaT4",
    }

    response = requests.post(
        KAGGLE_PUSH_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Kaggle API HTTP {response.status_code}: {response.text}"
        )

    return response.text
