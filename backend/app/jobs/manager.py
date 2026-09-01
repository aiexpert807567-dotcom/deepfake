import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import DateTime, Float, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.models.schemas import JobResponse, JobStatus, JobCreateRequest


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    current_stage: Mapped[str] = mapped_column(String(255), default="")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    result_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_media_type: Mapped[str] = mapped_column(String(32))
    duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")


class JobManager:
    def __init__(self):
        # Set DATABASE_URL on Render for durable PostgreSQL. SQLite remains a
        # zero-config fallback for local/dev usage.
        database_url = os.getenv("DATABASE_URL", "sqlite:///./studio_jobs.db")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
        Base.metadata.create_all(self.engine)

    @staticmethod
    def _response(record: JobRecord) -> JobResponse:
        return JobResponse(
            job_id=record.job_id,
            status=JobStatus(record.status),
            progress_percent=record.progress_percent,
            current_stage=record.current_stage,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
            result_url=record.result_url,
            target_media_type=record.target_media_type,
            duration_sec=record.duration_sec,
            warnings=json.loads(record.warnings_json or "[]"),
        )

    def create_job(self, req: JobCreateRequest, duration_sec: Optional[float] = None) -> JobResponse:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        record = JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED.value,
            progress_percent=0.0,
            current_stage="Enqueued for GPU Worker",
            error_message=None,
            created_at=now,
            updated_at=now,
            result_url=None,
            target_media_type=req.media_type,
            duration_sec=duration_sec,
            warnings_json="[]",
            payload_json=json.dumps(req.model_dump(mode="json")),
        )
        with Session(self.engine) as session:
            session.add(record)
            session.commit()
        return self._response(record)

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        with Session(self.engine) as session:
            record = session.get(JobRecord, job_id)
            return self._response(record) if record else None

    def list_jobs(self) -> List[JobResponse]:
        with Session(self.engine) as session:
            records = session.scalars(select(JobRecord).order_by(JobRecord.created_at.desc())).all()
            return [self._response(record) for record in records]

    @staticmethod
    def _payload(record: JobRecord) -> dict:
        return json.loads(record.payload_json or "{}")

    def get_next_queued_job(self) -> Optional[dict]:
        with Session(self.engine) as session:
            record = session.scalars(
                select(JobRecord).where(JobRecord.status == JobStatus.QUEUED.value).order_by(JobRecord.created_at.asc())
            ).first()
            return self._as_worker_dict(record) if record else None

    def get_active_job(self) -> Optional[dict]:
        active = [s.value for s in (
            JobStatus.INITIALIZING, JobStatus.ANALYZING, JobStatus.PROCESSING,
            JobStatus.RESTORING, JobStatus.ENHANCING, JobStatus.ENCODING, JobStatus.UPLOADING
        )]
        with Session(self.engine) as session:
            record = session.scalars(
                select(JobRecord).where(JobRecord.status.in_(active)).order_by(JobRecord.updated_at.desc())
            ).first()
            return self._as_worker_dict(record) if record else None

    def _as_worker_dict(self, record: JobRecord) -> dict:
        return {
            "job_id": record.job_id,
            "status": JobStatus(record.status),
            "progress_percent": record.progress_percent,
            "current_stage": record.current_stage,
            "error_message": record.error_message,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "result_url": record.result_url,
            "target_media_type": record.target_media_type,
            "duration_sec": record.duration_sec,
            "warnings": json.loads(record.warnings_json or "[]"),
            "payload": self._payload(record),
        }

    def update_job_status(self, job_id: str, status: JobStatus, stage: str, progress: float,
                          error: str = None, result_url: str = None, warning: str = None):
        with Session(self.engine) as session:
            record = session.get(JobRecord, job_id)
            if not record:
                return
            record.status = status.value
            record.current_stage = stage
            record.progress_percent = float(progress)
            record.updated_at = datetime.now(timezone.utc)
            if error:
                record.error_message = error
            if result_url:
                record.result_url = result_url
            if warning:
                warnings = json.loads(record.warnings_json or "[]")
                if warning not in warnings:
                    warnings.append(warning)
                    record.warnings_json = json.dumps(warnings)
            session.commit()


job_manager = JobManager()
