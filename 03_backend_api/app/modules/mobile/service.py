import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session


TECHNICIAN_ACTIVE_STATUSES = (
    "FACTIBILIDAD_EN_REVISION",
    "ASIGNADO_A_CUADRILLA",
    "EN_EJECUCION",
    "PENDIENTE_REVISION",
    "OBSERVADO",
)

PEXT_PREFEASIBILITY_VISIT_REQUIREMENTS = [
    {"code": "FACHADA", "label": "Fachada del predio", "required": True, "min_count": 1},
    {"code": "INGRESO_COMUN", "label": "Ingreso comun", "required": True, "min_count": 1},
    {"code": "LATERAL_DERECHA", "label": "Lateral derecha", "required": True, "min_count": 1},
    {"code": "LATERAL_IZQUIERDA", "label": "Lateral izquierda", "required": True, "min_count": 1},
]

PEXT_FIELD_REQUIREMENTS = [
    {"code": "CHARLA_5_MIN", "label": "CHARLA 5 MIN", "required": True, "min_count": 1},
    {"code": "ATS", "label": "ATS", "required": True, "min_count": 1},
    *PEXT_PREFEASIBILITY_VISIT_REQUIREMENTS,
    {"code": "NODO", "label": "Nodo / jumpeo", "required": True, "min_count": 1},
    {"code": "MUFA", "label": "Mufas nuevas o intervenidas", "required": True, "min_count": 1},
    {"code": "NAP", "label": "NAPs", "required": True, "min_count": 1},
    {"code": "RESERVA", "label": "Reservas", "required": False, "min_count": 0},
    {"code": "RECORRIDO_POSTE", "label": "Recorrido / postes", "required": False, "min_count": 0},
    {"code": "CUADRO_EMPALME", "label": "Cuadro de empalme", "required": True, "min_count": 1},
]

OC_FIELD_REQUIREMENTS = [
    {"code": "CHARLA_5_MIN", "label": "CHARLA 5 MIN", "required": True, "min_count": 1},
    {"code": "ATS", "label": "ATS", "required": True, "min_count": 1},
    {"code": "OC_MATERIAL", "label": "Materiales OC", "required": True, "min_count": 1},
    {"code": "OC_CANALIZACION", "label": "Canalizacion", "required": True, "min_count": 1},
    {"code": "OC_CAMARA", "label": "Camaras", "required": False, "min_count": 0},
    {"code": "OC_REPOSICION", "label": "Reposicion", "required": False, "min_count": 0},
]

