import subprocess
from pathlib import Path


def extract_audio(video_path: Path, output_audio_path: Path) -> bool:
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "copy", str(output_audio_path)]
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except Exception:
        return False


def mux_frames_and_audio(frames_pattern: str, audio_path: Path, output_video_path: Path, fps: float) -> bool:
    video_args = [
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", frames_pattern]
    if audio_path and audio_path.exists():
        cmd.extend(["-i", str(audio_path)])
        cmd.extend(video_args)
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest", str(output_video_path)])
    else:
        cmd.extend(video_args)
        cmd.append(str(output_video_path))
    return subprocess.run(cmd, capture_output=True).returncode == 0
