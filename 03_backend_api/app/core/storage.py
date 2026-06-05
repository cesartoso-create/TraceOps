from dataclasses import dataclass

import boto3
from botocore.client import Config
from fastapi import HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class StorageConfig:
    provider: str
    internal_endpoint: str
    public_endpoint: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region: str
    secure: bool
    auto_create_bucket: bool


def _normalize_endpoint(endpoint: str) -> str:
    return endpoint.removeprefix("https://").removeprefix("http://").strip().rstrip("/")


def active_storage_config() -> StorageConfig:
    provider = settings.storage_provider.lower().strip()
    if provider == "supabase":
        endpoint = _normalize_endpoint(settings.supabase_storage_endpoint)
        public_endpoint = _normalize_endpoint(settings.supabase_storage_public_endpoint or settings.supabase_storage_endpoint)
        missing = [
            name
            for name, value in {
                "SUPABASE_STORAGE_ENDPOINT": endpoint,
                "SUPABASE_STORAGE_ACCESS_KEY_ID": settings.supabase_storage_access_key_id,
                "SUPABASE_STORAGE_SECRET_ACCESS_KEY": settings.supabase_storage_secret_access_key,
                "SUPABASE_STORAGE_BUCKET": settings.supabase_storage_bucket,
            }.items()
            if not value
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Missing Supabase storage configuration: {', '.join(missing)}",
            )
        return StorageConfig(
            provider="supabase",
            internal_endpoint=endpoint,
            public_endpoint=public_endpoint,
            bucket=settings.supabase_storage_bucket,
            access_key_id=settings.supabase_storage_access_key_id,
            secret_access_key=settings.supabase_storage_secret_access_key,
            region=settings.supabase_storage_region,
            secure=settings.supabase_storage_secure,
            auto_create_bucket=False,
        )

    return StorageConfig(
        provider="minio",
        internal_endpoint=_normalize_endpoint(settings.minio_endpoint),
        public_endpoint=_normalize_endpoint(settings.minio_public_endpoint),
        bucket=settings.minio_bucket,
        access_key_id=settings.minio_root_user,
        secret_access_key=settings.minio_root_password,
        region=settings.s3_region,
        secure=settings.minio_secure,
        auto_create_bucket=True,
    )


def _scheme(config: StorageConfig) -> str:
    return "https" if config.secure else "http"


def storage_client(endpoint: str | None = None):
    config = active_storage_config()
    resolved_endpoint = _normalize_endpoint(endpoint or config.internal_endpoint)
    return boto3.client(
        "s3",
        endpoint_url=f"{_scheme(config)}://{resolved_endpoint}",
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name=config.region,
    )


def internal_storage_client():
    config = active_storage_config()
    return storage_client(config.internal_endpoint)


def public_storage_client():
    config = active_storage_config()
    return storage_client(config.public_endpoint)


def ensure_bucket() -> None:
    config = active_storage_config()
    client = internal_storage_client()
    try:
        client.head_bucket(Bucket=config.bucket)
    except Exception as exc:
        if not config.auto_create_bucket:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage bucket '{config.bucket}' not available. Create it in {config.provider} before uploading files.",
            ) from exc
        client.create_bucket(Bucket=config.bucket)
