from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.users.schemas import (
    RoleResponse,
    UserCreateRequest,
    UserListResponse,
    UserPasswordResetRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.users.service import (
    create_user,
    deactivate_user,
    get_user,
    list_roles,
    list_users,
    reset_password,
    update_user,
)

router = APIRouter()


@router.get("/roles", response_model=list[RoleResponse], dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def roles(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    return list_roles(db)


@router.get("", response_model=UserListResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def users(
    db: Annotated[Session, Depends(get_db)],
    role_code: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return list_users(db, role_code=role_code, is_active=is_active, search=search, limit=limit, offset=offset)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("ADMIN"))])
def users_create(payload: UserCreateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return create_user(db, payload)


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def users_get(user_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_roles("ADMIN"))])
def users_update(user_id: str, payload: UserUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return update_user(db, user_id, payload)


@router.post("/{user_id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_roles("ADMIN"))])
def users_deactivate(user_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return deactivate_user(db, user_id)


@router.post("/{user_id}/reset-password", response_model=UserResponse, dependencies=[Depends(require_roles("ADMIN"))])
def users_reset_password(
    user_id: str,
    payload: UserPasswordResetRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return reset_password(db, user_id, payload)
