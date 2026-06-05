from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.domain import EvidenceCategory
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.evidences.schemas import EvidenceCreateRequest, EvidenceListResponse, EvidenceResponse
from app.modules.evidences.service import create_evidence, delete_evidence, get_evidence, list_project_evidences

router = APIRouter()


@router.get("/categories")
def evidence_categories() -> list[str]:
    return [category.value for category in EvidenceCategory]


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO"))],
)
def evidences_create(
    payload: EvidenceCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return create_evidence(db, payload, current_user["id"])


@router.get("/project/{project_id}/items", response_model=EvidenceListResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO", "LIQUIDADOR", "AUDITOR"))])
def project_evidences_list(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return list_project_evidences(db, project_id, category=category, limit=limit, offset=offset)


@router.get("/{evidence_id}", response_model=EvidenceResponse, dependencies=[Depends(require_roles("ADMIN", "GESTOR", "SUPERVISOR", "TECNICO", "LIQUIDADOR", "AUDITOR"))])
def evidences_get(evidence_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return get_evidence(db, evidence_id)


@router.delete("/{evidence_id}", dependencies=[Depends(require_roles("ADMIN", "SUPERVISOR", "TECNICO"))])
def evidences_delete(evidence_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    return delete_evidence(db, evidence_id)
