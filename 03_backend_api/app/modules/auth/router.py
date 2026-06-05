from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import (
    BootstrapUserRequest,
    DeviceRegisterRequest,
    DeviceResponse,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import bootstrap_admin, login, register_device

router = APIRouter()


@router.post("/bootstrap", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(payload: BootstrapUserRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    if not settings.bootstrap_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap disabled")
    return bootstrap_admin(db, payload)


@router.post("/login", response_model=TokenResponse)
def auth_login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    token = login(db, payload)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    return current_user


@router.post("/devices/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def devices_register(
    payload: DeviceRegisterRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return register_device(db, current_user["id"], payload)

