from app.schemas.common import APIModel, DiagnosisStateStatus


class DiagnosisStateUpdateRequest(APIModel):
    status: DiagnosisStateStatus
    comment: str | None = None


class DiagnosisStateResponse(APIModel):
    id: int
    stac_card_id: int
    diagnosis_id: int
    expert_group_id: int
    status: str


class DiagnosisStateUpdateResponse(APIModel):
    diagnosis_state: DiagnosisStateResponse


class DiagnosisStateTransferRequest(APIModel):
    event_ids: list[int]
    target_diagnosis_state_id: int
    transferred_by: str | None = None


class DiagnosisStateTransferResponse(APIModel):
    diagnosis_state_id: int
    transferred_event_ids: list[int]
