import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Boolean, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.models.schemas import WorkerHeartbeat


class Base(DeclarativeBase):
    pass


class WorkerState(Base):
    __tablename__ = "worker_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkerManager:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "sqlite:///./studio_jobs.db")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
        Base.metadata.create_all(self.engine)

        self.last_heartbeat: Optional[WorkerHeartbeat] = None
        self.last_seen: Optional[datetime] = None
        self.enabled = self._load_enabled()
        self.shutdown_requested = False

    def _load_enabled(self) -> bool:
        with Session(self.engine) as session:
            state = session.get(WorkerState, 1)
            if state is None:
                state = WorkerState(id=1, enabled=False)
                session.add(state)
                session.commit()
                return False
            return bool(state.enabled)

    def _save_enabled(self, enabled: bool):
        with Session(self.engine) as session:
            state = session.get(WorkerState, 1)
            if state is None:
                state = WorkerState(id=1, enabled=enabled)
                session.add(state)
            else:
                state.enabled = enabled
            session.commit()

    def set_power(self, enabled: bool):
        self.enabled = bool(enabled)
        self._save_enabled(self.enabled)
        self.shutdown_requested = not self.enabled
        if not self.enabled:
            self.last_heartbeat = None
            self.last_seen = None
        else:
            self.shutdown_requested = False

    def record_heartbeat(self, hb: WorkerHeartbeat):
        if not self.enabled:
            return
        self.last_heartbeat = hb
        self.last_seen = datetime.now(timezone.utc)

    def request_shutdown(self):
        self.set_power(False)

    def reset_shutdown(self):
        self.shutdown_requested = False

    def get_status(self) -> dict:
        if not self.enabled:
            return {
                "online": False,
                "enabled": False,
                "status": "OFF",
                "message": "GPU worker disabled by operator.",
            }

        if not self.last_seen:
            return {
                "online": False,
                "enabled": True,
                "status": "OFFLINE",
                "message": "GPU enabled. Waiting for the Kaggle worker to connect.",
            }

        now = datetime.now(timezone.utc)
        is_online = (now - self.last_seen) < timedelta(minutes=2)
        return {
            "online": is_online,
            "enabled": True,
            "status": self.last_heartbeat.status if is_online else "OFFLINE",
            "gpu_name": self.last_heartbeat.gpu_name if is_online else None,
            "cuda_available": self.last_heartbeat.cuda_available if is_online else False,
            "vram_total_mb": self.last_heartbeat.vram_total_mb if is_online else None,
            "vram_used_mb": self.last_heartbeat.vram_used_mb if is_online else None,
            "pytorch_version": self.last_heartbeat.pytorch_version if is_online else None,
            "ffmpeg_available": self.last_heartbeat.ffmpeg_available if is_online else False,
            "current_job_id": self.last_heartbeat.current_job_id if is_online else None,
        }


worker_manager = WorkerManager()
