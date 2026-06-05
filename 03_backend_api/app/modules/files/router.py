from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.files.schemas import CompleteUploadRequest, FileResponse, PresignDownloadResponse, PresignUploadRequest, PresignUploadResponse
from app.modules.files.service import complete_upload, create_presigned_download, create_presigned_upload

router = APIRouter(dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO"))])


@router.post("/presign-upload", response_model=PresignUploadResponse)
def presign_upload(payload: PresignUploadRequest) -> dict:
    return create_presigned_upload(payload)


@router.get("/{file_id}/presign-download", response_model=PresignDownloadResponse)
def presign_download(file_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return create_presigned_download(db, file_id)


@router.post("/complete-upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def files_complete_upload(
    payload: CompleteUploadRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return complete_upload(db, payload, current_user["id"])
