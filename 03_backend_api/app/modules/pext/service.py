import json
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.pext.schemas import (
    PextExecutionPackageCreateRequest,
    PextPrefeasibilityUpsertRequest,
    SpliceChartCreateRequest,
    SpliceChartUpdateRequest,
    SpliceEntryCreateRequest,
)

PREFEASIBILITY_SCALAR_FIELDS = [
    "building_name",
    "condominium_name",
    "project_type_option",
    "project_subtype",
    "source_origin",
    "classification",
    "construction_type",
    "owner_delivery_date",
    "riser_completion_date",
    "authorized_access_type",
    "has_owners_board",
    "auth_letter_contact_role",
    "auth_letter_contact_name",
    "auth_letter_contact_phone",
    "auth_letter_contact_email",
    "access_contact_role",
    "access_contact_name",
    "access_contact_phone",
    "access_contact_email",
    "technical_visit_date",
    "visit_time_range",
    "department",
    "province",
    "district",
    "urbanization",
    "postal_code",
    "street_type",
    "street_name",
    "address_detail",
    "coordinates_text",
    "total_towers",
    "total_homes",
    "channel_agency",
    "whatsapp_group_required",
    "gca_manager_name",
    "gca_manager_phone",
    "gca_supervisor_name",
    "gca_supervisor_phone",
    "visit_date",
    "contact_name",
    "contact_phone",
    "address_confirmed",
    "building_type",
    "access_type",
    "tower_count",
    "floor_count",
    "riser_count",
    "hp_count",
    "existing_fo",
    "nearest_node_code",
    "distance_to_node_m",
    "feeder_mufa_code",
    "requires_oc",
    "oc_distance_m",
    "canalization_type",
    "poles_required",
    "nap_required_count",
    "splitter_required",
    "estimated_power_dbm",
    "latitude",
    "longitude",
    "gps_accuracy_m",
    "feasibility_result",
    "risks",
    "restrictions",
    "observations",
    "metadata",
]

REQUIRED_PREFEASIBILITY_FIELDS = {
    "building_name": "Nombre del edificio",
    "project_type_option": "Tipo de proyecto",
    "classification": "Clasificacion",
    "authorized_access_type": "Acceso autorizado",
    "technical_visit_date": "Fecha visita tecnica",
    "visit_time_range": "Rango visita",
    "department": "Departamento",
    "province": "Provincia",
    "district": "Distrito",
    "street_name": "Nombre via",
    "address_detail": "Mz / lote / numero",
    "latitude": "Latitud GPS",
    "longitude": "Longitud GPS",
    "gps_accuracy_m": "Precision GPS",
    "total_towers": "Total torres",
    "total_homes": "Total hogares",
    "feasibility_result": "Resultado",
}

REQUIRED_EVIDENCE_COUNTS = {
    "CHARLA_5_MIN": 1,
    "ATS": 1,
    "FACHADA": 1,
    "INGRESO_COMUN": 1,
    "LATERAL_DERECHA": 1,
    "LATERAL_IZQUIERDA": 1,
    "NODO": 1,
    "MUFA": 1,
    "NAP": 1,
}

EXECUTION_BASE_ALLOWED_STATUSES = {
    "PREDIO_APROBADO",
    "ASIGNADO_A_CUADRILLA",
    "EN_EJECUCION",
    "PENDIENTE_REVISION",
    "OBSERVADO",
    "APROBADO",
    "LIQUIDADO",
}


def _point_expr(latitude: Decimal | None, longitude: Decimal | None) -> str:
    if latitude is None or longitude is None:
        return "NULL"
    return "ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)"