PEXT_PREFEASIBILITY_FORM_SECTIONS = [
    {
        "code": "project_identification",
        "title": "Identificacion del predio",
        "fields": [
            {"key": "building_name", "label": "Nombre del edificio", "type": "text", "required": True, "max_length": 220},
            {"key": "condominium_name", "label": "Condominio", "type": "text", "max_length": 160},
            {
                "key": "project_type_option",
                "label": "Tipo de proyecto",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "NUEVO_PREDIO", "label": "Nuevo predio"},
                    {"value": "CORREDOR_VIAL", "label": "Corredor vial"},
                ],
            },
            {
                "key": "project_subtype",
                "label": "Subtipo de proyecto",
                "type": "select",
                "options": [
                    {"value": "AMPLIACION_DE_TORRE", "label": "Ampliacion de torre"},
                    {"value": "NUEVA_TORRE_ADMINISTRADOR", "label": "Nueva torre / administrador"},
                ],
            },
            {
                "key": "source_origin",
                "label": "Fuente u origen",
                "type": "select",
                "options": [
                    {"value": "PROPIO", "label": "Propio"},
                    {"value": "FARMING_GCA", "label": "Farming GCA"},
                ],
            },
            {
                "key": "classification",
                "label": "Clasificacion",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "EDIFICIO", "label": "Edificio"},
                    {"value": "CONDOMINIO", "label": "Condominio"},
                ],
            },
            {
                "key": "construction_type",
                "label": "Tipo de construccion",
                "type": "select",
                "options": [
                    {"value": "ESTRENO", "label": "Estreno"},
                    {"value": "MODERNO", "label": "Moderno"},
                    {"value": "ANTIGUO", "label": "Antiguo"},
                ],
            },
        ],
    },
    {
        "code": "access_and_contacts",
        "title": "Acceso",
        "fields": [
            {
                "key": "authorized_access_type",
                "label": "Acceso autorizado",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "AEREO", "label": "Aereo"},
                    {"value": "CANALIZADO", "label": "Canalizado"},
                    {"value": "CANAL_Y_POSTE", "label": "Canal y poste"},
                ],
            },
            {"key": "has_owners_board", "label": "Cuenta con junta", "type": "boolean"},
        ],
    },
    {
        "code": "visit_and_location",
        "title": "Visita tecnica y ubicacion",
        "fields": [
            {"key": "technical_visit_date", "label": "Fecha visita tecnica", "type": "date", "required": True},
            {
                "key": "visit_time_range",
                "label": "Rango visita",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "9AM_A_12M", "label": "9AM a 12M"},
                    {"value": "1PM_A_4PM", "label": "1PM a 4PM"},
                ],
            },
            {"key": "department", "label": "Departamento", "type": "text", "required": True, "max_length": 80},
            {"key": "province", "label": "Provincia", "type": "text", "required": True, "max_length": 80},
            {"key": "district", "label": "Distrito", "type": "text", "required": True, "max_length": 120},
            {"key": "urbanization", "label": "Urbanizacion", "type": "text", "max_length": 160},
            {"key": "postal_code", "label": "Codigo postal", "type": "text", "max_length": 20},
            {"key": "street_type", "label": "Tipo via", "type": "text", "max_length": 40},
            {"key": "street_name", "label": "Nombre via", "type": "text", "required": True, "max_length": 180},
            {"key": "address_detail", "label": "Mz / lote / numero", "type": "text", "required": True, "max_length": 220},
            {"key": "latitude", "label": "Latitud GPS", "type": "decimal", "required": True, "capture_gps": True, "min_value": -90, "max_value": 90},
            {"key": "longitude", "label": "Longitud GPS", "type": "decimal", "required": True, "capture_gps": True, "min_value": -180, "max_value": 180},
            {"key": "gps_accuracy_m", "label": "Precision GPS m", "type": "decimal", "required": True, "min_value": 0},
        ],
    },
    {
        "code": "towers_and_capacity",
        "title": "Torres y hogares",
        "fields": [
            {"key": "total_towers", "label": "Total torres", "type": "integer", "required": True, "min_value": 1},
            {"key": "floor_count", "label": "Pisos", "type": "integer", "required": True, "min_value": 0},
            {"key": "total_homes", "label": "Total hogares", "type": "integer", "required": True, "min_value": 0},
        ],
    },
    {
        "code": "tower_breakdown",
        "title": "Detalle de torres",
        "repeatable": True,
        "min_items": 1,
        "fields": [
            {"key": "tower_label", "label": "Torre", "type": "text", "required": True, "readonly": True, "max_length": 40},
            {"key": "floors", "label": "Pisos", "type": "integer", "required": True, "min_value": 0},
            {"key": "homes", "label": "Hogares", "type": "integer", "required": True, "min_value": 0},
        ],
    },
    {
        "code": "tower_contacts",
        "title": "Responsables por torre",
        "repeatable": True,
        "fields": [
            {"key": "tower_label", "label": "Torre", "type": "text", "required": True, "readonly": True, "max_length": 40},
            {"key": "role", "label": "Cargo", "type": "text", "max_length": 80},
            {"key": "full_name", "label": "Nombre", "type": "text", "required": True, "max_length": 160},
            {"key": "phone", "label": "Celular", "type": "phone", "required": True, "max_length": 40},
            {"key": "apartment_or_department", "label": "Departamento", "type": "text", "max_length": 80},
            {"key": "interested_clients", "label": "Clientes interesados", "type": "integer", "min_value": 0},
        ],
    },
    {
        "code": "gca_and_result",
        "title": "Canal",
        "fields": [
            {"key": "channel_agency", "label": "Canal", "type": "text", "max_length": 80},
            {"key": "gca_manager_name", "label": "Gestor", "type": "text", "max_length": 160},
            {"key": "gca_manager_phone", "label": "Celular Gestor", "type": "phone", "max_length": 40},
            {"key": "gca_supervisor_name", "label": "Supervisor", "type": "text", "max_length": 160},
            {"key": "gca_supervisor_phone", "label": "Celular Supervisor", "type": "phone", "max_length": 40},
            {
                "key": "feasibility_result",
                "label": "Resultado",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "PREFACTIBLE", "label": "Prefactible"},
                    {"value": "NO_PREFACTIBLE", "label": "No prefactible"},
                ],
            },
            {"key": "observations", "label": "Observaciones", "type": "textarea"},
        ],
    },
]

