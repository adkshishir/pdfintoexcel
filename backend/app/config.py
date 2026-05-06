"""Application configuration.

All runtime config flows through `Settings`. Environment variables override
defaults; in tests, instantiate `Settings(...)` directly with overrides.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- core ---
    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- limits ---
    max_upload_bytes: int = 30 * 1024 * 1024  # 30 MB per CRITICAL RULES
    job_ttl_seconds: int = 24 * 60 * 60       # auto-delete after 24h
    job_timeout_seconds: int = 10 * 60        # kill worker job after 10 min

    # --- database ---
    database_url: str = "postgresql+psycopg://converter:converter@postgres:5432/converter"

    # --- queue ---
    redis_url: str = "redis://redis:6379/0"
    celery_concurrency: int = 2

    # --- storage ---
    # "local" for dev / tests, "oracle" for prod (S3-compatible OCI Object Storage)
    storage_backend: Literal["local", "oracle"] = "local"
    storage_local_root: str = "/var/lib/converter/storage"
    storage_bucket: str = "converter"
    oracle_endpoint: str | None = None
    oracle_region: str | None = None
    oracle_access_key: str | None = None
    oracle_secret_key: str | None = None

    # --- pipeline ---
    default_mode: Literal["fast", "accurate"] = "fast"
    ocr_engine: Literal["paddle", "tesseract"] = "paddle"


@lru_cache
def get_settings() -> Settings:
    return Settings()
