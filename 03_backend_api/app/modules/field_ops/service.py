from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.field_ops.schemas import (
    ContractorCreateRequest,
    ContractorUpdateRequest,
    CrewCreateRequest,
    CrewMemberAddRequest,
    CrewUpdateRequest,
)


def _contractor_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "tax_id": row.tax_id,
        "type": row.type,
        "parent_contractor_id": str(row.parent_contractor_id) if row.parent_contractor_id else None,
        "is_active": row.is_active,
    }


def _crew_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "contractor_id": str(row.contractor_id) if row.contractor_id else None,
        "code": row.code,
        "name": row.name,
        "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
        "is_active": row.is_active,
    }


def _member_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "crew_id": str(row.crew_id),
        "user_id": str(row.user_id),
        "full_name": row.full_name,
        "email": row.email,
        "role": row.role_code,
        "position": row.position,
        "valid_from": row.valid_from,
        "valid_to": row.valid_to,
        "is_active": row.is_active,
    }


def list_contractors(db: Session, type: str | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {}
    if type:
        conditions.append("type = :type")
        params["type"] = type
    if is_active is not None:
        conditions.append("is_active = :is_active")
        params["is_active"] = is_active
    rows = db.execute(
        text(
            f"""
            SELECT id, name, tax_id, type, parent_contractor_id, is_active
            FROM contractors
            WHERE {" AND ".join(conditions)}
            ORDER BY name
            """
        ),
        params,
    ).all()
    return [_contractor_dict(row) for row in rows]


def get_contractor(db: Session, contractor_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT id, name, tax_id, type, parent_contractor_id, is_active
            FROM contractors
            WHERE id = CAST(:contractor_id AS uuid)
            """
        ),
        {"contractor_id": contractor_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor not found")
    return _contractor_dict(row)


def create_contractor(db: Session, payload: ContractorCreateRequest) -> dict[str, Any]:
    try:
        row = db.execute(
            text(
                """
                INSERT INTO contractors (name, tax_id, type, parent_contractor_id, is_active)
                VALUES (:name, :tax_id, :type, CAST(:parent_contractor_id AS uuid), true)
                RETURNING id
                """
            ),
            payload.model_dump(),
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid contractor relation")
    return get_contractor(db, str(row.id))


def update_contractor(db: Session, contractor_id: str, payload: ContractorUpdateRequest) -> dict[str, Any]:
    get_contractor(db, contractor_id)
    db.execute(
        text(
            """
            UPDATE contractors
            SET
                name = COALESCE(:name, name),
                tax_id = CASE WHEN :tax_id_set THEN :tax_id ELSE tax_id END,
                parent_contractor_id = CASE
                    WHEN :parent_contractor_id_set THEN CAST(:parent_contractor_id AS uuid)
                    ELSE parent_contractor_id
                END,
                is_active = COALESCE(:is_active, is_active)
            WHERE id = CAST(:contractor_id AS uuid)
            """
        ),
        {
            **payload.model_dump(),
            "contractor_id": contractor_id,
            "tax_id_set": "tax_id" in payload.model_fields_set,
            "parent_contractor_id_set": "parent_contractor_id" in payload.model_fields_set,
        },
    )
    db.commit()
    return get_contractor(db, contractor_id)


def list_crews(db: Session, contractor_id: str | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {}
    if contractor_id:
        conditions.append("contractor_id = CAST(:contractor_id AS uuid)")
        params["contractor_id"] = contractor_id
    if is_active is not None:
        conditions.append("is_active = :is_active")
        params["is_active"] = is_active
    rows = db.execute(
        text(
            f"""
            SELECT id, contractor_id, code, name, supervisor_id, is_active
            FROM crews
            WHERE {" AND ".join(conditions)}
            ORDER BY code
            """
        ),
        params,
    ).all()
    return [_crew_dict(row) for row in rows]


def get_crew(db: Session, crew_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT id, contractor_id, code, name, supervisor_id, is_active
            FROM crews
            WHERE id = CAST(:crew_id AS uuid)
            """
        ),
        {"crew_id": crew_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return _crew_dict(row)


def create_crew(db: Session, payload: CrewCreateRequest) -> dict[str, Any]:
    try:
        row = db.execute(
            text(
                """
                INSERT INTO crews (contractor_id, code, name, supervisor_id, is_active)
                VALUES (CAST(:contractor_id AS uuid), :code, :name, CAST(:supervisor_id AS uuid), true)
                RETURNING id
                """
            ),
            payload.model_dump(),
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew code already exists or invalid relation")
    return get_crew(db, str(row.id))


def update_crew(db: Session, crew_id: str, payload: CrewUpdateRequest) -> dict[str, Any]:
    get_crew(db, crew_id)
    db.execute(
        text(
            """
            UPDATE crews
            SET
                contractor_id = CASE WHEN :contractor_id_set THEN CAST(:contractor_id AS uuid) ELSE contractor_id END,
                code = COALESCE(:code, code),
                name = COALESCE(:name, name),
                supervisor_id = CASE WHEN :supervisor_id_set THEN CAST(:supervisor_id AS uuid) ELSE supervisor_id END,
                is_active = COALESCE(:is_active, is_active)
            WHERE id = CAST(:crew_id AS uuid)
            """
        ),
        {
            **payload.model_dump(),
            "crew_id": crew_id,
            "contractor_id_set": "contractor_id" in payload.model_fields_set,
            "supervisor_id_set": "supervisor_id" in payload.model_fields_set,
        },
    )
    db.commit()
    return get_crew(db, crew_id)


def list_crew_members(db: Session, crew_id: str) -> list[dict[str, Any]]:
    get_crew(db, crew_id)
    rows = db.execute(
        text(
            """
            SELECT cm.id, cm.crew_id, cm.user_id, u.full_name, u.email, r.code AS role_code,
                   cm.position, cm.valid_from, cm.valid_to, cm.is_active
            FROM crew_members cm
            JOIN users u ON u.id = cm.user_id
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE cm.crew_id = CAST(:crew_id AS uuid)
            ORDER BY cm.is_active DESC, u.full_name
            """
        ),
        {"crew_id": crew_id},
    ).all()
    return [_member_dict(row) for row in rows]


def add_crew_member(db: Session, crew_id: str, payload: CrewMemberAddRequest) -> dict[str, Any]:
    get_crew(db, crew_id)
    try:
        row = db.execute(
            text(
                """
                INSERT INTO crew_members (crew_id, user_id, position, valid_from, is_active)
                VALUES (
                    CAST(:crew_id AS uuid),
                    CAST(:user_id AS uuid),
                    :position,
                    COALESCE(:valid_from, CURRENT_DATE),
                    true
                )
                ON CONFLICT (crew_id, user_id)
                DO UPDATE SET position = EXCLUDED.position, valid_to = NULL, is_active = true
                RETURNING id
                """
            ),
            {"crew_id": crew_id, **payload.model_dump()},
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid crew member")
    members = list_crew_members(db, crew_id)
    return next(member for member in members if member["id"] == str(row.id))


def remove_crew_member(db: Session, crew_id: str, member_id: str) -> dict[str, Any]:
    get_crew(db, crew_id)
    row = db.execute(
        text(
            """
            UPDATE crew_members
            SET is_active = false, valid_to = CURRENT_DATE
            WHERE id = CAST(:member_id AS uuid) AND crew_id = CAST(:crew_id AS uuid)
            RETURNING id
            """
        ),
        {"crew_id": crew_id, "member_id": member_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found")
    db.commit()
    members = list_crew_members(db, crew_id)
    return next(member for member in members if member["id"] == str(row.id))

