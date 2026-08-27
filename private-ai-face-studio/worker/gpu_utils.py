import torch
import shutil

def detect_gpu_environment():
    cuda_avail = torch.cuda.is_available()
    return {
        "cuda_available": cuda_avail,
        "gpu_name": torch.cuda.get_device_name(0) if cuda_avail else "CPU Fallback",
        "vram_total_mb": int(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)) if cuda_avail else 0,
        "vram_used_mb": int(torch.cuda.memory_allocated(0) / (1024 * 1024)) if cuda_avail else 0,
        "pytorch_version": torch.__version__,
        "ffmpeg_available": shutil.which("ffmpeg") is not None
    }
