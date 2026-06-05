from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.pext.schemas import (
    PextExecutionPackageCreateRequest,
    PextExecutionPackageResponse,
    PextFieldOutputResponse,
    PextFieldValidationResponse,
    PextPrefeasibilityResponse,
    PextPrefeasibilityUpsertRequest,
    SpliceChartCreateRequest,
    SpliceChartResponse,
    SpliceChartUpdateRequest,
    SpliceEntryCreateRequest,
    SpliceEntryResponse,
)
from app.modules.pext.service import (
    add_splice_entry,
    create_execution_package,
    create_splice_chart,
    get_current_execution_package,
    get_prefeasibility,
    get_field_output,
    get_splice_chart,
    list_splice_charts,
    update_splice_chart,
    upsert_prefeasibility,
    validate_field_output,
)

router = APIRouter()
read_roles = ("ADMIN", "GESTOR", "SUPERVISOR", "LIQUIDADOR", "WIN_VIEWER", "AUDITOR", "TECNICO")
write_roles = ("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO")
supervisor_write_roles = ("ADMIN", "GESTOR", "SUPERVISOR")


@router.get(
    "/projects/{project_id}/field-output",
    response_model=PextFieldOutputResponse,
    dependencies=[Depends(require_roles(*read_roles))],
)
def field_output_get(project_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_field_output(db, project_id)


@router.get(
    "/projects/{project_id}/field-output/validation",
    response_model=PextFieldValidationResponse,
    dependencies=[Depends(require_roles(*read_roles))],
)
def field_output_validation_get(project_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return validate_field_output(db, project_id)


@router.get(
    "/projects/{project_id}/execution-package",
    response_model=PextExecutionPackageResponse,
    dependencies=[Depends(require_roles(*read_roles))],
)
def execution_package_get(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    package_stage: str | None = None,
) -> dict:
    return get_current_execution_package(db, project_id, package_stage)


@router.post(
    "/projects/{project_id}/execution-package",
    response_model=PextExecutionPackageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*supervisor_write_roles))],
)
def execution_package_create(
    project_id: str,
    payload: PextExecutionPackageCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return create_execution_package(db, project_id, current_user["id"], payload)


@router.get(
    "/projects/{project_id}/prefeasibility",
    response_model=PextPrefeasibilityResponse,
    dependencies=[Depends(require_roles(*read_roles))],
)
def prefeasibility_get(project_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_prefeasibility(db, project_id)


@router.put(
    "/projects/{project_id}/prefeasibility",
    response_model=PextPrefeasibilityResponse,
    dependencies=[Depends(require_roles(*write_roles))],
)
def prefeasibility_upsert(
    project_id: str,
    payload: PextPrefeasibilityUpsertRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return upsert_prefeasibility(db, project_id, current_user["id"], payload)


@router.get(
    "/projects/{project_id}/splice-charts",
    response_model=list[SpliceChartResponse],
    dependencies=[Depends(require_roles(*read_roles))],
)
def splice_charts_list(project_id: str, db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    return list_splice_charts(db, project_id)


@router.post(
    "/projects/{project_id}/splice-charts",
    response_model=SpliceChartResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*write_roles))],
)
def splice_charts_create(
    project_id: str,
    payload: SpliceChartCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return create_splice_chart(db, project_id, current_user["id"], payload)


@router.get(
    "/splice-charts/{chart_id}",
    response_model=SpliceChartResponse,
    dependencies=[Depends(require_roles(*read_roles))],
)
def splice_charts_get(chart_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_splice_chart(db, chart_id)


@router.patch(
    "/splice-charts/{chart_id}",
    response_model=SpliceChartResponse,
    dependencies=[Depends(require_roles(*write_roles))],
)
def splice_charts_update(chart_id: str, payload: SpliceChartUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return update_splice_chart(db, chart_id, payload)


@router.post(
    "/splice-charts/{chart_id}/entries",
    response_model=SpliceEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*write_roles))],
)
def splice_entries_add(chart_id: str, payload: SpliceEntryCreateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return add_splice_entry(db, chart_id, payload)
