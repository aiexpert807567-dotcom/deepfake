from datetime import datetime, timezone, timedelta
from typing import Optional
from app.models.schemas import WorkerHeartbeat

class WorkerManager:
    def __init__(self):
        self.last_heartbeat: Optional[WorkerHeartbeat] = None
        self.last_seen: Optional[datetime] = None
        self.enabled = True

    def set_power(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.last_heartbeat = None
            self.last_seen = None

    def record_heartbeat(self, hb: WorkerHeartbeat):
        if not self.enabled:
            return
        self.last_heartbeat = hb
        self.last_seen = datetime.now(timezone.utc)

    def get_status(self) -> dict:
        if not self.enabled:
            return {"online": False, "enabled": False, "status": "OFF", "message": "GPU worker disabled by operator."}
        if not self.last_seen:
            return {"online": False, "enabled": True, "status": "OFFLINE", "message": "No GPU worker active."}
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
            "current_job_id": self.last_heartbeat.current_job_id if is_online else None
        }

worker_manager = WorkerManager()
