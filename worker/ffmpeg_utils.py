import subprocess
from pathlib import Path

def extract_audio(video_path: Path, output_audio_path: Path) -> bool:
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "copy", str(output_audio_path)]
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except Exception:
        return False

def mux_frames_and_audio(frames_pattern: str, audio_path: Path, output_video_path: Path, fps: float) -> bool:
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", frames_pattern]
    if audio_path and audio_path.exists():
        cmd.extend(["-i", str(audio_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(output_video_path)])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video_path)])
    return subprocess.run(cmd, capture_output=True).returncode == 0
