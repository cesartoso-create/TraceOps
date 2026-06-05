from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.mobile.schemas import MobileFieldPackageResponse, MobileProjectListResponse
from app.modules.mobile.service import get_field_package, list_my_projects

router = APIRouter(dependencies=[Depends(require_roles("TECNICO"))])


@router.get("/my-projects", response_model=MobileProjectListResponse)
def my_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return list_my_projects(db, current_user["id"])


@router.get("/projects/{project_id}/field-package", response_model=MobileFieldPackageResponse)
def project_field_package(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return get_field_package(db, project_id, current_user["id"])

