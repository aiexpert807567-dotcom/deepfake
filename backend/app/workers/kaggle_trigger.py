import subprocess
import sys
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parent.parent.parent / "kaggle_kernel"


def trigger_kaggle_run():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kaggle",
            "kernels",
            "push",
            "-p",
            str(KERNEL_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )

    output = (result.stdout + "\n" + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(f"Kaggle kernel push failed: {output}")

    return output
