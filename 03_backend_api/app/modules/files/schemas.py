from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    project_id: str
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=120)
    file_kind: str = Field(default="IMAGE", pattern="^(IMAGE|THUMBNAIL|KMZ|KML|PDF|DOCUMENT|ZIP)$")
    evidence_id: str | None = None
    checksum_sha256: str | None = Field(default=None, max_length=128)


class PresignUploadResponse(BaseModel):
    bucket: str
    object_key: str
    upload_url: str
    method: str = "PUT"
    expires_in_seconds: int
    headers: dict[str, str]


class PresignDownloadResponse(BaseModel):
    file_id: str
    bucket: str
    object_key: str
    download_url: str
    expires_in_seconds: int


class CompleteUploadRequest(BaseModel):
    bucket: str
    object_key: str
    original_filename: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    checksum_sha256: str | None = Field(default=None, max_length=128)
    file_kind: str = Field(default="IMAGE", pattern="^(IMAGE|THUMBNAIL|KMZ|KML|PDF|DOCUMENT|ZIP)$")
    evidence_id: str | None = None


class FileResponse(BaseModel):
    id: str
    bucket: str
    object_key: str
    original_filename: str | None = None
    mime_type: str
    size_bytes: int
    checksum_sha256: str | None = None
    file_kind: str
    version: int
