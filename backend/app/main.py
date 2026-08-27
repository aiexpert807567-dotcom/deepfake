import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import aiofiles

from app.config import settings
from app.auth.security import create_access_token, verify_token, verify_worker_token
from app.models.schemas import JobCreateRequest, JobResponse, JobStatus, WorkerHeartbeat, WorkerPowerRequest
from app.jobs.manager import job_manager
from app.workers.manager import worker_manager
from app.storage.local_storage import storage
from app.utils.media import analyze_media_file, assess_reference_quality

app = FastAPI(title="Private AI Face Studio API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username != settings.admin_username or password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_access_token({"sub": username})
    return {"access_token": token, "token_type": "bearer", "user": {"username": username}}

@app.get("/api/auth/me")
async def get_me(user: dict = Depends(verify_token)):
    return {"username": user.get("sub"), "role": "admin"}

@app.post("/api/media/upload-target")
async def upload_target(file: UploadFile = File(...), user: dict = Depends(verify_token)):
    file_id, file_path = await storage.save_upload(file)
    try:
        analysis = analyze_media_file(file_path)
        if analysis["media_type"] == "video" and analysis["duration_sec"] > settings.max_video_duration_sec:
            storage.cleanup_file(file_path)
            raise HTTPException(status_code=400, detail=f"Exceeds max duration of {settings.max_video_duration_sec}s")
        return {"media_id": file_id, "filename": file_path.name, "analysis": analysis}
    except HTTPException:
        raise
    except Exception as exc:
        storage.cleanup_file(file_path)
        raise HTTPException(status_code=400, detail=f"Media analysis failed: {exc}")

@app.post("/api/media/upload-reference")
async def upload_reference(file: UploadFile = File(...), user: dict = Depends(verify_token)):
    file_id, file_path = await storage.save_upload(file)
    analysis = assess_reference_quality(file_path)
    return {"reference_id": file_id, "filename": file_path.name, "analysis": analysis}

@app.get("/api/media/{media_id}/download")
async def download_media(media_id: str, user: dict = Depends(verify_token)):
    path = storage.get_upload_path(media_id)
    return FileResponse(str(path), filename=path.name)

@app.get("/api/media/{media_id}/detect-faces")
async def detect_faces(media_id: str, user: dict = Depends(verify_token)):
    storage.get_upload_path(media_id)
    return {"media_id": media_id, "faces": [{"id": "face_0", "label": "Face 1 (Primary Target)", "confidence": 0.98}, {"id": "face_1", "label": "Face 2 (Background)", "confidence": 0.93}]}

@app.post("/api/jobs", response_model=JobResponse)
async def create_job(req: JobCreateRequest, user: dict = Depends(verify_token)):
    target_path = storage.get_upload_path(req.target_media_id)
    analysis = analyze_media_file(target_path)
    return job_manager.create_job(req, duration_sec=analysis.get("duration_sec", 0.0))

@app.get("/api/jobs", response_model=list[JobResponse])
async def list_jobs(user: dict = Depends(verify_token)):
    return job_manager.list_jobs()

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, user: dict = Depends(verify_token)):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/worker/power")
async def worker_power(req: WorkerPowerRequest, user: dict = Depends(verify_token)):
    if not req.enabled and job_manager.get_active_job():
        raise HTTPException(status_code=409, detail="Cannot turn off GPU while a job is processing.")
    worker_manager.set_power(req.enabled)
    return worker_manager.get_status()

@app.get("/api/worker/power-status")
async def worker_power_status(authorized: bool = Depends(verify_worker_token)):
    return {"enabled": worker_manager.enabled}

@app.post("/api/worker/heartbeat")
async def worker_heartbeat(hb: WorkerHeartbeat, authorized: bool = Depends(verify_worker_token)):
    worker_manager.record_heartbeat(hb)
    return {"status": "ACK", "enabled": worker_manager.enabled}

@app.get("/api/worker/poll")
async def worker_poll(authorized: bool = Depends(verify_worker_token)):
    if not worker_manager.enabled:
        return {"job": None, "enabled": False}
    job = job_manager.get_next_queued_job()
    if not job:
        return {"job": None, "enabled": True}
    job_manager.update_job_status(job["job_id"], JobStatus.INITIALIZING, "Worker assigned", 5.0)
    return {"job": job, "enabled": True}

@app.get("/api/worker/media/{media_id}")
async def worker_download_media(media_id: str, authorized: bool = Depends(verify_worker_token)):
    path = storage.get_upload_path(media_id)
    return FileResponse(str(path), filename=path.name)

@app.post("/api/worker/update-progress")
async def worker_progress(job_id: str = Form(...), status: JobStatus = Form(...), stage: str = Form(...), progress: float = Form(...), error: str = Form(None), authorized: bool = Depends(verify_worker_token)):
    job_manager.update_job_status(job_id, status, stage, progress, error)
    return {"status": "OK"}

@app.post("/api/worker/upload-result")
async def worker_upload_result(job_id: str = Form(...), result_file: UploadFile = File(...), authorized: bool = Depends(verify_worker_token)):
    ext = Path(result_file.filename or "result.bin").suffix.lower() or ".bin"
    res_path = storage.results_dir / f"{job_id}{ext}"
    async with aiofiles.open(res_path, "wb") as f:
        await f.write(await result_file.read())
    result_url = f"/api/results/{job_id}{ext}"
    job_manager.update_job_status(job_id, JobStatus.COMPLETED, "Completed Successfully", 100.0, result_url=result_url)
    return {"result_url": result_url}

@app.get("/api/worker/status")
async def get_worker_status(user: dict = Depends(verify_token)):
    return worker_manager.get_status()

@app.get("/api/results/{filename}")
async def download_result(filename: str):
    path = storage.results_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Result media not found")
    return FileResponse(str(path), filename=path.name)
