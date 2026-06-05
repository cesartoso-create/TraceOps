from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import BootstrapUserRequest, DeviceRegisterRequest, LoginRequest


def _row_to_user(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "full_name": row.full_name,
        "email": row.email,
        "role": row.role_code,
        "is_active": row.is_active,
    }


def get_user_by_email(db: Session, email: str) -> Any | None:
    return db.execute(
        text(
            """
            SELECT u.id, u.full_name, u.email, u.password_hash, u.is_active, r.code AS role_code
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE lower(u.email) = lower(:email)
            """
        ),
        {"email": email},
    ).first()


def get_user_by_id(db: Session, user_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT u.id, u.full_name, u.email, u.is_active, r.code AS role_code
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE u.id = CAST(:user_id AS uuid)
            """
        ),
        {"user_id": user_id},
    ).first()
    if row is None or not row.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _row_to_user(row)


def bootstrap_admin(db: Session, payload: BootstrapUserRequest) -> dict[str, Any]:
    user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    if user_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bootstrap already completed")

    role_id = db.execute(text("SELECT id FROM roles WHERE code = 'ADMIN'")).scalar_one_or_none()
    if role_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ADMIN role missing")

    row = db.execute(
        text(
            """
            INSERT INTO users (full_name, email, password_hash, role_id, is_active)
            VALUES (:full_name, lower(:email), :password_hash, :role_id, true)
            RETURNING id, full_name, email, is_active
            """
        ),
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "role_id": role_id,
        },
    ).first()
    db.commit()
    return {
        "id": str(row.id),
        "full_name": row.full_name,
        "email": row.email,
        "role": "ADMIN",
        "is_active": row.is_active,
    }


def login(db: Session, payload: LoginRequest) -> str:
    row = get_user_by_email(db, payload.email)
    if row is None or not row.is_active or not row.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, row.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    db.execute(text("UPDATE users SET last_login_at = now() WHERE id = :id"), {"id": row.id})
    db.commit()
    return create_access_token(str(row.id), {"role": row.role_code, "email": row.email})


def register_device(db: Session, user_id: str, payload: DeviceRegisterRequest) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            INSERT INTO devices (user_id, device_uuid, platform, app_version, last_seen_at, is_trusted)
            VALUES (CAST(:user_id AS uuid), :device_uuid, :platform, :app_version, now(), true)
            ON CONFLICT (device_uuid)
            DO UPDATE SET
                user_id = EXCLUDED.user_id,
                platform = EXCLUDED.platform,
                app_version = EXCLUDED.app_version,
                last_seen_at = now()
            RETURNING id, device_uuid, platform, app_version, is_trusted
            """
        ),
        {
            "user_id": user_id,
            "device_uuid": payload.device_uuid,
            "platform": payload.platform,
            "app_version": payload.app_version,
        },
    ).first()
    db.commit()
    return {
        "id": str(row.id),
        "device_uuid": row.device_uuid,
        "platform": row.platform,
        "app_version": row.app_version,
        "is_trusted": row.is_trusted,
    }

