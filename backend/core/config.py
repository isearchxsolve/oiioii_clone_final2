import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "oiioii"
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    api_prefix: str = "/api/v1"

    # Security
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS")

    # Database
    database_url: str = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")

    # Redis / Job Queue
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    job_queue_name: str = "media_generation"
    job_default_timeout: int = 300
    job_max_retries: int = 3

    # Storage
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")  # local, s3, gcs
    storage_local_path: str = Field(default="./data/assets", alias="STORAGE_LOCAL_PATH")
    storage_s3_bucket: Optional[str] = Field(default=None, alias="STORAGE_S3_BUCKET")
    storage_s3_region: Optional[str] = Field(default=None, alias="STORAGE_S3_REGION")
    storage_s3_access_key: Optional[str] = Field(default=None, alias="STORAGE_S3_ACCESS_KEY")
    storage_s3_secret_key: Optional[str] = Field(default=None, alias="STORAGE_S3_SECRET_KEY")
    storage_public_url: Optional[str] = Field(default=None, alias="STORAGE_PUBLIC_URL")

    # Media Generation API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    replicate_api_token: Optional[str] = Field(default=None, alias="REPLICATE_API_TOKEN")
    stability_api_key: Optional[str] = Field(default=None, alias="STABILITY_API_KEY")
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")
    runway_api_key: Optional[str] = Field(default=None, alias="RUNWAY_API_KEY")
    pika_api_key: Optional[str] = Field(default=None, alias="PIKA_API_KEY")
    luma_api_key: Optional[str] = Field(default=None, alias="LUMA_API_KEY")

    # Media Generation Defaults
    default_image_model: str = "gpt-image-1"
    default_video_model: str = "gen-3-alpha"
    default_audio_model: str = "eleven_multilingual_v2"
    default_upscale_model: str = "esrgan"

    # Workflow Settings
    workflow_max_concurrent_jobs: int = Field(default=5, alias="WORKFLOW_MAX_CONCURRENT_JOBS")
    workflow_step_timeout: int = Field(default=600, alias="WORKFLOW_STEP_TIMEOUT")
    storyboard_frames_per_scene: int = Field(default=4, alias="STORYBOARD_FRAMES_PER_SCENE")

    # Asset Store
    asset_store_enabled: bool = True
    asset_max_file_size_mb: int = Field(default=500, alias="ASSET_MAX_FILE_SIZE_MB")
    asset_allowed_extensions: List[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".wav", ".mp3", ".glb", ".gltf"]
    )

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("asset_allowed_extensions", mode="before")
    @classmethod
    def parse_asset_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    def get_media_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a media generation provider."""
        key_map = {
            "openai": self.openai_api_key,
            "replicate": self.replicate_api_token,
            "stability": self.stability_api_key,
            "elevenlabs": self.elevenlabs_api_key,
            "runway": self.runway_api_key,
            "pika": self.pika_api_key,
            "luma": self.luma_api_key,
        }
        return key_map.get(provider.lower())


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience function for dependency injection
def get_config() -> Settings:
    return get_settings()