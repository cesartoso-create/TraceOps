from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class PextPrefeasibilityTowerRequest(BaseModel):
    tower_label: str = Field(max_length=40)
    floors: int | None = Field(default=None, ge=0)
    homes: int | None = Field(default=None, ge=0)


class PextPrefeasibilityTowerContactRequest(BaseModel):
    tower_label: str = Field(max_length=40)
    role: str | None = Field(default=None, max_length=80)
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    apartment_or_department: str | None = Field(default=None, max_length=80)
    interested_clients: int | None = Field(default=None, ge=0)


class PextPrefeasibilityUpsertRequest(BaseModel):
    building_name: str | None = Field(default=None, max_length=220)
    condominium_name: str | None = Field(default=None, max_length=160)
    project_type_option: str | None = Field(default=None, max_length=80)
    project_subtype: str | None = Field(default=None, max_length=120)
    source_origin: str | None = Field(default=None, max_length=80)
    classification: str | None = Field(default=None, max_length=80)
    construction_type: str | None = Field(default=None, max_length=80)
    owner_delivery_date: date | None = None
    riser_completion_date: date | None = None
    authorized_access_type: str | None = Field(default=None, max_length=80)
    has_owners_board: bool | None = None
    auth_letter_contact_role: str | None = Field(default=None, max_length=80)
    auth_letter_contact_name: str | None = Field(default=None, max_length=160)
    auth_letter_contact_phone: str | None = Field(default=None, max_length=40)
    auth_letter_contact_email: str | None = Field(default=None, max_length=160)
    access_contact_role: str | None = Field(default=None, max_length=80)
    access_contact_name: str | None = Field(default=None, max_length=160)
    access_contact_phone: str | None = Field(default=None, max_length=40)
    access_contact_email: str | None = Field(default=None, max_length=160)
    technical_visit_date: date | None = None
    visit_time_range: str | None = Field(default=None, max_length=80)
    department: str | None = Field(default=None, max_length=80)
    province: str | None = Field(default=None, max_length=80)
    district: str | None = Field(default=None, max_length=120)
    urbanization: str | None = Field(default=None, max_length=160)
    postal_code: str | None = Field(default=None, max_length=20)
    street_type: str | None = Field(default=None, max_length=40)
    street_name: str | None = Field(default=None, max_length=180)
    address_detail: str | None = Field(default=None, max_length=220)
    coordinates_text: str | None = Field(default=None, max_length=120)
    total_towers: int | None = Field(default=None, ge=0)
    total_homes: int | None = Field(default=None, ge=0)
    channel_agency: str | None = Field(default=None, max_length=80)
    whatsapp_group_required: bool | None = None
    gca_manager_name: str | None = Field(default=None, max_length=160)
    gca_manager_phone: str | None = Field(default=None, max_length=40)
    gca_supervisor_name: str | None = Field(default=None, max_length=160)
    gca_supervisor_phone: str | None = Field(default=None, max_length=40)
    visit_date: date | None = None
    contact_name: str | None = Field(default=None, max_length=160)
    contact_phone: str | None = Field(default=None, max_length=40)
    address_confirmed: bool = False
    building_type: str | None = Field(default=None, max_length=80)
    access_type: str | None = Field(default=None, max_length=80)
    tower_count: int | None = Field(default=None, ge=0)
    floor_count: int | None = Field(default=None, ge=0)
    riser_count: int | None = Field(default=None, ge=0)
    hp_count: int | None = Field(default=None, ge=0)
    existing_fo: bool | None = None
    nearest_node_code: str | None = Field(default=None, max_length=80)
    distance_to_node_m: Decimal | None = Field(default=None, ge=0)
    feeder_mufa_code: str | None = Field(default=None, max_length=80)
    requires_oc: bool | None = None
    oc_distance_m: Decimal | None = Field(default=None, ge=0)
    canalization_type: str | None = Field(default=None, max_length=80)
    poles_required: int | None = Field(default=None, ge=0)
    nap_required_count: int | None = Field(default=None, ge=0)
    splitter_required: str | None = Field(default=None, max_length=80)
    estimated_power_dbm: Decimal | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    gps_accuracy_m: Decimal | None = Field(default=None, ge=0)
    feasibility_result: str = Field(default="REQUIERE_VISITA", pattern="^(PREFACTIBLE|NO_PREFACTIBLE|REQUIERE_VISITA)$")
    risks: str | None = None
    restrictions: str | None = None
    observations: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    towers: list[PextPrefeasibilityTowerRequest] = Field(default_factory=list)
    tower_contacts: list[PextPrefeasibilityTowerContactRequest] = Field(default_factory=list)


