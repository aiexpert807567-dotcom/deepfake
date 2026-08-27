import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models.schemas import JobResponse, JobStatus, JobCreateRequest

class JobManager:
    def __init__(self):
        # Render's local filesystem is not durable across restarts, so this
        # in-memory queue is intentionally simple but should not be treated as
        # persistent history. A durable DB can be introduced later without
        # changing the API contract.
        self.jobs: Dict[str, dict] = {}

    def create_job(self, req: JobCreateRequest, duration_sec: Optional[float] = None) -> JobResponse:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        job_data = {
            "job_id": job_id, "status": JobStatus.QUEUED, "progress_percent": 0.0,
            "current_stage": "Enqueued for GPU Worker", "error_message": None,
            "created_at": now, "updated_at": now, "result_url": None,
            "target_media_type": req.media_type, "duration_sec": duration_sec,
            "warnings": [], "payload": req.model_dump()
        }
        self.jobs[job_id] = job_data
        return JobResponse(**job_data)

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        return JobResponse(**self.jobs[job_id]) if job_id in self.jobs else None

    def list_jobs(self) -> List[JobResponse]:
        return [JobResponse(**j) for j in sorted(self.jobs.values(), key=lambda x: x["created_at"], reverse=True)]

    def get_next_queued_job(self) -> Optional[dict]:
        for j in self.jobs.values():
            if j["status"] == JobStatus.QUEUED:
                return j
        return None

    def get_active_job(self) -> Optional[dict]:
        active = {JobStatus.INITIALIZING, JobStatus.ANALYZING, JobStatus.PROCESSING, JobStatus.RESTORING,
                  JobStatus.ENHANCING, JobStatus.ENCODING, JobStatus.UPLOADING}
        for j in self.jobs.values():
            if j["status"] in active:
                return j
        return None

    def update_job_status(self, job_id: str, status: JobStatus, stage: str, progress: float, error: str = None, result_url: str = None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["current_stage"] = stage
            self.jobs[job_id]["progress_percent"] = progress
            self.jobs[job_id]["updated_at"] = datetime.now(timezone.utc)
            if error:
                self.jobs[job_id]["error_message"] = error
            if result_url:
                self.jobs[job_id]["result_url"] = result_url

job_manager = JobManager()
