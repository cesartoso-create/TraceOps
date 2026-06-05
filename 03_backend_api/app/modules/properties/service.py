from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.properties.schemas import PropertyCreateRequest, PropertyUpdateRequest


def _property_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "external_property_id": row.external_property_id,
        "source": row.source,
        "address": row.address,
        "district": row.district,
        "province": row.province,
        "region": row.region,
        "tower_count": row.tower_count,
        "riser_count": row.riser_count,
        "floor_count": row.floor_count,
        "hp_count": row.hp_count,
        "node_code": row.node_code,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "current_status": row.current_status,
    }


def _point_sql(latitude: Decimal | None, longitude: Decimal | None) -> str:
    if latitude is None or longitude is None:
        return "NULL"
    return "ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)"


def list_properties(
    db: Session,
    search: str | None = None,
    current_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions = ["1 = 1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if search:
        conditions.append("(external_property_id ILIKE :search OR address ILIKE :search OR node_code ILIKE :search)")
        params["search"] = f"%{search}%"
    if current_status:
        conditions.append("current_status = :current_status")
        params["current_status"] = current_status

    where_clause = " AND ".join(conditions)
    total = db.execute(text(f"SELECT COUNT(*) FROM properties WHERE {where_clause}"), params).scalar_one()
    rows = db.execute(
        text(
            f"""
            SELECT id, external_property_id, source, address, district, province, region,
                   tower_count, riser_count, floor_count, hp_count, node_code,
                   latitude, longitude, current_status
            FROM properties
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).all()
    return {"items": [_property_dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def get_property(db: Session, property_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT id, external_property_id, source, address, district, province, region,
                   tower_count, riser_count, floor_count, hp_count, node_code,
                   latitude, longitude, current_status
            FROM properties
            WHERE id = CAST(:property_id AS uuid)
            """
        ),
        {"property_id": property_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return _property_dict(row)


def create_property(db: Session, payload: PropertyCreateRequest, user_id: str) -> dict[str, Any]:
    point_expr = _point_sql(payload.latitude, payload.longitude)
    try:
        row = db.execute(
            text(
                f"""
                INSERT INTO properties (
                    external_property_id, source, address, district, province, region,
                    tower_count, riser_count, floor_count, hp_count, node_code,
                    location, latitude, longitude, received_at, registered_by, current_status
                )
                VALUES (
                    :external_property_id, :source, :address, :district, :province, :region,
                    :tower_count, :riser_count, :floor_count, :hp_count, :node_code,
                    {point_expr}, :latitude, :longitude, :received_at, CAST(:user_id AS uuid), 'PREDIO_REGISTRADO'
                )
                RETURNING id
                """
            ),
            {**payload.model_dump(), "user_id": user_id},
        ).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Property already exists")
    return get_property(db, str(row.id))


def update_property(db: Session, property_id: str, payload: PropertyUpdateRequest) -> dict[str, Any]:
    get_property(db, property_id)
    point_expr = _point_sql(payload.latitude, payload.longitude)
    db.execute(
        text(
            f"""
            UPDATE properties
            SET
                external_property_id = COALESCE(:external_property_id, external_property_id),
                address = COALESCE(:address, address),
                district = CASE WHEN :district_set THEN :district ELSE district END,
                province = CASE WHEN :province_set THEN :province ELSE province END,
                region = CASE WHEN :region_set THEN :region ELSE region END,
                tower_count = CASE WHEN :tower_count_set THEN :tower_count ELSE tower_count END,
                riser_count = CASE WHEN :riser_count_set THEN :riser_count ELSE riser_count END,
                floor_count = CASE WHEN :floor_count_set THEN :floor_count ELSE floor_count END,
                hp_count = CASE WHEN :hp_count_set THEN :hp_count ELSE hp_count END,
                node_code = CASE WHEN :node_code_set THEN :node_code ELSE node_code END,
                latitude = CASE WHEN :latitude_set THEN :latitude ELSE latitude END,
                longitude = CASE WHEN :longitude_set THEN :longitude ELSE longitude END,
                location = CASE WHEN :latitude_set AND :longitude_set THEN {point_expr} ELSE location END,
                current_status = COALESCE(:current_status, current_status),
                updated_at = now()
            WHERE id = CAST(:property_id AS uuid)
            """
        ),
        {
            **payload.model_dump(),
            "property_id": property_id,
            "district_set": "district" in payload.model_fields_set,
            "province_set": "province" in payload.model_fields_set,
            "region_set": "region" in payload.model_fields_set,
            "tower_count_set": "tower_count" in payload.model_fields_set,
            "riser_count_set": "riser_count" in payload.model_fields_set,
            "floor_count_set": "floor_count" in payload.model_fields_set,
            "hp_count_set": "hp_count" in payload.model_fields_set,
            "node_code_set": "node_code" in payload.model_fields_set,
            "latitude_set": "latitude" in payload.model_fields_set,
            "longitude_set": "longitude" in payload.model_fields_set,
        },
    )
    db.commit()
    return get_property(db, property_id)
