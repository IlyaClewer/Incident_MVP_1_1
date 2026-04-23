from app.schemas.common import APIModel


class ExpertGroupMeta(APIModel):
    id: int
    title: str
    diagnosis_ids: list[int]
    group_diagnosis_ids: list[int] = []
    primary_group_diagnosis_id: int | None = None


class GroupDiagnosisMeta(APIModel):
    id: int
    title: str


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


class ModelResultMeta(APIModel):
    id: int
    stac_card_id: int
    group_diagnosis_id: int | None = None
    group_diagnosis_title: str | None = None
    has_complication: bool
    probability: float | None = None


class MetaResponse(APIModel):
    expert_groups: list[ExpertGroupMeta]
    group_diagnoses: list[GroupDiagnosisMeta] = []
    diagnoses: list[DiagnosisMeta]
    diagnosis_states: list[DiagnosisStateMeta]
    stac_card_diagnosis_index: dict[str, list[int]]
    model_results: list[ModelResultMeta] = []
