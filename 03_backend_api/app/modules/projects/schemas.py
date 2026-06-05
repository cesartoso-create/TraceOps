from datetime import date

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    property_id: str
    parent_project_id: str | None = None
    network_group_id: str | None = None
    project_scope: str = Field(default="PREDIO", pattern="^(PREDIO|TENDIDO_GENERAL|TRONCAL|DISTRIBUCION)$")
    project_code: str = Field(min_length=2, max_length=80)
    project_type: str = Field(pattern="^(PEXT|OC|MIXTO)$")
    name: str = Field(min_length=2, max_length=180)
    priority: str = Field(default="MEDIA", pattern="^(BAJA|MEDIA|ALTA|CRITICA)$")
    supervisor_id: str | None = None
    contractor_id: str | None = None
    subcontractor_id: str | None = None
    crew_id: str | None = None
    technician_id: str | None = None
    scheduled_date: date | None = None


class ProjectUpdateRequest(BaseModel):
    parent_project_id: str | None = None
    network_group_id: str | None = None
    project_scope: str | None = Field(default=None, pattern="^(PREDIO|TENDIDO_GENERAL|TRONCAL|DISTRIBUCION)$")
    name: str | None = Field(default=None, min_length=2, max_length=180)
    priority: str | None = Field(default=None, pattern="^(BAJA|MEDIA|ALTA|CRITICA)$")
    supervisor_id: str | None = None
    contractor_id: str | None = None
    subcontractor_id: str | None = None
    crew_id: str | None = None
    technician_id: str | None = None
    scheduled_date: date | None = None


class ProjectAssignRequest(BaseModel):
    supervisor_id: str | None = None
    contractor_id: str | None = None
    subcontractor_id: str | None = None
    crew_id: str | None = None
    technician_id: str | None = None
    scheduled_date: date | None = None


class ProjectStatusTransitionRequest(BaseModel):
    to_status: str = Field(min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=500)


class ProjectResponse(BaseModel):
    id: str
    property_id: str
    parent_project_id: str | None = None
    network_group_id: str | None = None
    project_scope: str
    external_property_id: str | None = None
    project_code: str
    project_type: str
    name: str
    priority: str
    manager_id: str | None = None
    supervisor_id: str | None = None
    contractor_id: str | None = None
    subcontractor_id: str | None = None
    crew_id: str | None = None
    technician_id: str | None = None
    scheduled_date: date | None = None
    current_status: str
    last_from_status: str | None = None
    status_version: int


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    limit: int
    offset: int
