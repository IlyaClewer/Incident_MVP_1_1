from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventClass(Base):
    __tablename__ = "events_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    event_types: Mapped[list["EventType"]] = relationship(back_populates="event_class")


class EventDetailsCategory(Base):
    __tablename__ = "events_details_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    details_table: Mapped[str] = mapped_column(Text, nullable=False)

    event_types: Mapped[list["EventType"]] = relationship(back_populates="details_category")


class EventType(Base):
    __tablename__ = "events_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    details_category_id: Mapped[int] = mapped_column(
        ForeignKey("events_details_categories.id"),
        nullable=False,
    )
    events_class_id: Mapped[int] = mapped_column(
        ForeignKey("events_class.id"),
        nullable=False,
    )
    short_title: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    seq_numb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    details_category: Mapped["EventDetailsCategory"] = relationship(back_populates="event_types")
    event_class: Mapped["EventClass"] = relationship(back_populates="event_types")
    events: Mapped[list["Event"]] = relationship(back_populates="event_type")
    diagnosis_links: Mapped[list["DiagnosisEventDirectory"]] = relationship(back_populates="event_type")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type_id: Mapped[int] = mapped_column(ForeignKey("events_types.id"), nullable=False)
    mh_rn: Mapped[int] = mapped_column(ForeignKey("stac_cards.mh_rn"), nullable=False)

    event_timestamp: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    event_type: Mapped["EventType"] = relationship(back_populates="events")
    stac_card: Mapped["StacCard"] = relationship(back_populates="events")
    diagnosis_event_states: Mapped[list["DiagnosisEventState"]] = relationship(back_populates="event")
