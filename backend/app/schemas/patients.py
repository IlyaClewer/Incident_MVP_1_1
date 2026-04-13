from datetime import date

from app.schemas.common import APIModel


class StacCardSummary(APIModel):
    id: int
    amb_card_num: str | None = None
    cardNumber: str | None = None
    department: int | None = None
    date_hosp: date | None = None
    date_operation: date | None = None
    date_discharge: date | None = None
    status: str = "new"


class PatientSummary(APIModel):
    amb_card_num: str | None = None
    patientName: str | None = None
    birthDate: date | None = None
    stac_cards: list[StacCardSummary]


class PatientsResponse(APIModel):
    patients: list[PatientSummary]
