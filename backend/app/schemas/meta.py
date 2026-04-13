from app.schemas.common import APIModel


class ExpertGroupMeta(APIModel):
    id: int
    title: str
    diagnosis_ids: list[int]


class DiagnosisMeta(APIModel):
    id: int
    name: str
    description: str | None = None
    stac_card_ids: list[int]
    formulas: list[str]
    event_type_ids: list[int]


class DiagnosisStateMeta(APIModel):
    id: int
    stac_card_id: int
    diagnosis_id: int
    expert_group_id: int
    status: str


class MetaResponse(APIModel):
    expert_groups: list[ExpertGroupMeta]
    diagnoses: list[DiagnosisMeta]
    diagnosis_states: list[DiagnosisStateMeta]
    stac_card_diagnosis_index: dict[str, list[int]]
