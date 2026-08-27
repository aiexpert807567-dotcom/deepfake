import os
import time
import requests
from pathlib import Path
from gpu_utils import detect_gpu_environment
from job_processor import JobProcessor

API_URL = os.getenv("API_URL", "http://localhost:8000")
WORKER_AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN", "studio_worker_secret_token_2026")
WORKER_ID = os.getenv("WORKER_ID", "kaggle_gpu_worker_01")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {WORKER_AUTH_TOKEN}"})
processor = JobProcessor()

def run_worker_loop():
    print(f"=== Private AI Face Studio GPU Worker: {WORKER_ID} ===")
    print(f"API Endpoint: {API_URL}")
    while True:
        try:
            gpu_info = detect_gpu_environment()
            session.post(f"{API_URL}/api/worker/heartbeat", json={"worker_id": WORKER_ID, **gpu_info, "status": "IDLE"}, timeout=5)
            
            resp = session.get(f"{API_URL}/api/worker/poll", timeout=10)
            if resp.status_code == 200:
                job = resp.json().get("job")
                if job:
                    job_id = job["job_id"]
                    print(f"[Worker] Processing Job: {job_id}")
                    
                    def progress_callback(prog, stage, msg):
                        session.post(f"{API_URL}/api/worker/update-progress", data={"job_id": job_id, "status": stage, "stage": msg, "progress": prog})

                    target_path = Path(f"./temp_target_{job_id}")
                    res = processor.process_job(job["payload"], target_path, [], progress_callback)
                    
                    with open(res, "rb") as rf:
                        session.post(f"{API_URL}/api/worker/upload-result", data={"job_id": job_id}, files={"result_file": rf})
                    print(f"[Worker] Completed Job: {job_id}")
            time.sleep(3)
        except Exception as e:
            print(f"[Worker Error]: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker_loop()
