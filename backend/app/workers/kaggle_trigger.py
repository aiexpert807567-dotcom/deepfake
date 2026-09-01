import json
import os
from pathlib import Path

import requests

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"
KAGGLE_PUSH_URL = "https://www.kaggle.com/api/v1/kernels/push"


def trigger_kaggle_run() -> dict:
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not username or not key:
        raise RuntimeError("KAGGLE_USERNAME / KAGGLE_KEY not configured on this backend")

    metadata_path = KERNEL_DIR / "kernel-metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("Kaggle kernel-metadata.json not found")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    metadata["enable_gpu"] = True
    metadata["enable_internet"] = True
    metadata["enable_tpu"] = False
    metadata["machine_shape"] = "NvidiaTeslaT4"

    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    code_file = KERNEL_DIR / metadata["code_file"]
    if not code_file.exists():
        raise RuntimeError(f"Kaggle code file not found: {code_file}")

    payload = {
        "slug": metadata["id"],
        "newTitle": metadata["title"],
        "text": code_file.read_text(encoding="utf-8"),
        "language": metadata["language"],
        "kernelType": metadata["kernel_type"],
        "isPrivate": metadata["is_private"],
        "enableGpu": True,
        "enableInternet": True,
        "machineShape": "NvidiaTeslaT4",
        "datasetDataSources": metadata.get("dataset_sources", []),
        "kernelDataSources": metadata.get("kernel_sources", []),
        "competitionDataSources": metadata.get("competition_sources", []),
        "modelDataSources": metadata.get("model_sources", []),
    }

    response = requests.post(
        KAGGLE_PUSH_URL,
        auth=(username, key),
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(
            f"Kaggle API HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    try:
        result = response.json()
    except ValueError:
        result = {"raw_response": response.text[:1000]}

    return {
        "triggered": True,
        "gpu_enabled": True,
        "internet_enabled": True,
        "machine_shape": "NvidiaTeslaT4",
        "result": result,
    }
