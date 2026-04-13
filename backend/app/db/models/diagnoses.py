from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiagnosisType(Base):
    __tablename__ = "diagnosis_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)

    diagnosis_states: Mapped[list["DiagnosisState"]] = relationship(back_populates="diagnosis_type")
    event_directory_links: Mapped[list["DiagnosisEventDirectory"]] = relationship(back_populates="diagnosis")
    exp_group_links: Mapped[list["ExpGroupDiagnosis"]] = relationship(back_populates="diagnosis_type")


class DiagnosisStateStatus(Base):
    __tablename__ = "diagnosis_state_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    diagnosis_states: Mapped[list["DiagnosisState"]] = relationship(back_populates="status")


class DiagnosisState(Base):
    __tablename__ = "diagnosis_state"
    __table_args__ = (
        UniqueConstraint("mh_rn", "experts_group_id", "diagnosis_types_id", name="uk_diagnosis_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experts_group_id: Mapped[int] = mapped_column(ForeignKey("experts_groups.id"), nullable=False)
    mh_rn: Mapped[int] = mapped_column(ForeignKey("stac_cards.mh_rn"), nullable=False)
    diagnosis_types_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_types.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_state_status.id"), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    experts_group: Mapped["ExpertsGroup"] = relationship(back_populates="diagnosis_states")
    stac_card: Mapped["StacCard"] = relationship(back_populates="diagnosis_states")
    diagnosis_type: Mapped["DiagnosisType"] = relationship(back_populates="diagnosis_states")
    status: Mapped["DiagnosisStateStatus"] = relationship(back_populates="diagnosis_states")
    event_states: Mapped[list["DiagnosisEventState"]] = relationship(back_populates="diagnosis_state")


class DiagnosisEventState(Base):
    __tablename__ = "diagnosis_events_state"
    __table_args__ = (
        UniqueConstraint("diagnosis_state_id", "events_id", name="uk_diagnosis_events_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagnosis_state_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_state.id"), nullable=False)
    events_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    is_transferred: Mapped[bool | None] = mapped_column(nullable=True)
    transferred_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    diagnosis_state: Mapped["DiagnosisState"] = relationship(back_populates="event_states")
    event: Mapped["Event"] = relationship(back_populates="diagnosis_event_states")


class DiagnosisEventDirectory(Base):
    __tablename__ = "diagnosis_events_directory"
    __table_args__ = (
        UniqueConstraint(
            "events_type_id",
            "diagnosis_id",
            name="uq_diagnosis_events_directory_event_diagnosis",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    events_type_id: Mapped[int] = mapped_column(
        ForeignKey("events_types.id"),
        nullable=False,
    )
    diagnosis_id: Mapped[int] = mapped_column(
        ForeignKey("diagnosis_types.id"),
        nullable=False,
    )

    event_type: Mapped["EventType"] = relationship(back_populates="diagnosis_links")
    diagnosis: Mapped["DiagnosisType"] = relationship(back_populates="event_directory_links")


class ExpGroupDiagnosis(Base):
    __tablename__ = "exp_groups_diagnosis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experts_group_id: Mapped[int] = mapped_column(ForeignKey("experts_groups.id"), nullable=False)
    diagnosis_type_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_types.id"), nullable=False)

    experts_group: Mapped["ExpertsGroup"] = relationship(back_populates="diagnosis_links")
    diagnosis_type: Mapped["DiagnosisType"] = relationship(back_populates="exp_group_links")
