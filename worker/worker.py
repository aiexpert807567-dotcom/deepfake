import os
import sys
import time
import requests
from pathlib import Path
from gpu_utils import detect_gpu_environment
from job_processor import JobProcessor

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
WORKER_AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN")
WORKER_ID = os.getenv("WORKER_ID", "kaggle_gpu_worker_01")
if not WORKER_AUTH_TOKEN:
    raise RuntimeError("WORKER_AUTH_TOKEN environment variable is required")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {WORKER_AUTH_TOKEN}"})
processor = JobProcessor()

def run_worker_loop():
    print(f"=== Private AI Face Studio GPU Worker: {WORKER_ID} ===")
    print(f"Connected Backend: {API_URL}")
    print("[*] Worker is active and waiting for jobs...")
    
    while True:
        try:
            power = session.get(f"{API_URL}/api/worker/power-status", timeout=10)
            if power.status_code == 200 and power.json().get("enabled") is False:
                print("[Worker] Remote GPU switch is OFF. Shutting down to free the Kaggle GPU session...")
                sys.exit(0)

            gpu_info = detect_gpu_environment()
            session.post(f"{API_URL}/api/worker/heartbeat", json={"worker_id": WORKER_ID, **gpu_info, "status": "IDLE"}, timeout=5)
            resp = session.get(f"{API_URL}/api/worker/poll", timeout=10)
            if resp.status_code != 200:
                time.sleep(5)
                continue
            data = resp.json()
            if data.get("enabled") is False:
                time.sleep(15)
                continue
            job = data.get("job")
            if job:
                job_id = job["job_id"]
                payload = job["payload"]
                print(f"[Worker] Processing Job: {job_id}")

                def progress_callback(prog, stage, msg, warning=None):
                    try:
                        data = {"job_id": job_id, "status": stage, "stage": msg, "progress": prog}
                        if warning:
                            data["warning"] = warning
                        session.post(f"{API_URL}/api/worker/update-progress", data=data, timeout=10)
                    except Exception as exc:
                        print(f"[Worker] Progress update failed: {exc}")

                target_id = payload["target_media_id"]
                target_path = Path(f"./temp_target_{job_id}")
                r = session.get(f"{API_URL}/api/worker/media/{target_id}", stream=True, timeout=120)
                r.raise_for_status()
                with open(target_path, "wb") as out:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            out.write(chunk)

                reference_files = []
                for ref_id in payload.get("reference_ids", []):
                    ref_path = Path(f"./temp_ref_{job_id}_{ref_id}")
                    r = session.get(f"{API_URL}/api/worker/media/{ref_id}", timeout=120)
                    r.raise_for_status()
                    ref_path.write_bytes(r.content)
                    reference_files.append(ref_path)

                try:
                    res = processor.process_job(payload, target_path, reference_files, progress_callback)
                    with open(res, "rb") as rf:
                        upload = session.post(f"{API_URL}/api/worker/upload-result", data={"job_id": job_id}, files={"result_file": rf}, timeout=300)
                        upload.raise_for_status()
                    print(f"[Worker] Completed Job: {job_id}")
                except Exception as exc:
                    print(f"[Worker] Job failed: {exc}")
                    session.post(f"{API_URL}/api/worker/update-progress", data={"job_id": job_id, "status": "FAILED", "stage": "Processing failed", "progress": 0, "error": str(exc)}, timeout=10)
                finally:
                    target_path.unlink(missing_ok=True)
                    for ref in reference_files:
                        ref.unlink(missing_ok=True)

                print("[Worker] Job finished. Exiting after single job (auto-shutdown mode).")
                sys.exit(0)
            time.sleep(3)
        except Exception as exc:
            print(f"[Worker Error]: {exc}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker_loop()
