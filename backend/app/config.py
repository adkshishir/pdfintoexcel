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
    celery_concurrency_processing: int = 2
    celery_concurrency_housekeeping: int = 4

    # --- storage ---
    # "local" for dev / tests, "oracle" for prod (S3-compatible OCI Object Storage)
    storage_backend: Literal["local", "oracle"] = "local"
    storage_local_root: str = "/var/lib/converter/storage"
    storage_bucket: str = "converter"
    oracle_endpoint: str | None = None
    oracle_region: str | None = None
    oracle_access_key: str | None = None
    oracle_secret_key: str | None = None

    # --- analytics (internal dashboard) ---
    analytics_api_key: str = ""

    # --- admin auth ---
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 30
    jwt_refresh_ttl_days: int = 14
    admin_bootstrap_email: str = "admin@pdfintoexcel.com"
    admin_bootstrap_password: str = "admin123"

    # --- pipeline ---
    default_mode: Literal["fast", "accurate"] = "fast"
    ocr_engine: Literal["paddle", "tesseract"] = "paddle"
    # Default OCR languages (see app.ocr.lang_resolve).
    ocr_default_tesseract_lang: str = "eng"
    ocr_default_paddle_lang: str = "en"

    # --- blog generation ---
    blog_llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"


@lru_cache
def get_settings() -> Settings:
    return Settings()
