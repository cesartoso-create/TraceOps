from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.properties.schemas import (
    PropertyCreateRequest,
    PropertyListResponse,
    PropertyResponse,
    PropertyUpdateRequest,
)
from app.modules.properties.service import create_property, get_property, list_properties, update_property

router = APIRouter()
read_roles = ("ADMIN", "GESTOR", "SUPERVISOR", "LIQUIDADOR", "WIN_VIEWER", "AUDITOR")
write_roles = ("ADMIN", "GESTOR", "SUPERVISOR")


@router.get("", response_model=PropertyListResponse, dependencies=[Depends(require_roles(*read_roles))])
def properties_list(
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    current_status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return list_properties(db, search=search, current_status=current_status, limit=limit, offset=offset)


@router.post(
    "",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*write_roles))],
)
def properties_create(
    payload: PropertyCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return create_property(db, payload, current_user["id"])


@router.get("/{property_id}", response_model=PropertyResponse, dependencies=[Depends(require_roles(*read_roles))])
def properties_get(property_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_property(db, property_id)


@router.patch("/{property_id}", response_model=PropertyResponse, dependencies=[Depends(require_roles(*write_roles))])
def properties_update(property_id: str, payload: PropertyUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return update_property(db, property_id, payload)
