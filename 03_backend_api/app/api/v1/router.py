from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.evidences.router import router as evidences_router
from app.modules.field_ops.router import router as field_ops_router
from app.modules.files.router import router as files_router
from app.modules.meta.router import router as meta_router
from app.modules.mobile.router import router as mobile_router
from app.modules.pext.router import router as pext_router
from app.modules.properties.router import router as properties_router
from app.modules.projects.router import router as projects_router
from app.modules.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(meta_router, tags=["meta"])
api_router.include_router(mobile_router, prefix="/mobile", tags=["mobile"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(field_ops_router, tags=["field-ops"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(pext_router, prefix="/pext", tags=["pext"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(evidences_router, prefix="/evidences", tags=["evidences"])
