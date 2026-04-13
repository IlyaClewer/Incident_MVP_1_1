from datetime import date

from pydantic import Field

from app.schemas.common import APIModel


class EventDetailField(APIModel):
    key: str
    label: str
    value: str
    order: int = 0


class StacCardEventItem(APIModel):
    id: int
    event_type_id: int
    date_trigger: date | None = None
    trigger: str
    event_ids: list[int]
    diagnosis_state_ids: list[int]
    details: list[EventDetailField] = Field(default_factory=list)


class StacCardEventsResponse(APIModel):
    events: list[StacCardEventItem]
