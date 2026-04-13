from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.patients import PatientsResponse
from app.services.patients_service import PatientsService

router = APIRouter(tags=["patients"])


@router.get("/patients", response_model=PatientsResponse)
async def get_patients(db: AsyncSession = Depends(get_db)) -> PatientsResponse:
    patients = await PatientsService.list_patients(db)
    return PatientsResponse(patients=patients)
