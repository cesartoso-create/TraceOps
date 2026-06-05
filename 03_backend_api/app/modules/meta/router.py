from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.meta.ubigeo import list_departments, list_districts, list_provinces

router = APIRouter()


@router.get("/meta")
def meta() -> dict[str, str]:
    return {"name": "TraceOps", "version": "0.1.0", "environment": settings.traceops_env}


@router.get("/ubigeo/departments")
def ubigeo_departments(db: Session = Depends(get_db)) -> list[dict]:
    return list_departments(db)


@router.get("/ubigeo/provinces")
def ubigeo_provinces(department_id: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return list_provinces(db, department_id=department_id)


@router.get("/ubigeo/districts")
def ubigeo_districts(province_id: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return list_districts(db, province_id=province_id)
