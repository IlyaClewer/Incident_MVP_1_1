from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.diagnosis_states import (
    DiagnosisStateTransferRequest,
    DiagnosisStateTransferResponse,
    DiagnosisStateUpdateRequest,
    DiagnosisStateUpdateResponse,
)
from app.services.diagnosis_state_service import DiagnosisStateService

router = APIRouter(tags=["diagnosis-states"])


@router.patch("/diagnosis-states/{diagnosis_state_id}", response_model=DiagnosisStateUpdateResponse)
async def patch_diagnosis_state(
    diagnosis_state_id: int,
    payload: DiagnosisStateUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> DiagnosisStateUpdateResponse:
    diagnosis_state = await DiagnosisStateService.update_status(
        db,
        diagnosis_state_id=diagnosis_state_id,
        target_status=payload.status,
        comment=payload.comment,
    )
    return DiagnosisStateUpdateResponse(diagnosis_state=diagnosis_state)


@router.post(
    "/diagnosis-states/{diagnosis_state_id}/transfer",
    response_model=DiagnosisStateTransferResponse,
)
async def transfer_diagnosis_state_events(
    diagnosis_state_id: int,
    payload: DiagnosisStateTransferRequest,
    db: AsyncSession = Depends(get_db),
) -> DiagnosisStateTransferResponse:
    transferred_event_ids = await DiagnosisStateService.transfer_events(
        db,
        source_diagnosis_state_id=diagnosis_state_id,
        target_diagnosis_state_id=payload.target_diagnosis_state_id,
        event_ids=payload.event_ids,
        transferred_by=payload.transferred_by,
    )
    return DiagnosisStateTransferResponse(
        diagnosis_state_id=payload.target_diagnosis_state_id,
        transferred_event_ids=transferred_event_ids,
    )
