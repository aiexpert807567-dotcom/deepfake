import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = os.getenv("APP_ENV", "development")
    secret_key: str = os.getenv("APP_SECRET_KEY", "dev_secret_key_must_be_overridden_in_prod_32c")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123456")
    worker_auth_token: str = os.getenv("WORKER_AUTH_TOKEN", "studio_worker_secret_token_2026")
    
    max_video_duration_sec: int = int(os.getenv("MAX_VIDEO_DURATION", 30))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 500))
    auto_delete_source: bool = os.getenv("AUTO_DELETE_SOURCE", "true").lower() == "true"
    worker_idle_timeout_min: int = int(os.getenv("WORKER_IDLE_TIMEOUT_MINUTES", 30))
    
    storage_dir: str = os.getenv("STORAGE_LOCAL_PATH", "./data/storage")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/studio.db")

settings = Settings()