PEXT_SPLICE_CHART_FORM_SECTIONS = [
    {
        "code": "node",
        "title": "Nodo",
        "fields": [
            {"key": "node_code", "label": "Nodo", "type": "text", "required": True, "max_length": 80},
            {"key": "jumpear", "label": "Jumpear", "type": "select", "options": [{"value": "SI", "label": "Si"}, {"value": "NO", "label": "No"}]},
            {"key": "jumpeo_count", "label": "Cantidad de jumpeos", "type": "integer", "min_value": 1},
            {"key": "node_visit_count", "label": "Numero de visitas al nodo", "type": "integer", "min_value": 0},
        ],
    },
    {
        "code": "node_jumpeos",
        "title": "Jumpeos",
        "repeatable": True,
        "repeat_count_field": "jumpeo_count",
        "min_items": 1,
        "fields": [
            {"key": "jumpeo_number", "label": "Jumpeo", "type": "text", "readonly": True},
            {"key": "jumpeo_date", "label": "Fecha jumpeo", "type": "date"},
            {"key": "patch_panel", "label": "Patch panel", "type": "text", "max_length": 120},
            {"key": "jumpeo_hilos", "label": "Hilo(s)", "type": "text", "max_length": 120},
            {"key": "odf_slot_olt", "label": "ODF_SLOT_OLT", "type": "text", "max_length": 120},
            {
                "key": "patch_cord_type",
                "label": "Patch cord",
                "type": "select",
                "options": [
                    {"value": "LC_UPC_2MT", "label": "LC/UPC 2MT"},
                    {"value": "LC_UPC_3MT", "label": "LC/UPC 3MT"},
                    {"value": "LC_UPC_5MT", "label": "LC/UPC 5MT"},
                    {"value": "SC_UPC_LC_UPC_10MT", "label": "SC/UPC-LC/UPC 10MT"},
                    {"value": "OTRO", "label": "Otro"},
                ],
            },
            {"key": "patch_cord_quantity", "label": "Cantidad patch cord", "type": "integer", "min_value": 0},
            {"key": "jumpeo_access", "label": "Acceso", "type": "select", "options": [{"value": "REMOTO", "label": "Remoto"}, {"value": "PRESENCIAL", "label": "Presencial"}]},
        ],
    },
    {
        "code": "mufa_control",
        "title": "Mufas",
        "fields": [
            {"key": "mufa_count", "label": "Numero de mufas", "type": "integer", "required": True, "min_value": 1},
        ],
    },
    {
        "code": "mufas",
        "title": "MUFA",
        "repeatable": True,
        "repeat_count_field": "mufa_count",
        "min_items": 1,
        "fields": [
            {"key": "mufa_number", "label": "Nro MUFA", "type": "text", "readonly": True, "required": True},
            {"key": "mufa_code", "label": "Codigo MUFA", "type": "text", "required": True, "max_length": 80},
            {
                "key": "mufa_type",
                "label": "Tipo MUFA",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "NUEVA", "label": "Nueva"},
                    {"value": "INTERVENIDA", "label": "Intervenida"},
                ],
            },
            {"key": "latitude", "label": "Latitud MUFA", "type": "decimal", "capture_gps": True},
            {"key": "longitude", "label": "Longitud MUFA", "type": "decimal", "capture_gps": True},
            {
                "key": "fo_in_type",
                "label": "Tipo FO IN",
                "type": "select",
                "options": [
                    {"value": "96H", "label": "96H"},
                    {"value": "48H", "label": "48H"},
                    {"value": "24H", "label": "24H"},
                    {"value": "12H", "label": "12H"},
                    {"value": "SPLITTER_1X8", "label": "Splitter 1x8"},
                ],
            },
            {"key": "hilo_in", "label": "Hilo IN", "type": "text", "max_length": 40},
            {
                "key": "fo_out_type",
                "label": "Tipo FO OUT",
                "type": "select",
                "options": [
                    {"value": "96H", "label": "96H"},
                    {"value": "48H", "label": "48H"},
                    {"value": "24H", "label": "24H"},
                    {"value": "12H", "label": "12H"},
                    {"value": "SPLITTER_1X8", "label": "Splitter 1x8"},
                ],
            },
            {"key": "hilo_out", "label": "Hilo OUT", "type": "text", "max_length": 40},
            {"key": "splitter_count", "label": "Cantidad splitters 1x8", "type": "integer", "min_value": 0},
            {
                "key": "elemento_instalado",
                "label": "Elemento instalado",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "NINGUNO", "label": "NINGUNO"},
                    {"value": "SPLITTER_1X8_PLC_SIN_CONECTOR", "label": "SPLITTER 1X8 PLC SIN CONECTOR"},
                    {"value": "SPLITTER_PLC_1X16", "label": "SPLITTER PLC 1X16"},
                    {"value": "SPLITTER_1X8_PLC_CAJA_FIJA_SC_APC", "label": "SPLITTER 1X8 PLC EN CAJA FIJA CON ENFRENTADORES SC/APC"},
                    {"value": "SPLITTER_PLC_1X2_SIN_CONECTOR", "label": "SPLITTER PLC 1X2 SIN CONECTOR"},
                ],
            },
            {
                "key": "trabajo",
                "label": "Trabajo",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "VERIFICACION", "label": "VERIFICACION"},
                    {"value": "EMPALME", "label": "EMPALME"},
                ],
            },
            {"key": "observations", "label": "Observaciones", "type": "textarea"},
        ],
    },
    {
        "code": "last_mufa_outputs",
        "title": "Ultima MUFA - FO OUT hacia edificio",
        "repeatable": True,
        "min_items": 8,
        "fields": [
            {"key": "fo_in", "label": "FO IN", "type": "text", "readonly": True, "max_length": 80},
            {"key": "fo_out", "label": "FO OUT", "type": "text", "readonly": True, "max_length": 80},
            {"key": "splitter_label", "label": "Splitter", "type": "text", "readonly": True, "max_length": 80},
            {"key": "out_number", "label": "Salida splitter / hilo empalmado", "type": "text", "max_length": 40},
            {
                "key": "output_status",
                "label": "Estado salida",
                "type": "select",
                "options": [
                    {"value": "ASIGNADA", "label": "Asignada"},
                    {"value": "LIBRE", "label": "Libre"},
                ],
            },
            {
                "key": "tendido_fo_type",
                "label": "Tipo FO tendido",
                "type": "select",
                "options": [
                    {"value": "96H", "label": "96H"},
                    {"value": "48H", "label": "48H"},
                    {"value": "24H", "label": "24H"},
                    {"value": "12H", "label": "12H"},
                ],
            },
            {"key": "tower_destination", "label": "Torre destino", "type": "text", "max_length": 80},
            {"key": "tendido", "label": "Tendido / observacion", "type": "text", "max_length": 120},
        ],
    },
    {
        "code": "nap_control",
        "title": "NAPs",
        "fields": [
            {"key": "nap_count", "label": "Numero de NAPs", "type": "integer", "required": True, "min_value": 1},
        ],
    },
    {
        "code": "naps",
        "title": "NAP",
        "repeatable": True,
        "repeat_count_field": "nap_count",
        "min_items": 1,
        "fields": [
            {"key": "out_12h", "label": "12H - OUT", "type": "text", "readonly": True, "max_length": 40},
            {
                "key": "splice_type",
                "label": "Empalme",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "EN_PUNTA", "label": "EN PUNTA"},
                    {"value": "SANGRADO", "label": "SANGRADO"},
                ],
            },
            {"key": "tendido", "label": "Tendido", "type": "text", "max_length": 120},
            {"key": "tower_or_riser", "label": "Torre / montante", "type": "text", "max_length": 80},
            {"key": "floor", "label": "Piso", "type": "text", "max_length": 40},
            {"key": "nap_number", "label": "NAP", "type": "text", "readonly": True, "max_length": 40},
            {"key": "label", "label": "Rotulo", "type": "text", "required": True, "max_length": 120},
            {
                "key": "tipo_nap",
                "label": "Tipo NAP",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "PLOMA", "label": "PLOMA"},
                    {"value": "BLANCA", "label": "BLANCA"},
                    {"value": "DIXON", "label": "DIXON"},
                    {"value": "CTO", "label": "CTO"},
                ],
            },
            {"key": "potencia_dbm", "label": "Potencia dBm", "type": "decimal", "required": True},
        ],
    },
    {
        "code": "execution_dates",
        "title": "Fechas de ejecucion",
        "fields": [
            {"key": "fecha_inicio_ejecucion", "label": "Fecha inicio ejecucion", "type": "date", "required": True},
            {"key": "fecha_fin_ejecucion", "label": "Fecha fin ejecucion", "type": "date", "required": True},
        ],
    },
    {
        "code": "execution_status_info",
        "title": "Datos adicionales STATUS",
        "fields": [
            {"key": "supervisor_win", "label": "Supervisor WIN", "type": "text", "max_length": 160},
            {"key": "contractor_name", "label": "Contrata", "type": "text", "max_length": 160},
            {"key": "subcontractor_name", "label": "Subcontrata", "type": "text", "max_length": 160},
            {"key": "technician_name", "label": "Tecnico", "type": "text", "max_length": 160},
        ],
    },
    {
        "code": "fiber_run_control",
        "title": "Tendido fibra optica",
        "fields": [
            {"key": "fiber_run_count", "label": "Numero de tendidos FO", "type": "integer", "required": True, "min_value": 1},
        ],
    },
    {
        "code": "fiber_runs",
        "title": "Tendido fibra optica",
        "repeatable": True,
        "repeat_count_field": "fiber_run_count",
        "min_items": 1,
        "fields": [
            {
                "key": "tipo_fibra",
                "label": "Tipo de fibra",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "12H", "label": "12H"},
                    {"value": "24H", "label": "24H"},
                    {"value": "48H", "label": "48H"},
                    {"value": "96H", "label": "96H"},
                ],
            },
            {"key": "metros_externo", "label": "Metros externo", "type": "decimal", "required": True, "min_value": 0},
            {"key": "metros_interno", "label": "Metros interno", "type": "decimal", "required": True, "min_value": 0},
            {"key": "total", "label": "Total", "type": "decimal", "readonly": True},
            {"key": "observacion", "label": "Observacion", "type": "textarea"},
        ],
    },
    {
        "code": "fiber_tip_control",
        "title": "Puntas de fibra",
        "fields": [
            {"key": "fiber_tip_count", "label": "Numero de puntas de fibra", "type": "integer", "required": True, "min_value": 1},
        ],
    },
    {
        "code": "fiber_tips",
        "title": "Punta de fibra",
        "repeatable": True,
        "repeat_count_field": "fiber_tip_count",
        "min_items": 1,
        "fields": [
            {
                "key": "tipo_fibra",
                "label": "Tipo de fibra",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "12H", "label": "12H"},
                    {"value": "24H", "label": "24H"},
                    {"value": "48H", "label": "48H"},
                    {"value": "96H", "label": "96H"},
                ],
            },
            {"key": "punta_inicial", "label": "Punta inicial", "type": "text", "required": True, "max_length": 80},
            {"key": "punta_final", "label": "Punta final", "type": "text", "required": True, "max_length": 80},
        ],
    },
]

