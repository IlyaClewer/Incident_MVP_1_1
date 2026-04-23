from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.meta import MetaResponse
from app.services.patients_service import PatientsService

router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
async def get_meta(db: AsyncSession = Depends(get_db)) -> MetaResponse:
    (
        expert_groups,
        group_diagnoses,
        diagnoses,
        diagnosis_states,
        stac_card_diagnosis_index,
        model_results,
    ) = await PatientsService.get_meta(db)
    return MetaResponse(
        expert_groups=expert_groups,
        group_diagnoses=group_diagnoses,
        diagnoses=diagnoses,
        diagnosis_states=diagnosis_states,
        stac_card_diagnosis_index=stac_card_diagnosis_index,
        model_results=model_results,
    )
