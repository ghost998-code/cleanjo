from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "Garbage Detection API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    LEGACY_API_PREFIX: str = "/api"

    NODE_ENV: str = "development"
    VITE_API_URL: str = "http://localhost:8000/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/garbage_db"
    REDIS_URL: str = "redis://localhost:6379"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_STATUS_CHANGED: str = "report.status.changed"
    KAFKA_TOPIC_REPORT_ASSIGNED: str = "report.assigned"

    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OTP_EXPIRE_MINUTES: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_DEV_MODE: bool = True

    MAX_IMAGE_UPLOAD_BYTES: int = 5 * 1024 * 1024
    MAX_VIDEO_UPLOAD_BYTES: int = 20 * 1024 * 1024
    MAX_DESCRIPTION_LENGTH: int = 500
    MAX_REPORT_PHOTOS: int = 15
    GPS_WARNING_ACCURACY_METERS: float = 20.0
    GPS_MAX_ACCURACY_METERS: float = 10.0

    PUBLIC_BASE_URL: str = "http://localhost:8000"
    LOCAL_UPLOAD_DIR: str = str(Path(__file__).resolve().parents[2] / "uploads")
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
