from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.events import StacCardEventsResponse
from app.services.patients_service import PatientsService

router = APIRouter(tags=["stac-cards"])


@router.get("/stac-cards/{stac_card_id}/events", response_model=StacCardEventsResponse)
async def get_stac_card_events(
    stac_card_id: int,
    db: AsyncSession = Depends(get_db),
) -> StacCardEventsResponse:
    events = await PatientsService.list_stac_card_events(db, stac_card_id)
    return StacCardEventsResponse(events=events)
