from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.domain import ProjectStatus
from app.modules.projects.schemas import (
    ProjectAssignRequest,
    ProjectCreateRequest,
    ProjectStatusTransitionRequest,
    ProjectUpdateRequest,
)
from app.modules.pext.service import validate_field_output

ALLOWED_TRANSITIONS = {
    "PREDIO_REGISTRADO": {"FACTIBILIDAD_EN_REVISION", "PENDIENTE_RESPUESTA_WIN", "PREDIO_APROBADO"},
    "FACTIBILIDAD_EN_REVISION": {"PENDIENTE_REVISION"},
    "PENDIENTE_RESPUESTA_WIN": {"PREDIO_APROBADO", "PREDIO_RECHAZADO", "PREDIO_OBSERVADO"},
    "PREDIO_OBSERVADO": {"FACTIBILIDAD_EN_REVISION"},
    "PREDIO_APROBADO": {"ASIGNADO_A_CUADRILLA"},
    "ASIGNADO_A_CUADRILLA": {"EN_EJECUCION"},
    "EN_EJECUCION": {"PENDIENTE_REVISION"},
    "PENDIENTE_REVISION": {"PENDIENTE_RESPUESTA_WIN", "OBSERVADO", "APROBADO"},
    "OBSERVADO": {"EN_EJECUCION"},
    "APROBADO": {"LIQUIDADO"},
}


def _project_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "property_id": str(row.property_id),
        "parent_project_id": str(row.parent_project_id) if row.parent_project_id else None,
        "network_group_id": str(row.network_group_id) if row.network_group_id else None,
        "project_scope": row.project_scope,
        "external_property_id": row.external_property_id,
        "project_code": row.project_code,
        "project_type": row.project_type,
        "name": row.name,
        "priority": row.priority,
        "manager_id": str(row.manager_id) if row.manager_id else None,
        "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
        "contractor_id": str(row.contractor_id) if row.contractor_id else None,
        "subcontractor_id": str(row.subcontractor_id) if row.subcontractor_id else None,
        "crew_id": str(row.crew_id) if row.crew_id else None,
        "technician_id": str(row.technician_id) if row.technician_id else None,
        "scheduled_date": row.scheduled_date,
        "current_status": row.current_status,
        "last_from_status": getattr(row, "last_from_status", None),
        "status_version": row.status_version,
    }


def _select_project_sql() -> str:
    return """
        SELECT p.id, p.property_id, pr.external_property_id, p.project_code, p.project_type,
               p.parent_project_id, p.network_group_id, p.project_scope,
               p.name, p.priority, p.manager_id, p.supervisor_id, p.contractor_id,
               p.subcontractor_id, p.crew_id, p.technician_id, p.scheduled_date, p.current_status,
               p.status_version, last_history.from_status AS last_from_status
        FROM projects p
        JOIN properties pr ON pr.id = p.property_id
        LEFT JOIN LATERAL (
            SELECT h.from_status
            FROM project_status_history h
            WHERE h.project_id = p.id
            ORDER BY h.changed_at DESC
            LIMIT 1
        ) last_history ON TRUE
    """


