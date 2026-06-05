from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.field_ops.schemas import (
    ContractorCreateRequest,
    ContractorResponse,
    ContractorUpdateRequest,
    CrewCreateRequest,
    CrewMemberAddRequest,
    CrewMemberResponse,
    CrewResponse,
    CrewUpdateRequest,
)
from app.modules.field_ops.service import (
    add_crew_member,
    create_contractor,
    create_crew,
    get_contractor,
    get_crew,
    list_contractors,
    list_crew_members,
    list_crews,
    remove_crew_member,
    update_contractor,
    update_crew,
)

router = APIRouter()


@router.get("/contractors", response_model=list[ContractorResponse], dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def contractors_list(
    db: Annotated[Session, Depends(get_db)],
    type: str | None = None,
    is_active: bool | None = None,
) -> list[dict]:
    return list_contractors(db, type=type, is_active=is_active)


@router.post("/contractors", response_model=ContractorResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def contractors_create(payload: ContractorCreateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return create_contractor(db, payload)


@router.get("/contractors/{contractor_id}", response_model=ContractorResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def contractors_get(contractor_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_contractor(db, contractor_id)


@router.patch("/contractors/{contractor_id}", response_model=ContractorResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def contractors_update(
    contractor_id: str,
    payload: ContractorUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return update_contractor(db, contractor_id, payload)


@router.get("/crews", response_model=list[CrewResponse], dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def crews_list(
    db: Annotated[Session, Depends(get_db)],
    contractor_id: str | None = None,
    is_active: bool | None = None,
) -> list[dict]:
    return list_crews(db, contractor_id=contractor_id, is_active=is_active)


@router.post("/crews", response_model=CrewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def crews_create(payload: CrewCreateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return create_crew(db, payload)


@router.get("/crews/{crew_id}", response_model=CrewResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def crews_get(crew_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_crew(db, crew_id)


@router.patch("/crews/{crew_id}", response_model=CrewResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def crews_update(crew_id: str, payload: CrewUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    return update_crew(db, crew_id, payload)


@router.get("/crews/{crew_id}/members", response_model=list[CrewMemberResponse], dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR"))])
def crew_members_list(crew_id: str, db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    return list_crew_members(db, crew_id)


@router.post("/crews/{crew_id}/members", response_model=CrewMemberResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def crew_members_add(
    crew_id: str,
    payload: CrewMemberAddRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return add_crew_member(db, crew_id, payload)


@router.delete("/crews/{crew_id}/members/{member_id}", response_model=CrewMemberResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR"))])
def crew_members_remove(crew_id: str, member_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return remove_crew_member(db, crew_id, member_id)