class PextPrefeasibilityResponse(PextPrefeasibilityUpsertRequest):
    id: str
    project_id: str
    evaluated_by: str | None = None


class SpliceChartCreateRequest(BaseModel):
    mufa_code: str = Field(min_length=2, max_length=80)
    mufa_type: str = Field(pattern="^(NUEVA|INTERVENIDA)$")
    node_code: str | None = Field(default=None, max_length=80)
    cable_in: str | None = Field(default=None, max_length=120)
    cable_out: str | None = Field(default=None, max_length=120)
    fiber_capacity: str | None = Field(default=None, max_length=40)
    observations: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpliceChartUpdateRequest(BaseModel):
    mufa_code: str | None = Field(default=None, min_length=2, max_length=80)
    mufa_type: str | None = Field(default=None, pattern="^(NUEVA|INTERVENIDA)$")
    node_code: str | None = Field(default=None, max_length=80)
    cable_in: str | None = Field(default=None, max_length=120)
    cable_out: str | None = Field(default=None, max_length=120)
    fiber_capacity: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, pattern="^(BORRADOR|ENVIADO|VALIDADO|OBSERVADO)$")
    observations: str | None = None
    metadata: dict[str, Any] | None = None


class SpliceEntryCreateRequest(BaseModel):
    sequence_number: int = Field(ge=1)
    tray: str | None = Field(default=None, max_length=40)
    tube_color: str | None = Field(default=None, max_length=40)
    fiber_in_number: int | None = Field(default=None, ge=1)
    fiber_in_color: str | None = Field(default=None, max_length=40)
    fiber_out_number: int | None = Field(default=None, ge=1)
    fiber_out_color: str | None = Field(default=None, max_length=40)
    service_type: str | None = Field(default=None, max_length=80)
    nap_code: str | None = Field(default=None, max_length=80)
    destination: str | None = Field(default=None, max_length=160)
    signal_dbm: Decimal | None = None
    observations: str | None = None


class SpliceEntryResponse(SpliceEntryCreateRequest):
    id: str
    chart_id: str


class SpliceChartResponse(SpliceChartCreateRequest):
    id: str
    project_id: str
    prepared_by: str | None = None
    status: str
    entries: list[SpliceEntryResponse] = Field(default_factory=list)


class PextFieldOutputResponse(BaseModel):
    project: dict[str, Any]
    property: dict[str, Any]
    prefeasibility: dict[str, Any] | None = None
    splice_charts: list[dict[str, Any]] = Field(default_factory=list)
    evidences: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class PextFieldValidationResponse(BaseModel):
    is_complete: bool
    blocking_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    required_evidence_counts: dict[str, int] = Field(default_factory=dict)
    actual_evidence_counts: dict[str, int] = Field(default_factory=dict)


class PextExecutionPackageCreateRequest(BaseModel):
    package_stage: str = Field(
        default="BASE_WIN_APROBADA",
        pattern="^(BASE_WIN_APROBADA|EJECUCION_EDITADA|AS_BUILT_FINAL)$",
    )
    change_reason: str | None = Field(default=None, max_length=500)
    source_package_id: str | None = None


class PextExecutionPackageResponse(BaseModel):
    id: str
    project_id: str
    package_stage: str
    version_number: int
    source_package_id: str | None = None
    project_status: str
    snapshot: dict[str, Any]
    change_reason: str | None = None
    created_by: str | None = None
    is_current: bool
    created_at: Any
