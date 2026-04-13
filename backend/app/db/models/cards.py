from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ForeignKey, Integer, String, Text, SmallInteger, Float, Numeric, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AmbCard(Base):
    __tablename__ = "amb_cards"

    amb_card_number: Mapped[str] = mapped_column(String, primary_key=True)
    patient_name: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)

    external_patient_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    amb_card_rn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    stac_cards: Mapped[list["StacCard"]] = relationship(back_populates="amb_card")


class StacCard(Base):
    __tablename__ = "stac_cards"

    mh_rn: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_numb: Mapped[str | None] = mapped_column(String, nullable=True)
    mht_numb: Mapped[str | None] = mapped_column(String, nullable=True)

    amd_card_numb: Mapped[str | None] = mapped_column(
        ForeignKey("amb_cards.amb_card_number"),
        nullable=True,
    )

    department: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admission_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    daisharge_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    external_patient_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)

    oper_dates: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    oper_timestamp: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    amb_card: Mapped["AmbCard | None"] = relationship(back_populates="stac_cards")
    events: Mapped[list["Event"]] = relationship(back_populates="stac_card")
    diagnosis_states: Mapped[list["DiagnosisState"]] = relationship(back_populates="stac_card")
    exp_group_links: Mapped[list["StacCardExpGroup"]] = relationship(back_populates="stac_card")



class StacExpGroupStatus(Base):
    __tablename__ = "stac_exp_group_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    stac_card_exp_groups: Mapped[list["StacCardExpGroup"]] = relationship(back_populates="status")


class StacCardExpGroup(Base):
    __tablename__ = "stac_cards_exp_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experts_group_id: Mapped[int] = mapped_column(ForeignKey("experts_groups.id"), nullable=False)
    mh_rn: Mapped[int] = mapped_column(ForeignKey("stac_cards.mh_rn"), nullable=False)
    taken_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("experts.id"), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("stac_exp_group_status.id"), nullable=False)
    is_transferred: Mapped[bool | None] = mapped_column(nullable=True)
    transferred_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    experts_group: Mapped["ExpertsGroup"] = relationship(back_populates="stac_card_links")
    stac_card: Mapped["StacCard"] = relationship(back_populates="exp_group_links")
    taken_by_user: Mapped["Expert | None"] = relationship(back_populates="taken_card_links")
    status: Mapped["StacExpGroupStatus"] = relationship(back_populates="stac_card_exp_groups")