def list_projects(
    db: Session,
    current_status: str | None = None,
    project_type: str | None = None,
    crew_id: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if current_status:
        conditions.append("p.current_status = :current_status")
        params["current_status"] = current_status
    if project_type:
        conditions.append("p.project_type = :project_type")
        params["project_type"] = project_type
    if crew_id:
        conditions.append("p.crew_id = CAST(:crew_id AS uuid)")
        params["crew_id"] = crew_id
    if search:
        conditions.append("(p.project_code ILIKE :search OR p.name ILIKE :search OR pr.external_property_id ILIKE :search)")
        params["search"] = f"%{search}%"

    where_clause = " AND ".join(conditions)
    total = db.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM projects p
            JOIN properties pr ON pr.id = p.property_id
            WHERE {where_clause}
            """
        ),
        params,
    ).scalar_one()
    rows = db.execute(
        text(
            f"""
            {_select_project_sql()}
            WHERE {where_clause}
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).all()
    return {"items": [_project_dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def get_project(db: Session, project_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            f"""
            {_select_project_sql()}
            WHERE p.id = CAST(:project_id AS uuid)
            """
        ),
        {"project_id": project_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _project_dict(row)


def _property_exists(db: Session, property_id: str) -> bool:
    return bool(
        db.execute(
            text("SELECT 1 FROM properties WHERE id = CAST(:property_id AS uuid)"),
            {"property_id": property_id},
        ).first()
    )


def create_project(db: Session, payload: ProjectCreateRequest, user_id: str) -> dict[str, Any]:
    if not _property_exists(db, payload.property_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid property_id")
    try:
        row = db.execute(
            text(
                """
                INSERT INTO projects (
                    property_id, parent_project_id, network_group_id, project_scope,
                    project_code, project_type, name, priority, manager_id,
                    supervisor_id, contractor_id, subcontractor_id, crew_id, technician_id, scheduled_date, current_status
                )
                VALUES (
                    CAST(:property_id AS uuid), CAST(:parent_project_id AS uuid), CAST(:network_group_id AS uuid), :project_scope,
                    :project_code, :project_type, :name, :priority, CAST(:manager_id AS uuid),
                    CAST(:supervisor_id AS uuid), CAST(:contractor_id AS uuid), CAST(:subcontractor_id AS uuid),
                    CAST(:crew_id AS uuid), CAST(:technician_id AS uuid), :scheduled_date, 'PREDIO_REGISTRADO'
                )
                RETURNING id
                """
            ),
            {**payload.model_dump(), "manager_id": user_id},
        ).first()
        db.execute(
            text(
                """
                INSERT INTO project_status_history (project_id, from_status, to_status, changed_by, reason)
                VALUES (:project_id, NULL, 'PREDIO_REGISTRADO', CAST(:user_id AS uuid), 'Proyecto creado')
                """
            ),
            {"project_id": row.id, "user_id": user_id},
        )
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project code already exists or invalid relation")
    return get_project(db, str(row.id))


def update_project(db: Session, project_id: str, payload: ProjectUpdateRequest) -> dict[str, Any]:
    get_project(db, project_id)
    db.execute(
        text(
            """
            UPDATE projects
            SET
                name = COALESCE(:name, name),
                parent_project_id = CASE WHEN :parent_project_id_set THEN CAST(:parent_project_id AS uuid) ELSE parent_project_id END,
                network_group_id = CASE WHEN :network_group_id_set THEN CAST(:network_group_id AS uuid) ELSE network_group_id END,
                project_scope = COALESCE(:project_scope, project_scope),
                priority = COALESCE(:priority, priority),
                supervisor_id = CASE WHEN :supervisor_id_set THEN CAST(:supervisor_id AS uuid) ELSE supervisor_id END,
                contractor_id = CASE WHEN :contractor_id_set THEN CAST(:contractor_id AS uuid) ELSE contractor_id END,
                subcontractor_id = CASE WHEN :subcontractor_id_set THEN CAST(:subcontractor_id AS uuid) ELSE subcontractor_id END,
                crew_id = CASE WHEN :crew_id_set THEN CAST(:crew_id AS uuid) ELSE crew_id END,
                technician_id = CASE WHEN :technician_id_set THEN CAST(:technician_id AS uuid) ELSE technician_id END,
                scheduled_date = CASE WHEN :scheduled_date_set THEN :scheduled_date ELSE scheduled_date END,
                updated_at = now()
            WHERE id = CAST(:project_id AS uuid)
            """
        ),
        {
            **payload.model_dump(),
            "project_id": project_id,
            "parent_project_id_set": "parent_project_id" in payload.model_fields_set,
            "network_group_id_set": "network_group_id" in payload.model_fields_set,
            "supervisor_id_set": "supervisor_id" in payload.model_fields_set,
            "contractor_id_set": "contractor_id" in payload.model_fields_set,
            "subcontractor_id_set": "subcontractor_id" in payload.model_fields_set,
            "crew_id_set": "crew_id" in payload.model_fields_set,
            "technician_id_set": "technician_id" in payload.model_fields_set,
            "scheduled_date_set": "scheduled_date" in payload.model_fields_set,
        },
    )
    db.commit()
    return get_project(db, project_id)


def assign_project(db: Session, project_id: str, payload: ProjectAssignRequest, user_id: str) -> dict[str, Any]:
    project = update_project(db, project_id, ProjectUpdateRequest(**payload.model_dump()))
    if project["current_status"] == "PREDIO_APROBADO":
        return transition_project(
            db,
            project_id,
            ProjectStatusTransitionRequest(to_status="ASIGNADO_A_CUADRILLA", reason="Asignacion operativa"),
            user_id,
        )
    return get_project(db, project_id)


def transition_project(db: Session, project_id: str, payload: ProjectStatusTransitionRequest, user_id: str) -> dict[str, Any]:
    if payload.to_status not in {status_item.value for status_item in ProjectStatus}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid to_status")
    project = get_project(db, project_id)
    from_status = project["current_status"]
    if payload.to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transition {from_status} -> {payload.to_status} is not allowed",
        )
    if (
        payload.to_status == "PENDIENTE_REVISION"
        and from_status != "FACTIBILIDAD_EN_REVISION"
        and project["project_type"] in {"PEXT", "MIXTO"}
    ):
        validation = validate_field_output(db, project_id)
        if not validation["is_complete"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Project field output is incomplete",
                    "blocking_errors": validation["blocking_errors"],
                    "warnings": validation["warnings"],
                },
            )

    db.execute(
        text(
            """
            UPDATE projects
            SET current_status = :to_status, status_version = status_version + 1, updated_at = now()
            WHERE id = CAST(:project_id AS uuid)
            """
        ),
        {"project_id": project_id, "to_status": payload.to_status},
    )
    db.execute(
        text(
            """
            INSERT INTO project_status_history (project_id, from_status, to_status, changed_by, reason)
            VALUES (CAST(:project_id AS uuid), :from_status, :to_status, CAST(:user_id AS uuid), :reason)
            """
        ),
        {
            "project_id": project_id,
            "from_status": from_status,
            "to_status": payload.to_status,
            "user_id": user_id,
            "reason": payload.reason,
        },
    )
    db.commit()
    return get_project(db, project_id)
