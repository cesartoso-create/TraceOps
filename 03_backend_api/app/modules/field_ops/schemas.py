from datetime import date

from pydantic import BaseModel, Field


class ContractorCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    tax_id: str | None = Field(default=None, max_length=40)
    type: str = Field(pattern="^(CONTRATA|SUBCONTRATA)$")
    parent_contractor_id: str | None = None


class ContractorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    tax_id: str | None = Field(default=None, max_length=40)
    parent_contractor_id: str | None = None
    is_active: bool | None = None


class ContractorResponse(BaseModel):
    id: str
    name: str
    tax_id: str | None = None
    type: str
    parent_contractor_id: str | None = None
    is_active: bool


class CrewCreateRequest(BaseModel):
    contractor_id: str
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    supervisor_id: str | None = None


class CrewUpdateRequest(BaseModel):
    contractor_id: str | None = None
    code: str | None = Field(default=None, min_length=2, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    supervisor_id: str | None = None
    is_active: bool | None = None


class CrewResponse(BaseModel):
    id: str
    contractor_id: str | None = None
    code: str
    name: str
    supervisor_id: str | None = None
    is_active: bool


class CrewMemberAddRequest(BaseModel):
    user_id: str
    position: str | None = Field(default=None, max_length=80)
    valid_from: date | None = None


class CrewMemberResponse(BaseModel):
    id: str
    crew_id: str
    user_id: str
    full_name: str
    email: str
    role: str | None = None
    position: str | None = None
    valid_from: date
    valid_to: date | None = None
    is_active: bool

