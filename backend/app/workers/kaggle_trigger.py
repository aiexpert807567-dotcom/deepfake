import json
import os
from pathlib import Path

import requests

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"
KAGGLE_PUSH_URL = "https://www.kaggle.com/api/v1/kernels/push"



def trigger_kaggle_run():
    import os
    import subprocess
    import tempfile

    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not username or not key:
        raise RuntimeError("KAGGLE_USERNAME/KAGGLE_KEY are not configured")

    kernel_dir = KERNEL_DIR

    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["KAGGLE_USERNAME"] = username
        env["KAGGLE_KEY"] = key

        result = subprocess.run(
            ["python", "-m", "kaggle", "kernels", "push", "-p", str(kernel_dir)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Kaggle CLI push failed: {result.stderr.strip() or result.stdout.strip()}"
            )

        return result.stdout.strip()
