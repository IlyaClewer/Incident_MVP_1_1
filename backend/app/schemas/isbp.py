from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from app.schemas.common import APIModel


class IsbpStatus(StrEnum):
    CREATED_DRAFT = "CREATED_DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    NOT_FOUND = "NOT_FOUND"


class IsbpDiagnosisPayload(APIModel):
    id: int
    title: str
    status: str


class IsbpPatientPayload(APIModel):
    amb_card_number: str | None = None
    external_patient_id: int | None = None
    patient_name: str
    birth_date: date | None = None
    sex: int | None = None


class IsbpStacCardPayload(APIModel):
    card_number: str | None = None
    mht_numb: str | None = None
    department: int | None = None
    admission_date: datetime | None = None
    discharge_date: datetime | None = None
    weight: float | None = None
    height: float | None = None


class IsbpUserPayload(APIModel):
    id: int | str
    ad_username: str | None = None
    display_name: str


class IsbpEventPayload(APIModel):
    id: int
    event_type_id: int
    event_type_title: str | None = None
    event_type_short_title: str | None = None
    event_timestamp: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IsbpCreateIncidentRequest(APIModel):
    mh_rn: int
    diagnosis_state_id: int
    comment: str
    diagnosis: IsbpDiagnosisPayload
    patient: IsbpPatientPayload
    stac_card: IsbpStacCardPayload
    user: IsbpUserPayload
    events: list[IsbpEventPayload]


class IsbpCreateIncidentResponse(APIModel):
    success: bool
    status: str
    message: str | None = None
    mh_rn: int | None = None
    diagnosis_state_id: int | None = None
    isbp_incident_id: str | None = None
    error_code: str | None = None


class IsbpIncidentStatusResponse(APIModel):
    success: bool
    status: str
    message: str | None = None
    mh_rn: int | None = None
    diagnosis_state_id: int | None = None
    isbp_incident_id: str | None = None
    confirmed_at: datetime | None = None
    error_code: str | None = None


class IsbpPollTarget(APIModel):
    mh_rn: int
    diagnosis_state_id: int
    isbp_incident_id: str | None = None
    last_status: str | None = None

