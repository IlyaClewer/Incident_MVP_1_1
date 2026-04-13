from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DiagnosisStateStatus(StrEnum):
    NEW = "new"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
