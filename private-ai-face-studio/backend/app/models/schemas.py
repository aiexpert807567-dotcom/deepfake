from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    ANALYZING = "ANALYZING"
    PROCESSING = "PROCESSING"
    RESTORING = "RESTORING"
    ENHANCING = "ENHANCING"
    ENCODING = "ENCODING"
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class QualityPreset(str, Enum):
    BALANCED = "balanced"
    HIGH = "high"
    MAXIMUM = "maximum"

class JobCreateRequest(BaseModel):
    media_type: str
    target_media_id: str
    selected_face_id: str
    reference_ids: List[str]
    quality: QualityPreset = QualityPreset.MAXIMUM
    resolution: str = "original"
    face_restoration: bool = True
    temporal_stabilization: bool = True
    color_matching: bool = True
    lighting_matching: bool = True
    occlusion_handling: bool = True
    super_resolution: bool = True

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_percent: float = 0.0
    current_stage: str = ""
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    result_url: Optional[str] = None
    target_media_type: str
    duration_sec: Optional[float] = None
    warnings: List[str] = []

class WorkerHeartbeat(BaseModel):
    worker_id: str
    gpu_name: Optional[str] = None
    cuda_available: bool = False
    vram_total_mb: Optional[int] = None
    vram_used_mb: Optional[int] = None
    pytorch_version: Optional[str] = None
    ffmpeg_available: bool = False
    status: str = "IDLE"
    current_job_id: Optional[str] = None
