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
        raise RuntimeError("KAGGLE_USERNAME / KAGGLE_KEY not configured on Render")

    metadata_path = KERNEL_DIR / "kernel-metadata.json"
    notebook_path = KERNEL_DIR / "deepfake.ipynb"

    if not metadata_path.exists():
        raise RuntimeError("kernel-metadata.json not found")
    if not notebook_path.exists():
        raise RuntimeError("deepfake.ipynb not found")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid Kaggle notebook JSON: {exc}") from exc

    # Kaggle requires every cell source to be an array of strings.
    for cell in notebook.get("cells", []):
        source = cell.get("source", [])
        if isinstance(source, str):
            cell["source"] = source.splitlines(True)
        elif not isinstance(source, list):
            cell["source"] = [str(source)]

    # Validate the exact structure before sending it.
    for i, cell in enumerate(notebook.get("cells", [])):
        if not isinstance(cell.get("source"), list):
            raise RuntimeError(f"Notebook cell {i} source is not a list")
        if not all(isinstance(line, str) for line in cell["source"]):
            raise RuntimeError(f"Notebook cell {i} contains invalid source data")

    metadata["enable_gpu"] = True
    metadata["enable_internet"] = True
    metadata["enable_tpu"] = False
    metadata["machine_shape"] = "NvidiaTeslaT4"

    # Kaggle's push API expects the notebook itself as the `text` field.
    payload = {
        "id": int(metadata.get("id_no", 132245566)),
        "title": metadata.get("title", "deepfake"),
        "code_file": metadata.get("code_file", "deepfake.ipynb"),
        "language": metadata.get("language", "python"),
        "kernel_type": metadata.get("kernel_type", "notebook"),
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "enable_tpu": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": metadata.get("dataset_sources", []),
        "kernel_sources": metadata.get("kernel_sources", []),
        "competition_sources": metadata.get("competition_sources", []),
        "model_sources": metadata.get("model_sources", []),
        "docker_image": metadata.get("docker_image"),
        "text": json.dumps(notebook, ensure_ascii=False, separators=(",", ":")),
    }

    response = requests.post(
        KAGGLE_PUSH_URL,
        auth=(username, key),
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text[:2000]

        raise RuntimeError(
            f"Kaggle API HTTP {response.status_code}: {detail}"
        )

    try:
        result = response.json()
    except Exception:
        result = response.text

    return {
        "triggered": True,
        "gpu_enabled": True,
        "internet_enabled": True,
        "machine_shape": "NvidiaTeslaT4",
        "result": result,
    }