PEXT_SPLICE_ENTRY_FORM_SECTIONS = []


def _forms_for_project(project_type: str) -> dict[str, Any]:
    if project_type == "OC":
        return {"prefeasibility": [], "splice_chart": [], "splice_entry": []}
    return {
        "prefeasibility": PEXT_PREFEASIBILITY_FORM_SECTIONS,
        "splice_chart": PEXT_SPLICE_CHART_FORM_SECTIONS,
        "splice_entry": PEXT_SPLICE_ENTRY_FORM_SECTIONS,
    }


def _project_row_to_mobile(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "project_code": row.project_code,
        "project_type": row.project_type,
        "name": row.name,
        "priority": row.priority,
        "current_status": row.current_status,
        "scheduled_date": row.scheduled_date,
        "status_version": row.status_version,
        "property": {
            "id": str(row.property_id),
            "external_property_id": row.external_property_id,
            "address": row.address,
            "district": row.district,
            "node_code": row.node_code,
            "latitude": row.latitude,
            "longitude": row.longitude,
        },
    }


def _select_mobile_project_sql() -> str:
    return """
        SELECT p.id, p.property_id, p.project_code, p.project_type, p.name, p.priority,
               p.current_status, p.scheduled_date, p.status_version,
               pr.external_property_id, pr.address, pr.district, pr.node_code,
               pr.latitude, pr.longitude
        FROM projects p
        JOIN properties pr ON pr.id = p.property_id
    """


