import os
import subprocess
import sys

os.environ["API_URL"] = "https://ai-face-studio-backend-d56h.onrender.com"
os.environ["WORKER_AUTH_TOKEN"] = "studio_worker_secret_token_2026"
os.environ["WORKER_ID"] = "kaggle_t4_gpu"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "worker/requirements.txt"], check=True)

subprocess.run(["apt-get", "update", "-qq"], check=False)
subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=False)

subprocess.run([sys.executable, "-u", "worker/worker.py"], check=True)
