from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceCreateRequest(BaseModel):
    project_id: str
    category: str
    subcategory: str | None = Field(default=None, max_length=80)
    associated_code: str | None = Field(default=None, max_length=120)
    element_type: str | None = Field(default=None, max_length=80)
    pext_prefeasibility_id: str | None = None
    splice_chart_id: str | None = None
    splice_entry_id: str | None = None
    local_client_uuid: UUID
    captured_at: datetime
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)
    gps_accuracy_m: Decimal | None = Field(default=None, ge=0)
    gps_provider: str | None = Field(default=None, max_length=40)
    device_id: str | None = None
    checksum_sha256: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceResponse(BaseModel):
    id: str
    project_id: str
    captured_by: str | None = None
    category: str
    subcategory: str | None = None
    associated_code: str | None = None
    element_type: str | None = None
    pext_prefeasibility_id: str | None = None
    splice_chart_id: str | None = None
    splice_entry_id: str | None = None
    local_client_uuid: str
    captured_at: datetime
    received_at: datetime
    latitude: Decimal
    longitude: Decimal
    gps_accuracy_m: Decimal | None = None
    gps_provider: str | None = None
    gps_validated: bool
    file_id: str | None = None
    thumbnail_file_id: str | None = None
    checksum_sha256: str | None = None
    validation_status: str
    metadata: dict[str, Any]


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    limit: int
    offset: int

