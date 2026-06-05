import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.domain import EvidenceCategory
from app.core.storage import internal_storage_client
from app.modules.evidences.schemas import EvidenceCreateRequest

MAX_GPS_ACCURACY_M = 50


def _evidence_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "project_id": str(row.project_id),
        "captured_by": str(row.captured_by) if row.captured_by else None,
        "category": row.category,
        "subcategory": row.subcategory,
        "associated_code": row.associated_code,
        "element_type": row.element_type,
        "pext_prefeasibility_id": str(row.pext_prefeasibility_id) if row.pext_prefeasibility_id else None,
        "splice_chart_id": str(row.splice_chart_id) if row.splice_chart_id else None,
        "splice_entry_id": str(row.splice_entry_id) if row.splice_entry_id else None,
        "local_client_uuid": str(row.local_client_uuid),
        "captured_at": row.captured_at,
        "received_at": row.received_at,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "gps_accuracy_m": row.gps_accuracy_m,
        "gps_provider": row.gps_provider,
        "gps_validated": row.gps_validated,
        "file_id": str(row.file_id) if row.file_id else None,
        "thumbnail_file_id": str(row.thumbnail_file_id) if row.thumbnail_file_id else None,
        "checksum_sha256": row.checksum_sha256,
        "validation_status": row.validation_status,
        "metadata": row.metadata,
    }


def _validate_category(category: str) -> None:
    if category not in {item.value for item in EvidenceCategory}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid evidence category")


def _gps_validated(accuracy: Any | None) -> bool:
    if accuracy is None:
        return False
    return float(accuracy) <= MAX_GPS_ACCURACY_M


def _base_select() -> str:
    return """
        SELECT id, project_id, captured_by, category, subcategory, associated_code, element_type,
               pext_prefeasibility_id, splice_chart_id, splice_entry_id, local_client_uuid,
               captured_at, received_at, latitude, longitude, gps_accuracy_m, gps_provider,
               gps_validated, file_id, thumbnail_file_id, checksum_sha256, validation_status, metadata
        FROM evidences
    """


def create_evidence(db: Session, payload: EvidenceCreateRequest, user_id: str) -> dict[str, Any]:
    _validate_category(payload.category)
    values = payload.model_dump()
    values["metadata"] = json.dumps(values["metadata"])
    values["gps_validated"] = _gps_validated(payload.gps_accuracy_m)

    try:
        row = db.execute(
            text(
                """
                INSERT INTO evidences (
                    project_id, captured_by, category, subcategory, associated_code, element_type,
                    pext_prefeasibility_id, splice_chart_id, splice_entry_id, local_client_uuid,
                    captured_at, location, latitude, longitude, gps_accuracy_m, gps_provider,
                    gps_validated, device_id, checksum_sha256, metadata
                )
                VALUES (
                    CAST(:project_id AS uuid), CAST(:user_id AS uuid), :category, :subcategory,
                    :associated_code, :element_type, CAST(:pext_prefeasibility_id AS uuid),
                    CAST(:splice_chart_id AS uuid), CAST(:splice_entry_id AS uuid),
                    CAST(:local_client_uuid AS uuid), :captured_at,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                    :latitude, :longitude, :gps_accuracy_m, :gps_provider, :gps_validated,
                    CAST(:device_id AS uuid), :checksum_sha256, CAST(:metadata AS jsonb)
                )
                ON CONFLICT (project_id, local_client_uuid)
                DO UPDATE SET
                    received_at = now(),
                    checksum_sha256 = EXCLUDED.checksum_sha256,
                    metadata = EXCLUDED.metadata
                RETURNING id
                """
            ),
            {"user_id": user_id, **values},
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid evidence relation or duplicate data")
    return get_evidence(db, str(row.id))


def get_evidence(db: Session, evidence_id: str) -> dict[str, Any]:
    row = db.execute(
        text(f"{_base_select()} WHERE id = CAST(:evidence_id AS uuid)"),
        {"evidence_id": evidence_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return _evidence_dict(row)


def list_project_evidences(
    db: Session,
    project_id: str,
    category: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {"project_id": project_id, "limit": limit, "offset": offset}
    conditions = ["project_id = CAST(:project_id AS uuid)"]
    if category:
        _validate_category(category)
        conditions.append("category = :category")
        params["category"] = category

    where_clause = " AND ".join(conditions)
    total = db.execute(text(f"SELECT COUNT(*) FROM evidences WHERE {where_clause}"), params).scalar_one()
    rows = db.execute(
        text(
            f"""
            {_base_select()}
            WHERE {where_clause}
            ORDER BY captured_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).all()
    return {"items": [_evidence_dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def delete_evidence(db: Session, evidence_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT e.id, e.file_id, f.bucket, f.object_key
            FROM evidences e
            LEFT JOIN files f ON f.id = e.file_id
            WHERE e.id = CAST(:evidence_id AS uuid)
            """
        ),
        {"evidence_id": evidence_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    if row.bucket and row.object_key:
        try:
            internal_storage_client().delete_object(Bucket=row.bucket, Key=row.object_key)
        except Exception:
            pass

    db.execute(text("DELETE FROM evidences WHERE id = CAST(:evidence_id AS uuid)"), {"evidence_id": evidence_id})
    if row.file_id:
        db.execute(text("DELETE FROM files WHERE id = :file_id"), {"file_id": row.file_id})
    db.commit()
    return {"deleted": True, "id": evidence_id}
