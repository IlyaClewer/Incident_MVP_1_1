from app.schemas.common import APIModel


class ExpertGroupCatalogItem(APIModel):
    id: int
    title: str
    diagnosis_ids: list[int]


class ExpertGroupCreate(APIModel):
    title: str
    diagnosis_ids: list[int] = []


class ExpertGroupUpdate(APIModel):
    title: str | None = None
    diagnosis_ids: list[int] | None = None


class DiagnosisTypeCatalogItem(APIModel):
    id: int
    title: str
    formula: str | None = None
    event_type_ids: list[int]
    expert_group_ids: list[int]


class DiagnosisTypeCreate(APIModel):
    title: str
    formula: str | None = None
    event_type_ids: list[int] = []
    expert_group_ids: list[int] = []


class DiagnosisTypeUpdate(APIModel):
    title: str | None = None
    formula: str | None = None
    event_type_ids: list[int] | None = None
    expert_group_ids: list[int] | None = None


class EventTypeCatalogItem(APIModel):
    id: int
    details_category_id: int
    events_class_id: int
    short_title: str
    title: str
    category: int | None = None
    query: str | None = None
    active: bool | None = None
    seq_numb: int | None = None


class EventTypeCreate(APIModel):
    details_category_id: int
    events_class_id: int
    short_title: str
    title: str
    category: int | None = None
    query: str | None = None
    active: bool | None = None
    seq_numb: int | None = None


class EventTypeUpdate(APIModel):
    details_category_id: int | None = None
    events_class_id: int | None = None
    short_title: str | None = None
    title: str | None = None
    category: int | None = None
    query: str | None = None
    active: bool | None = None
    seq_numb: int | None = None
