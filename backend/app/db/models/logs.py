from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID, TIMESTAMP


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    action: Mapped[str | None] = mapped_column(Text, nullable=True)
    expert_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("experts.id"), nullable=True)
    experts_group_id: Mapped[int | None] = mapped_column(ForeignKey("experts_groups.id"), nullable=True)
    mh_rn: Mapped[int | None] = mapped_column(ForeignKey("stac_cards.mh_rn"), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    expert: Mapped["Expert | None"] = relationship(back_populates="logs")
    experts_group: Mapped["ExpertsGroup | None"] = relationship(back_populates="logs")
