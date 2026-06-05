from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_departments(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, name, code
            FROM ubigeo_departments
            ORDER BY name
            """
        )
    ).all()
    return [{"id": str(row.id), "name": row.name, "code": row.code} for row in rows]


def list_provinces(db: Session, department_id: str | None = None) -> list[dict[str, Any]]:
    if not department_id:
        rows = db.execute(
            text(
                """
                SELECT id, department_id, name, code
                FROM ubigeo_provinces
                ORDER BY name
                """
            )
        ).all()
        return [
            {"id": str(row.id), "department_id": str(row.department_id), "name": row.name, "code": row.code}
            for row in rows
        ]

    rows = db.execute(
        text(
            """
            SELECT id, department_id, name, code
            FROM ubigeo_provinces
            WHERE department_id = CAST(:department_id AS uuid)
            ORDER BY name
            """
        ),
        {"department_id": department_id},
    ).all()
    return [
        {"id": str(row.id), "department_id": str(row.department_id), "name": row.name, "code": row.code}
        for row in rows
    ]


def list_districts(db: Session, province_id: str | None = None) -> list[dict[str, Any]]:
    if not province_id:
        rows = db.execute(
            text(
                """
                SELECT id, province_id, name, code
                FROM ubigeo_districts
                ORDER BY name
                """
            )
        ).all()
        return [{"id": str(row.id), "province_id": str(row.province_id), "name": row.name, "code": row.code} for row in rows]

    rows = db.execute(
        text(
            """
            SELECT id, province_id, name, code
            FROM ubigeo_districts
            WHERE province_id = CAST(:province_id AS uuid)
            ORDER BY name
            """
        ),
        {"province_id": province_id},
    ).all()
    return [{"id": str(row.id), "province_id": str(row.province_id), "name": row.name, "code": row.code} for row in rows]