def list_my_projects(db: Session, user_id: str) -> dict[str, Any]:
    rows = db.execute(
        text(
            f"""
            {_select_mobile_project_sql()}
            WHERE p.technician_id = CAST(:user_id AS uuid)
              AND p.current_status IN ('FACTIBILIDAD_EN_REVISION', 'ASIGNADO_A_CUADRILLA', 'EN_EJECUCION', 'OBSERVADO')
            ORDER BY p.scheduled_date NULLS LAST, p.created_at DESC
            """
        ),
        {"user_id": user_id},
    ).all()
    items = [_project_row_to_mobile(row) for row in rows]
    return {"items": items, "total": len(items)}


def get_mobile_project_for_technician(db: Session, project_id: str, user_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            f"""
            {_select_mobile_project_sql()}
            WHERE p.id = CAST(:project_id AS uuid)
              AND p.technician_id = CAST(:user_id AS uuid)
            """
        ),
        {"project_id": project_id, "user_id": user_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned project not found")
    return _project_row_to_mobile(row)


def _requirements_for_project(project_type: str, current_status: str) -> list[dict[str, Any]]:
    if project_type == "OC":
        return OC_FIELD_REQUIREMENTS
    if project_type == "PEXT" and current_status == "FACTIBILIDAD_EN_REVISION":
        return PEXT_PREFEASIBILITY_VISIT_REQUIREMENTS
    if project_type == "MIXTO":
        return PEXT_FIELD_REQUIREMENTS + [item for item in OC_FIELD_REQUIREMENTS if item["code"].startswith("OC_")]
    return PEXT_FIELD_REQUIREMENTS


def _get_prefeasibility_or_empty(db: Session, project_id: str) -> dict[str, Any] | None:
    row = db.execute(
        text("SELECT * FROM pext_prefeasibility_forms WHERE project_id = CAST(:project_id AS uuid)"),
        {"project_id": project_id},
    ).first()
    if row is None:
        return None
    fields = dict(row._mapping)
    form_id = str(fields.pop("id"))
    fields["project_id"] = str(fields["project_id"])
    if fields.get("evaluated_by"):
        fields["evaluated_by"] = str(fields["evaluated_by"])
    fields.pop("location", None)
    towers = db.execute(
        text(
            """
            SELECT tower_label, floors, homes
            FROM pext_prefeasibility_towers
            WHERE prefeasibility_id = CAST(:prefeasibility_id AS uuid)
            ORDER BY tower_label
            """
        ),
        {"prefeasibility_id": form_id},
    ).all()
    tower_contacts = db.execute(
        text(
            """
            SELECT tower_label, role, full_name, phone, apartment_or_department, interested_clients
            FROM pext_prefeasibility_tower_contacts
            WHERE prefeasibility_id = CAST(:prefeasibility_id AS uuid)
            ORDER BY tower_label, created_at
            """
        ),
        {"prefeasibility_id": form_id},
    ).all()
    fields["towers"] = [{"tower_label": item.tower_label, "floors": item.floors, "homes": item.homes} for item in towers]
    fields["tower_contacts"] = [
        {
            "tower_label": item.tower_label,
            "role": item.role,
            "full_name": item.full_name,
            "phone": item.phone,
            "apartment_or_department": item.apartment_or_department,
            "interested_clients": item.interested_clients,
        }
        for item in tower_contacts
    ]
    return {
        "id": form_id,
        "feasibility_result": fields.get("feasibility_result"),
        "fields": fields,
    }


def _list_splice_chart_summaries(db: Session, project_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT c.id, c.mufa_code, c.mufa_type, c.node_code, c.fiber_capacity, c.status,
                   COUNT(e.id) AS entry_count
            FROM pext_splice_charts c
            LEFT JOIN pext_splice_chart_entries e ON e.chart_id = c.id
            WHERE c.project_id = CAST(:project_id AS uuid)
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """
        ),
        {"project_id": project_id},
    ).all()
    return [
        {
            "id": str(row.id),
            "mufa_code": row.mufa_code,
            "mufa_type": row.mufa_type,
            "node_code": row.node_code,
            "fiber_capacity": row.fiber_capacity,
            "status": row.status,
            "entry_count": row.entry_count,
        }
        for row in rows
    ]


def _get_splice_chart_draft(db: Session, project_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT metadata
            FROM pext_splice_charts
            WHERE project_id = CAST(:project_id AS uuid)
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """
        ),
        {"project_id": project_id},
    ).first()
    if row is None:
        return {}
    if isinstance(row.metadata, dict):
        return row.metadata
    return json.loads(row.metadata or "{}")


def get_field_package(db: Session, project_id: str, user_id: str) -> dict[str, Any]:
    project = get_mobile_project_for_technician(db, project_id, user_id)
    return {
        "project": project,
        "requirements": _requirements_for_project(project["project_type"], project["current_status"]),
        "forms": _forms_for_project(project["project_type"]),
        "prefeasibility": _get_prefeasibility_or_empty(db, project_id),
        "splice_chart_draft": _get_splice_chart_draft(db, project_id),
        "splice_charts": _list_splice_chart_summaries(db, project_id),
    }
