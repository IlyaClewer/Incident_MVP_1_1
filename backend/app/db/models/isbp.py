from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IsbpIncident(Base):
    __tablename__ = "isbp_incidents"
    __table_args__ = (
        UniqueConstraint("diagnosis_state_id", name="uq_isbp_incidents_diagnosis_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagnosis_state_id: Mapped[int] = mapped_column(
        ForeignKey("diagnosis_state.id"),
        nullable=False,
    )
    mh_rn: Mapped[int] = mapped_column(ForeignKey("stac_cards.mh_rn"), nullable=False)
    experts_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("experts_groups.id"),
        nullable=True,
    )
    expert_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("experts.id"),
        nullable=True,
    )
    isbp_incident_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_request_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    create_response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_status_response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    diagnosis_state: Mapped["DiagnosisState"] = relationship()
    stac_card: Mapped["StacCard"] = relationship()
    experts_group: Mapped["ExpertsGroup | None"] = relationship()
    expert: Mapped["Expert | None"] = relationship()

