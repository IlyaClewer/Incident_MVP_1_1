from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Expert(Base):
    __tablename__ = "experts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ad_username: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True, default="expert")
    last_login: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    sessions: Mapped[list["Session"]] = relationship(back_populates="expert")
    group_links: Mapped[list["ExpertExpGroup"]] = relationship(back_populates="expert")
    logs: Mapped[list["Log"]] = relationship(back_populates="expert")
    taken_card_links: Mapped[list["StacCardExpGroup"]] = relationship(back_populates="taken_by_user")


class ExpertsGroup(Base):
    __tablename__ = "experts_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    group_diagnosis_id: Mapped[int | None] = mapped_column(
        ForeignKey("group_diagnosis.id"),
        nullable=True,
    )

    expert_links: Mapped[list["ExpertExpGroup"]] = relationship(back_populates="experts_group")
    diagnosis_states: Mapped[list["DiagnosisState"]] = relationship(back_populates="experts_group")
    diagnosis_links: Mapped[list["ExpGroupDiagnosis"]] = relationship(back_populates="experts_group")
    diagnosis_group_links: Mapped[list["ExpGroupGroupDiagnosis"]] = relationship(
        back_populates="experts_group"
    )
    primary_group_diagnosis: Mapped["GroupDiagnosis | None"] = relationship(
        back_populates="primary_expert_groups",
        foreign_keys=[group_diagnosis_id],
    )
    stac_card_links: Mapped[list["StacCardExpGroup"]] = relationship(back_populates="experts_group")
    logs: Mapped[list["Log"]] = relationship(back_populates="experts_group")


class ExpertExpGroup(Base):
    __tablename__ = "expert_exp_groups"
    __table_args__ = (
        UniqueConstraint("experts_group_id", "expert_id", name="uq_expert_exp_groups_group_expert"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experts_group_id: Mapped[int] = mapped_column(ForeignKey("experts_groups.id"), nullable=False)
    expert_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("experts.id"), nullable=False)

    experts_group: Mapped["ExpertsGroup"] = relationship(back_populates="expert_links")
    expert: Mapped["Expert"] = relationship(back_populates="group_links")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    expert_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("experts.id"), nullable=True)
    session_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    device_info: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    expert: Mapped["Expert | None"] = relationship(back_populates="sessions")
