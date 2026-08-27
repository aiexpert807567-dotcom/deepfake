import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import settings

class LocalStorage:
    def __init__(self):
        self.base_dir = Path(settings.storage_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.results_dir = self.base_dir / "results"
        for d in [self.uploads_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _generate_safe_filename(self, original_filename: str) -> str:
        ext = Path(original_filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".avi"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")
        return f"{uuid.uuid4().hex}{ext}"

    async def save_upload(self, file: UploadFile) -> tuple[str, Path]:
        filename = self._generate_safe_filename(file.filename or "upload.bin")
        target_path = self.uploads_dir / filename
        async with aiofiles.open(target_path, "wb") as out_file:
            content = await file.read()
            if len(content) > settings.max_upload_size_mb * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")
            await out_file.write(content)
        return filename.split(".")[0], target_path

    def get_upload_path(self, filename_or_id: str) -> Path:
        matches = list(self.uploads_dir.glob(f"{filename_or_id}*"))
        if not matches:
            raise HTTPException(status_code=404, detail="File not found")
        return matches[0]

    def cleanup_file(self, path: Path):
        try:
            if path.exists():
                os.remove(path)
        except Exception:
            pass

storage = LocalStorage()
