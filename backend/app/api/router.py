from fastapi import APIRouter

from app.api.v1.catalogs import router as catalogs_router
from app.api.v1.diagnosis_states import router as diagnosis_states_router
from app.api.v1.health import router as health_router
from app.api.v1.meta import router as meta_router
from app.api.v1.patients import router as patients_router
from app.api.v1.stac_cards import router as stac_cards_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(patients_router)
api_router.include_router(meta_router)
api_router.include_router(stac_cards_router)
api_router.include_router(diagnosis_states_router)
api_router.include_router(catalogs_router)
