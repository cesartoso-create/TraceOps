from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users.schemas import UserCreateRequest, UserPasswordResetRequest, UserUpdateRequest


def _user_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "full_name": row.full_name,
        "email": row.email,
        "phone": row.phone,
        "role": row.role_code,
        "is_active": row.is_active,
    }


def list_roles(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, code, name, description
            FROM roles
            ORDER BY code
            """
        )
    ).all()
    return [
        {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "description": row.description,
        }
        for row in rows
    ]


def _get_role_id(db: Session, role_code: str) -> Any:
    role_id = db.execute(
        text("SELECT id FROM roles WHERE code = upper(:role_code)"),
        {"role_code": role_code},
    ).scalar_one_or_none()
    if role_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role_code")
    return role_id


def list_users(
    db: Session,
    role_code: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if role_code:
        conditions.append("r.code = upper(:role_code)")
        params["role_code"] = role_code
    if is_active is not None:
        conditions.append("u.is_active = :is_active")
        params["is_active"] = is_active
    if search:
        conditions.append("(u.full_name ILIKE :search OR u.email ILIKE :search OR u.phone ILIKE :search)")
        params["search"] = f"%{search}%"

    where_clause = " AND ".join(conditions)
    total = db.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE {where_clause}
            """
        ),
        params,
    ).scalar_one()

    rows = db.execute(
        text(
            f"""
            SELECT u.id, u.full_name, u.email, u.phone, u.is_active, r.code AS role_code
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).all()
    return {"items": [_user_dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def get_user(db: Session, user_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT u.id, u.full_name, u.email, u.phone, u.is_active, r.code AS role_code
            FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE u.id = CAST(:user_id AS uuid)
            """
        ),
        {"user_id": user_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_dict(row)


def create_user(db: Session, payload: UserCreateRequest) -> dict[str, Any]:
    role_id = _get_role_id(db, payload.role_code)
    try:
        row = db.execute(
            text(
                """
                INSERT INTO users (full_name, email, phone, password_hash, role_id, is_active)
                VALUES (:full_name, lower(:email), :phone, :password_hash, :role_id, true)
                RETURNING id
                """
            ),
            {
                "full_name": payload.full_name,
                "email": payload.email,
                "phone": payload.phone,
                "password_hash": hash_password(payload.password),
                "role_id": role_id,
            },
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    return get_user(db, str(row.id))


def update_user(db: Session, user_id: str, payload: UserUpdateRequest) -> dict[str, Any]:
    current = get_user(db, user_id)
    role_id = _get_role_id(db, payload.role_code) if payload.role_code else None

    db.execute(
        text(
            """
            UPDATE users
            SET
                full_name = COALESCE(:full_name, full_name),
                phone = CASE WHEN :phone_set THEN :phone ELSE phone END,
                role_id = COALESCE(:role_id, role_id),
                is_active = COALESCE(:is_active, is_active),
                updated_at = now()
            WHERE id = CAST(:user_id AS uuid)
            """
        ),
        {
            "user_id": user_id,
            "full_name": payload.full_name,
            "phone": payload.phone,
            "phone_set": "phone" in payload.model_fields_set,
            "role_id": role_id,
            "is_active": payload.is_active,
        },
    )
    db.commit()

    updated = get_user(db, user_id)
    if current["is_active"] and not updated["is_active"]:
        db.execute(text("UPDATE devices SET is_trusted = false WHERE user_id = CAST(:user_id AS uuid)"), {"user_id": user_id})
        db.commit()
    return updated


def deactivate_user(db: Session, user_id: str) -> dict[str, Any]:
    return update_user(db, user_id, UserUpdateRequest(is_active=False))


def reset_password(db: Session, user_id: str, payload: UserPasswordResetRequest) -> dict[str, Any]:
    get_user(db, user_id)
    db.execute(
        text(
            """
            UPDATE users
            SET password_hash = :password_hash, updated_at = now()
            WHERE id = CAST(:user_id AS uuid)
            """
        ),
        {"user_id": user_id, "password_hash": hash_password(payload.password)},
    )
    db.execute(text("UPDATE devices SET is_trusted = false WHERE user_id = CAST(:user_id AS uuid)"), {"user_id": user_id})
    db.commit()
    return get_user(db, user_id)

