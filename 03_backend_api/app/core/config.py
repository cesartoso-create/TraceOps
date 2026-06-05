from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    traceops_env: str = Field(default="local", alias="TRACEOPS_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://traceops:traceops_dev_password@postgres:5432/traceops",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    storage_provider: str = Field(default="minio", alias="STORAGE_PROVIDER")

    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field(default="127.0.0.1:9000", alias="MINIO_PUBLIC_ENDPOINT")
    minio_bucket: str = Field(default="traceops-local", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_root_user: str = Field(default="traceops", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="traceops_minio_password", alias="MINIO_ROOT_PASSWORD")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")

    supabase_storage_endpoint: str = Field(default="", alias="SUPABASE_STORAGE_ENDPOINT")
    supabase_storage_public_endpoint: str = Field(default="", alias="SUPABASE_STORAGE_PUBLIC_ENDPOINT")
    supabase_storage_bucket: str = Field(default="traceops-evidences", alias="SUPABASE_STORAGE_BUCKET")
    supabase_storage_access_key_id: str = Field(default="", alias="SUPABASE_STORAGE_ACCESS_KEY_ID")
    supabase_storage_secret_access_key: str = Field(default="", alias="SUPABASE_STORAGE_SECRET_ACCESS_KEY")
    supabase_storage_region: str = Field(default="us-east-1", alias="SUPABASE_STORAGE_REGION")
    supabase_storage_secure: bool = Field(default=True, alias="SUPABASE_STORAGE_SECURE")

    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    bootstrap_enabled: bool = Field(default=True, alias="BOOTSTRAP_ENABLED")

    cors_origins_raw: str = Field(default="*", alias="CORS_ORIGINS")

    @cached_property
    def cors_origins(self) -> list[str]:
        if self.cors_origins_raw == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