def _ensure_pext_project(db: Session, project_id: str) -> None:
    row = db.execute(
        text("SELECT 1 FROM projects WHERE id = CAST(:project_id AS uuid) AND project_type IN ('PEXT', 'MIXTO')"),
        {"project_id": project_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PEXT project not found")


def _prefeasibility_dict(row: Any) -> dict[str, Any]:
    payload = {
        "id": str(row.id),
        "project_id": str(row.project_id),
        "evaluated_by": str(row.evaluated_by) if row.evaluated_by else None,
    }
    mapping = row._mapping
    for field in PREFEASIBILITY_SCALAR_FIELDS:
        payload[field] = mapping[field]
    return payload


def _list_prefeasibility_towers(db: Session, prefeasibility_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT tower_label, floors, homes
            FROM pext_prefeasibility_towers
            WHERE prefeasibility_id = CAST(:prefeasibility_id AS uuid)
            ORDER BY tower_label
            """
        ),
        {"prefeasibility_id": prefeasibility_id},
    ).all()
    return [{"tower_label": row.tower_label, "floors": row.floors, "homes": row.homes} for row in rows]


def _list_prefeasibility_tower_contacts(db: Session, prefeasibility_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT tower_label, role, full_name, phone, apartment_or_department, interested_clients
            FROM pext_prefeasibility_tower_contacts
            WHERE prefeasibility_id = CAST(:prefeasibility_id AS uuid)
            ORDER BY tower_label, created_at
            """
        ),
        {"prefeasibility_id": prefeasibility_id},
    ).all()
    return [
        {
            "tower_label": row.tower_label,
            "role": row.role,
            "full_name": row.full_name,
            "phone": row.phone,
            "apartment_or_department": row.apartment_or_department,
            "interested_clients": row.interested_clients,
        }
        for row in rows
    ]


def get_prefeasibility(db: Session, project_id: str) -> dict[str, Any]:
    _ensure_pext_project(db, project_id)
    row = db.execute(
        text(
            """
            SELECT *
            FROM pext_prefeasibility_forms
            WHERE project_id = CAST(:project_id AS uuid)
            """
        ),
        {"project_id": project_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefeasibility form not found")
    payload = _prefeasibility_dict(row)
    payload["towers"] = _list_prefeasibility_towers(db, payload["id"])
    payload["tower_contacts"] = _list_prefeasibility_tower_contacts(db, payload["id"])
    return payload


def upsert_prefeasibility(
    db: Session,
    project_id: str,
    user_id: str,
    payload: PextPrefeasibilityUpsertRequest,
) -> dict[str, Any]:
    _ensure_pext_project(db, project_id)
    point_expr = _point_expr(payload.latitude, payload.longitude)
    values = payload.model_dump()
    towers = values.pop("towers")
    tower_contacts = values.pop("tower_contacts")
    values["metadata"] = json.dumps(values["metadata"])
    insert_columns = ", ".join(PREFEASIBILITY_SCALAR_FIELDS)
    insert_values = ", ".join(
        "CAST(:metadata AS jsonb)" if field == "metadata" else f":{field}" for field in PREFEASIBILITY_SCALAR_FIELDS
    )
    update_values = ",\n                ".join(
        f"{field} = EXCLUDED.{field}" for field in PREFEASIBILITY_SCALAR_FIELDS if field != "metadata"
    )
    db.execute(
        text(
            f"""
            INSERT INTO pext_prefeasibility_forms (
                project_id, evaluated_by, {insert_columns}, location
            )
            VALUES (
                CAST(:project_id AS uuid), CAST(:user_id AS uuid), {insert_values}, {point_expr}
            )
            ON CONFLICT (project_id)
            DO UPDATE SET
                evaluated_by = EXCLUDED.evaluated_by,
                {update_values},
                metadata = EXCLUDED.metadata,
                location = EXCLUDED.location,
                updated_at = now()
            RETURNING id
            """
        ),
        {"project_id": project_id, "user_id": user_id, **values},
    ).first()
    form_id = db.execute(
        text("SELECT id FROM pext_prefeasibility_forms WHERE project_id = CAST(:project_id AS uuid)"),
        {"project_id": project_id},
    ).scalar_one()
    db.execute(
        text("DELETE FROM pext_prefeasibility_tower_contacts WHERE prefeasibility_id = CAST(:form_id AS uuid)"),
        {"form_id": str(form_id)},
    )
    db.execute(
        text("DELETE FROM pext_prefeasibility_towers WHERE prefeasibility_id = CAST(:form_id AS uuid)"),
        {"form_id": str(form_id)},
    )
    for tower in towers:
        db.execute(
            text(
                """
                INSERT INTO pext_prefeasibility_towers (prefeasibility_id, tower_label, floors, homes)
                VALUES (CAST(:form_id AS uuid), :tower_label, :floors, :homes)
                """
            ),
            {"form_id": str(form_id), **tower},
        )
    for contact in tower_contacts:
        db.execute(
            text(
                """
                INSERT INTO pext_prefeasibility_tower_contacts (
                    prefeasibility_id, tower_label, role, full_name, phone, apartment_or_department, interested_clients
                )
                VALUES (
                    CAST(:form_id AS uuid), :tower_label, :role, :full_name, :phone, :apartment_or_department, :interested_clients
                )
                """
            ),
            {"form_id": str(form_id), **contact},
        )
    db.commit()
    return get_prefeasibility(db, project_id)


def _entry_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "chart_id": str(row.chart_id),
        "sequence_number": row.sequence_number,
        "tray": row.tray,
        "tube_color": row.tube_color,
        "fiber_in_number": row.fiber_in_number,
        "fiber_in_color": row.fiber_in_color,
        "fiber_out_number": row.fiber_out_number,
        "fiber_out_color": row.fiber_out_color,
        "service_type": row.service_type,
        "nap_code": row.nap_code,
        "destination": row.destination,
        "signal_dbm": row.signal_dbm,
        "observations": row.observations,
    }


def _chart_dict(row: Any, entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "project_id": str(row.project_id),
        "mufa_code": row.mufa_code,
        "mufa_type": row.mufa_type,
        "node_code": row.node_code,
        "cable_in": row.cable_in,
        "cable_out": row.cable_out,
        "fiber_capacity": row.fiber_capacity,
        "prepared_by": str(row.prepared_by) if row.prepared_by else None,
        "status": row.status,
        "observations": row.observations,
        "metadata": row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}"),
        "entries": entries,
    }


def list_splice_charts(db: Session, project_id: str) -> list[dict[str, Any]]:
    _ensure_pext_project(db, project_id)
    rows = db.execute(
        text("SELECT * FROM pext_splice_charts WHERE project_id = CAST(:project_id AS uuid) ORDER BY created_at DESC"),
        {"project_id": project_id},
    ).all()
    return [get_splice_chart(db, str(row.id)) for row in rows]


def get_splice_chart(db: Session, chart_id: str) -> dict[str, Any]:
    chart = db.execute(
        text("SELECT * FROM pext_splice_charts WHERE id = CAST(:chart_id AS uuid)"),
        {"chart_id": chart_id},
    ).first()
    if chart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Splice chart not found")
    entries = db.execute(
        text("SELECT * FROM pext_splice_chart_entries WHERE chart_id = CAST(:chart_id AS uuid) ORDER BY sequence_number"),
        {"chart_id": chart_id},
    ).all()
    return _chart_dict(chart, [_entry_dict(row) for row in entries])


def create_splice_chart(db: Session, project_id: str, user_id: str, payload: SpliceChartCreateRequest) -> dict[str, Any]:
    _ensure_pext_project(db, project_id)
    row = db.execute(
        text(
            """
            INSERT INTO pext_splice_charts (
                project_id, mufa_code, mufa_type, node_code, cable_in, cable_out,
                fiber_capacity, prepared_by, observations, metadata
            )
            VALUES (
                CAST(:project_id AS uuid), :mufa_code, :mufa_type, :node_code, :cable_in, :cable_out,
                :fiber_capacity, CAST(:user_id AS uuid), :observations, CAST(:metadata AS jsonb)
            )
            RETURNING id
            """
        ),
        {"project_id": project_id, "user_id": user_id, **payload.model_dump(), "metadata": json.dumps(payload.metadata)},
    ).first()
    db.commit()
    return get_splice_chart(db, str(row.id))


def update_splice_chart(db: Session, chart_id: str, payload: SpliceChartUpdateRequest) -> dict[str, Any]:
    get_splice_chart(db, chart_id)
    db.execute(
        text(
            """
            UPDATE pext_splice_charts
            SET
                mufa_code = COALESCE(:mufa_code, mufa_code),
                mufa_type = COALESCE(:mufa_type, mufa_type),
                node_code = CASE WHEN :node_code_set THEN :node_code ELSE node_code END,
                cable_in = CASE WHEN :cable_in_set THEN :cable_in ELSE cable_in END,
                cable_out = CASE WHEN :cable_out_set THEN :cable_out ELSE cable_out END,
                fiber_capacity = CASE WHEN :fiber_capacity_set THEN :fiber_capacity ELSE fiber_capacity END,
                status = COALESCE(:status, status),
                observations = CASE WHEN :observations_set THEN :observations ELSE observations END,
                metadata = CASE WHEN :metadata_set THEN CAST(:metadata AS jsonb) ELSE metadata END,
                updated_at = now()
            WHERE id = CAST(:chart_id AS uuid)
            """
        ),
        {
            "chart_id": chart_id,
            **payload.model_dump(),
            "metadata": json.dumps(payload.metadata or {}),
            "node_code_set": "node_code" in payload.model_fields_set,
            "cable_in_set": "cable_in" in payload.model_fields_set,
            "cable_out_set": "cable_out" in payload.model_fields_set,
            "fiber_capacity_set": "fiber_capacity" in payload.model_fields_set,
            "observations_set": "observations" in payload.model_fields_set,
            "metadata_set": "metadata" in payload.model_fields_set,
        },
    )
    db.commit()
    return get_splice_chart(db, chart_id)


def add_splice_entry(db: Session, chart_id: str, payload: SpliceEntryCreateRequest) -> dict[str, Any]:
    get_splice_chart(db, chart_id)
    row = db.execute(
        text(
            """
            INSERT INTO pext_splice_chart_entries (
                chart_id, sequence_number, tray, tube_color, fiber_in_number, fiber_in_color,
                fiber_out_number, fiber_out_color, service_type, nap_code, destination, signal_dbm, observations
            )
            VALUES (
                CAST(:chart_id AS uuid), :sequence_number, :tray, :tube_color, :fiber_in_number,
                :fiber_in_color, :fiber_out_number, :fiber_out_color, :service_type, :nap_code,
                :destination, :signal_dbm, :observations
            )
            ON CONFLICT (chart_id, sequence_number)
            DO UPDATE SET
                tray = EXCLUDED.tray,
                tube_color = EXCLUDED.tube_color,
                fiber_in_number = EXCLUDED.fiber_in_number,
                fiber_in_color = EXCLUDED.fiber_in_color,
                fiber_out_number = EXCLUDED.fiber_out_number,
                fiber_out_color = EXCLUDED.fiber_out_color,
                service_type = EXCLUDED.service_type,
                nap_code = EXCLUDED.nap_code,
                destination = EXCLUDED.destination,
                signal_dbm = EXCLUDED.signal_dbm,
                observations = EXCLUDED.observations
            RETURNING id
            """
        ),
        {"chart_id": chart_id, **payload.model_dump()},
    ).first()
    db.commit()
    chart = get_splice_chart(db, chart_id)
    return next(entry for entry in chart["entries"] if entry["id"] == str(row.id))


def _project_output(db: Session, project_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    row = db.execute(
        text(
            """
            SELECT p.id, p.project_code, p.project_type, p.name, p.priority, p.current_status,
                   p.technician_id, p.crew_id, p.contractor_id, p.supervisor_id,
                   pr.id AS property_id, pr.external_property_id, pr.address, pr.district,
                   pr.province, pr.region, pr.node_code, pr.latitude, pr.longitude
            FROM projects p
            JOIN properties pr ON pr.id = p.property_id
            WHERE p.id = CAST(:project_id AS uuid)
              AND p.project_type IN ('PEXT', 'MIXTO')
            """
        ),
        {"project_id": project_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PEXT project not found")
    project = {
        "id": str(row.id),
        "project_code": row.project_code,
        "project_type": row.project_type,
        "name": row.name,
        "priority": row.priority,
        "current_status": row.current_status,
        "technician_id": str(row.technician_id) if row.technician_id else None,
        "crew_id": str(row.crew_id) if row.crew_id else None,
        "contractor_id": str(row.contractor_id) if row.contractor_id else None,
        "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
    }
    property_payload = {
        "id": str(row.property_id),
        "external_property_id": row.external_property_id,
        "address": row.address,
        "district": row.district,
        "province": row.province,
        "region": row.region,
        "node_code": row.node_code,
        "latitude": row.latitude,
        "longitude": row.longitude,
    }
    return project, property_payload


def _list_output_evidences(db: Session, project_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT e.id, e.category, e.subcategory, e.associated_code, e.element_type,
                   e.local_client_uuid, e.captured_at, e.received_at, e.latitude, e.longitude,
                   e.gps_accuracy_m, e.gps_provider, e.gps_validated, e.validation_status,
                   e.checksum_sha256, e.file_id, f.object_key, f.original_filename, f.mime_type, f.size_bytes
            FROM evidences e
            LEFT JOIN files f ON f.id = e.file_id
            WHERE e.project_id = CAST(:project_id AS uuid)
            ORDER BY e.captured_at ASC
            """
        ),
        {"project_id": project_id},
    ).all()
    return [
        {
            "id": str(row.id),
            "category": row.category,
            "subcategory": row.subcategory,
            "associated_code": row.associated_code,
            "element_type": row.element_type,
            "local_client_uuid": str(row.local_client_uuid),
            "captured_at": row.captured_at,
            "received_at": row.received_at,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "gps_accuracy_m": row.gps_accuracy_m,
            "gps_provider": row.gps_provider,
            "gps_validated": row.gps_validated,
            "validation_status": row.validation_status,
            "checksum_sha256": row.checksum_sha256,
            "file": {
                "id": str(row.file_id) if row.file_id else None,
                "object_key": row.object_key,
                "original_filename": row.original_filename,
                "mime_type": row.mime_type,
                "size_bytes": row.size_bytes,
            }
            if row.file_id
            else None,
        }
        for row in rows
    ]


def get_field_output(db: Session, project_id: str) -> dict[str, Any]:
    project, property_payload = _project_output(db, project_id)
    try:
        prefeasibility = get_prefeasibility(db, project_id)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
        prefeasibility = None
    splice_charts = list_splice_charts(db, project_id)
    evidences = _list_output_evidences(db, project_id)
    evidence_counts: dict[str, int] = {}
    for evidence in evidences:
        evidence_counts[evidence["category"]] = evidence_counts.get(evidence["category"], 0) + 1
    validation = validate_field_output_payload(prefeasibility, splice_charts, evidences)
    return {
        "project": project,
        "property": property_payload,
        "prefeasibility": prefeasibility,
        "splice_charts": splice_charts,
        "evidences": evidences,
        "summary": {
            "has_prefeasibility": prefeasibility is not None,
            "is_complete": validation["is_complete"],
            "blocking_error_count": len(validation["blocking_errors"]),
            "warning_count": len(validation["warnings"]),
            "splice_chart_count": len(splice_charts),
            "splice_entry_count": sum(len(chart["entries"]) for chart in splice_charts),
            "evidence_count": len(evidences),
            "evidence_counts": evidence_counts,
            "uploaded_evidence_count": sum(1 for evidence in evidences if evidence["file"] is not None),
            "gps_validated_count": sum(1 for evidence in evidences if evidence["gps_validated"]),
        },
    }


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


def validate_field_output_payload(
    prefeasibility: dict[str, Any] | None,
    splice_charts: list[dict[str, Any]],
    evidences: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if prefeasibility is None:
        errors.append("No existe ficha de prefactibilidad PEXT")
    else:
        for field, label in REQUIRED_PREFEASIBILITY_FIELDS.items():
            if _missing(prefeasibility.get(field)):
                errors.append(f"Prefactibilidad: falta {label}")
        if not prefeasibility.get("towers"):
            errors.append("Prefactibilidad: falta detalle de torres")
        tower_contacts = prefeasibility.get("tower_contacts") if isinstance(prefeasibility.get("tower_contacts"), list) else []
        has_contact_name = bool(
            prefeasibility.get("access_contact_name")
            or prefeasibility.get("auth_letter_contact_name")
            or any(contact.get("full_name") for contact in tower_contacts if isinstance(contact, dict))
        )
        has_contact_phone = bool(
            prefeasibility.get("access_contact_phone")
            or prefeasibility.get("auth_letter_contact_phone")
            or any(contact.get("phone") for contact in tower_contacts if isinstance(contact, dict))
        )
        if not tower_contacts:
            warnings.append("Prefactibilidad: no se registraron responsables por torre")
        if not has_contact_name:
            warnings.append("Prefactibilidad: no se registro nombre de contacto de acceso")
        if not has_contact_phone:
            warnings.append("Prefactibilidad: no se registro celular de contacto de acceso")

    if not splice_charts:
        errors.append("Cuadro de empalme: falta registrar al menos una MUFA")
    for chart in splice_charts:
        metadata = chart.get("metadata") if isinstance(chart.get("metadata"), dict) else {}
        mufa_rows = metadata.get("mufas") if isinstance(metadata, dict) else None
        if not chart.get("entries") and not (isinstance(mufa_rows, list) and mufa_rows):
            errors.append(f"Cuadro de empalme: MUFA {chart.get('mufa_code')} no tiene detalle de MUFA")

    evidence_counts: dict[str, int] = {}
    for evidence in evidences:
        evidence_counts[evidence["category"]] = evidence_counts.get(evidence["category"], 0) + 1
        if not evidence.get("gps_validated"):
            warnings.append(f"Evidencia {evidence['category']}: GPS no validado")
        if evidence.get("file") is None:
            errors.append(f"Evidencia {evidence['category']}: falta archivo/foto asociada")

    required_evidence_counts = dict(REQUIRED_EVIDENCE_COUNTS)
    last_metadata = splice_charts[0].get("metadata") if splice_charts and isinstance(splice_charts[0].get("metadata"), dict) else {}
    jumpear = str(last_metadata.get("jumpear") or "").strip().upper() if isinstance(last_metadata, dict) else ""
    if jumpear == "NO":
        required_evidence_counts.pop("NODO", None)

    for category, required_count in required_evidence_counts.items():
        actual_count = evidence_counts.get(category, 0)
        if actual_count < required_count:
            errors.append(f"Evidencia {category}: falta {required_count - actual_count}")

    return {
        "is_complete": not errors,
        "blocking_errors": errors,
        "warnings": warnings,
        "required_evidence_counts": required_evidence_counts,
        "actual_evidence_counts": evidence_counts,
    }


def validate_field_output(db: Session, project_id: str) -> dict[str, Any]:
    output = get_field_output(db, project_id)
    return validate_field_output_payload(output["prefeasibility"], output["splice_charts"], output["evidences"])


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _execution_package_dict(row: Any) -> dict[str, Any]:
    snapshot = row.snapshot
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    return {
        "id": str(row.id),
        "project_id": str(row.project_id),
        "package_stage": row.package_stage,
        "version_number": row.version_number,
        "source_package_id": str(row.source_package_id) if row.source_package_id else None,
        "project_status": row.project_status,
        "snapshot": snapshot,
        "change_reason": row.change_reason,
        "created_by": str(row.created_by) if row.created_by else None,
        "is_current": row.is_current,
        "created_at": row.created_at,
    }


def get_current_execution_package(
    db: Session,
    project_id: str,
    package_stage: str | None = None,
) -> dict[str, Any]:
    _ensure_pext_project(db, project_id)
    params: dict[str, Any] = {"project_id": project_id}
    stage_clause = ""
    if package_stage:
        stage_clause = "AND package_stage = :package_stage"
        params["package_stage"] = package_stage
    row = db.execute(
        text(
            f"""
            SELECT *
            FROM pext_execution_packages
            WHERE project_id = CAST(:project_id AS uuid)
              AND is_current = true
              {stage_clause}
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        params,
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution package not found")
    return _execution_package_dict(row)


def create_execution_package(
    db: Session,
    project_id: str,
    user_id: str,
    payload: PextExecutionPackageCreateRequest,
) -> dict[str, Any]:
    output = get_field_output(db, project_id)
    project_status = output["project"]["current_status"]
    if payload.package_stage == "BASE_WIN_APROBADA" and project_status not in EXECUTION_BASE_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project status {project_status} cannot create BASE_WIN_APROBADA",
        )
    source_package: dict[str, Any] | None = None
    if payload.source_package_id:
        source_row = db.execute(
            text(
                """
                SELECT *
                FROM pext_execution_packages
                WHERE id = CAST(:source_package_id AS uuid)
                  AND project_id = CAST(:project_id AS uuid)
                """
            ),
            {"source_package_id": payload.source_package_id, "project_id": project_id},
        ).first()
        if source_row is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid source_package_id")
        source_package = _execution_package_dict(source_row)

    next_version = db.execute(
        text(
            """
            SELECT COALESCE(MAX(version_number), 0) + 1
            FROM pext_execution_packages
            WHERE project_id = CAST(:project_id AS uuid)
              AND package_stage = :package_stage
            """
        ),
        {"project_id": project_id, "package_stage": payload.package_stage},
    ).scalar_one()

    snapshot = {
        "package_stage": payload.package_stage,
        "source_package": source_package,
        "baseline": {
            "project": output["project"],
            "property": output["property"],
            "prefeasibility": output["prefeasibility"],
            "splice_charts": output["splice_charts"],
            "evidences": output["evidences"],
            "summary": output["summary"],
        },
        "execution_rules": {
            "prefeasibility_editable_in_execution": True,
            "ce_editable_in_execution": True,
            "changes_require_reason": True,
            "baseline_must_not_be_overwritten": True,
        },
    }

    db.execute(
        text(
            """
            UPDATE pext_execution_packages
            SET is_current = false
            WHERE project_id = CAST(:project_id AS uuid)
              AND package_stage = :package_stage
              AND is_current = true
            """
        ),
        {"project_id": project_id, "package_stage": payload.package_stage},
    )
    row = db.execute(
        text(
            """
            INSERT INTO pext_execution_packages (
                project_id, package_stage, version_number, source_package_id,
                project_status, snapshot, change_reason, created_by
            )
            VALUES (
                CAST(:project_id AS uuid), :package_stage, :version_number,
                CAST(:source_package_id AS uuid), :project_status,
                CAST(:snapshot AS jsonb), :change_reason, CAST(:user_id AS uuid)
            )
            RETURNING *
            """
        ),
        {
            "project_id": project_id,
            "package_stage": payload.package_stage,
            "version_number": next_version,
            "source_package_id": payload.source_package_id,
            "project_status": project_status,
            "snapshot": json.dumps(_json_ready(snapshot)),
            "change_reason": payload.change_reason,
            "user_id": user_id,
        },
    ).first()
    db.execute(
        text(
            """
            INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, new_values)
            VALUES (
                CAST(:user_id AS uuid), 'PEXT_EXECUTION_PACKAGE_CREATED',
                'pext_execution_packages', CAST(:package_id AS uuid), CAST(:new_values AS jsonb)
            )
            """
        ),
        {
            "user_id": user_id,
            "package_id": str(row.id),
            "new_values": json.dumps(
                {
                    "project_id": project_id,
                    "package_stage": payload.package_stage,
                    "version_number": next_version,
                    "project_status": project_status,
                }
            ),
        },
    )
    db.commit()
    return get_current_execution_package(db, project_id, payload.package_stage)
