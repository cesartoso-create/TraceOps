from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MobilePropertySummary(BaseModel):
    id: str
    external_property_id: str
    address: str
    district: str | None = None
    node_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class MobileProjectSummary(BaseModel):
    id: str
    project_code: str
    project_type: str
    name: str
    priority: str
    current_status: str
    scheduled_date: date | None = None
    status_version: int
    property: MobilePropertySummary


class MobileProjectListResponse(BaseModel):
    items: list[MobileProjectSummary]
    total: int


class MobileFieldRequirement(BaseModel):
    code: str
    label: str
    required: bool = True
    min_count: int = 1


class MobileFormFieldOption(BaseModel):
    value: str
    label: str


class MobileFormField(BaseModel):
    key: str
    label: str
    type: str
    required: bool = False
    max_length: int | None = None
    min_value: int | Decimal | None = None
    max_value: int | Decimal | None = None
    options: list[MobileFormFieldOption] = Field(default_factory=list)
    capture_gps: bool = False
    readonly: bool = False
    offline_required: bool = True


class MobileFormSection(BaseModel):
    code: str
    title: str
    repeatable: bool = False
    min_items: int = 0
    repeat_count_field: str | None = None
    repeat_count_fixed: int | None = None
    fields: list[MobileFormField] = Field(default_factory=list)


class MobileFieldForms(BaseModel):
    prefeasibility: list[MobileFormSection] = Field(default_factory=list)
    splice_chart: list[MobileFormSection] = Field(default_factory=list)
    splice_entry: list[MobileFormSection] = Field(default_factory=list)


class MobilePextPrefeasibility(BaseModel):
    id: str | None = None
    feasibility_result: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)


class MobileSpliceChartSummary(BaseModel):
    id: str
    mufa_code: str
    mufa_type: str
    node_code: str | None = None
    fiber_capacity: str | None = None
    status: str
    entry_count: int


class MobileFieldPackageResponse(BaseModel):
    project: MobileProjectSummary
    requirements: list[MobileFieldRequirement]
    forms: MobileFieldForms = Field(default_factory=MobileFieldForms)
    prefeasibility: MobilePextPrefeasibility | None = None
    splice_chart_draft: dict[str, Any] = Field(default_factory=dict)
    splice_charts: list[MobileSpliceChartSummary] = Field(default_factory=list)
