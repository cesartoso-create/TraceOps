from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.storage import active_storage_config, ensure_bucket, internal_storage_client, public_storage_client
from app.modules.files.schemas import CompleteUploadRequest, PresignUploadRequest

UPLOAD_EXPIRATION_SECONDS = 900


def _safe_filename(filename: str) -> str:
    return filename.replace("\\", "_").replace("/", "_").strip() or "upload.bin"


def _object_key(payload: PresignUploadRequest) -> str:
    safe_name = _safe_filename(payload.filename)
    prefix = f"projects/{payload.project_id}/evidences"
    if payload.evidence_id:
        prefix = f"{prefix}/{payload.evidence_id}"
    return f"{prefix}/{uuid4()}-{safe_name}"


def create_presigned_upload(payload: PresignUploadRequest) -> dict:
    storage = active_storage_config()
    ensure_bucket()
    object_key = _object_key(payload)
    headers = {"Content-Type": payload.mime_type}
    upload_url = public_storage_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": storage.bucket,
            "Key": object_key,
            "ContentType": payload.mime_type,
        },
        ExpiresIn=UPLOAD_EXPIRATION_SECONDS,
        HttpMethod="PUT",
    )
    return {
        "bucket": storage.bucket,
        "object_key": object_key,
        "upload_url": upload_url,
        "method": "PUT",
        "expires_in_seconds": UPLOAD_EXPIRATION_SECONDS,
        "headers": headers,
    }


def create_presigned_download(db: Session, file_id: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT id, bucket, object_key
            FROM files
            WHERE id = CAST(:file_id AS uuid)
            """
        ),
        {"file_id": file_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    download_url = public_storage_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": row.bucket, "Key": row.object_key},
        ExpiresIn=UPLOAD_EXPIRATION_SECONDS,
        HttpMethod="GET",
    )
    return {
        "file_id": str(row.id),
        "bucket": row.bucket,
        "object_key": row.object_key,
        "download_url": download_url,
        "expires_in_seconds": UPLOAD_EXPIRATION_SECONDS,
    }


def _file_dict(row) -> dict:
    return {
        "id": str(row.id),
        "bucket": row.bucket,
        "object_key": row.object_key,
        "original_filename": row.original_filename,
        "mime_type": row.mime_type,
        "size_bytes": row.size_bytes,
        "checksum_sha256": row.checksum_sha256,
        "file_kind": row.file_kind,
        "version": row.version,
    }


def complete_upload(db: Session, payload: CompleteUploadRequest, user_id: str) -> dict:
    storage = active_storage_config()
    if payload.bucket != storage.bucket:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid bucket")

    try:
        internal_storage_client().head_object(Bucket=payload.bucket, Key=payload.object_key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded object not found") from exc

    row = db.execute(
        text(
            """
            INSERT INTO files (
                bucket, object_key, original_filename, mime_type, size_bytes,
                checksum_sha256, file_kind, uploaded_by
            )
            VALUES (
                :bucket, :object_key, :original_filename, :mime_type, :size_bytes,
                :checksum_sha256, :file_kind, CAST(:user_id AS uuid)
            )
            ON CONFLICT (object_key)
            DO UPDATE SET
                size_bytes = EXCLUDED.size_bytes,
                checksum_sha256 = EXCLUDED.checksum_sha256,
                version = files.version + 1
            RETURNING id, bucket, object_key, original_filename, mime_type, size_bytes,
                      checksum_sha256, file_kind, version
            """
        ),
        {"user_id": user_id, **payload.model_dump()},
    ).first()

    if payload.evidence_id:
        db.execute(
            text(
                """
                UPDATE evidences
                SET file_id = :file_id
                WHERE id = CAST(:evidence_id AS uuid)
                """
            ),
            {"file_id": row.id, "evidence_id": payload.evidence_id},
        )

    db.commit()
    return _file_dict(row)
