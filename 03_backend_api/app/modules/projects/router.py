from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.domain import ProjectStatus, ProjectType
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.projects.schemas import (
    ProjectAssignRequest,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatusTransitionRequest,
    ProjectUpdateRequest,
)
from app.modules.projects.service import (
    assign_project,
    create_project,
    get_project,
    list_projects,
    transition_project,
    update_project,
)

router = APIRouter()
read_roles = ("ADMIN", "GESTOR", "SUPERVISOR", "LIQUIDADOR", "WIN_VIEWER", "AUDITOR", "TECNICO")
write_roles = ("ADMIN", "GESTOR", "SUPERVISOR")
transition_roles = ("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO")


@router.get("/statuses")
def project_statuses() -> list[str]:
    return [status.value for status in ProjectStatus]


@router.get("/types")
def project_types() -> list[str]:
    return [project_type.value for project_type in ProjectType]


@router.get("", response_model=ProjectListResponse, dependencies=[Depends(require_roles(*read_roles))])
def projects_list(
    db: Annotated[Session, Depends(get_db)],
    current_status: str | None = None,
    project_type: str | None = None,
    crew_id: str | None = None,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return list_projects(
        db,
        current_status=current_status,
        project_type=project_type,
        crew_id=crew_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*write_roles))],
)
def projects_create(
    payload: ProjectCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return create_project(db, payload, current_user["id"])


@router.get("/{project_id}", response_model=ProjectResponse, dependencies=[Depends(require_roles(*read_roles))])
def projects_get(project_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_project(db, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse, dependencies=[Depends(require_roles(*write_roles))])
def projects_update(project_id: str, payload: ProjectUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return update_project(db, project_id, payload)


@router.post("/{project_id}/assign", response_model=ProjectResponse, dependencies=[Depends(require_roles(*write_roles))])
def projects_assign(
    project_id: str,
    payload: ProjectAssignRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return assign_project(db, project_id, payload, current_user["id"])


@router.post(
    "/{project_id}/transition",
    response_model=ProjectResponse,
    dependencies=[Depends(require_roles(*transition_roles))],
)
def projects_transition(
    project_id: str,
    payload: ProjectStatusTransitionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return transition_project(db, project_id, payload, current_user["id"])
