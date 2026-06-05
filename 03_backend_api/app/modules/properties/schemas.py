from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PropertyCreateRequest(BaseModel):
    external_property_id: str = Field(min_length=2, max_length=80)
    source: str = Field(default="MANUAL", pattern="^(WIN|EJAS|MANUAL)$")
    address: str = Field(min_length=3, max_length=255)
    district: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    tower_count: int | None = Field(default=None, ge=0)
    riser_count: int | None = Field(default=None, ge=0)
    floor_count: int | None = Field(default=None, ge=0)
    hp_count: int | None = Field(default=None, ge=0)
    node_code: str | None = Field(default=None, max_length=80)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    received_at: datetime | None = None


class PropertyUpdateRequest(BaseModel):
    external_property_id: str | None = Field(default=None, min_length=2, max_length=80)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    district: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    tower_count: int | None = Field(default=None, ge=0)
    riser_count: int | None = Field(default=None, ge=0)
    floor_count: int | None = Field(default=None, ge=0)
    hp_count: int | None = Field(default=None, ge=0)
    node_code: str | None = Field(default=None, max_length=80)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    current_status: str | None = Field(default=None, max_length=80)


class PropertyResponse(BaseModel):
    id: str
    external_property_id: str
    source: str
    address: str
    district: str | None = None
    province: str | None = None
    region: str | None = None
    tower_count: int | None = None
    riser_count: int | None = None
    floor_count: int | None = None
    hp_count: int | None = None
    node_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    current_status: str


class PropertyListResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    limit: int
    offset: int
