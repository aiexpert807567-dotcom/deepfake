import os
import subprocess
import sys
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"


def trigger_kaggle_run():
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not username or not key:
        raise RuntimeError("KAGGLE_USERNAME/KAGGLE_KEY are not configured")

    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = username
    env["KAGGLE_KEY"] = key

    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "push", "-p", str(KERNEL_DIR)],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )

    output = (result.stdout + "\n" + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(f"Kaggle kernel push failed: {output}")

    return output
