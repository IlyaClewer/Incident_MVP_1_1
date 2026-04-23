from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Integer, SmallInteger, String, Text, Float, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RemoteIncPatientMainInfo(Base):
    __tablename__ = "inc_patients_main_info"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amb_card_numb: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_birthday: Mapped[date | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    amb_card_rn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)


class RemoteIncPatientMh(Base):
    __tablename__ = "inc_patients_mh"
    __table_args__ = {"schema": "remote"}

    mh_rn: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_numb: Mapped[str | None] = mapped_column(String, nullable=True)
    mht_numb: Mapped[str | None] = mapped_column(String, nullable=True)
    dep: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admission_date: Mapped[date | None] = mapped_column(nullable=True)
    discharge_date: Mapped[date | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)


class RemoteIncPatientMhExtraInfo(Base):
    __tablename__ = "inc_patients_mh_extra_info"
    __table_args__ = {"schema": "remote"}

    mh_rn: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    oper_date: Mapped[list | None] = mapped_column(ARRAY(TIMESTAMP(timezone=False)), nullable=True)
    hemoglobin_start_value: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    creatinine_start_value: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    transfus_timestamp: Mapped[list | None] = mapped_column(ARRAY(TIMESTAMP(timezone=False)), nullable=True)
    oper_timestamp: Mapped[list | None] = mapped_column(ARRAY(TIMESTAMP(timezone=False)), nullable=True)


class RemoteIncEventsDetailsCategory(Base):
    __tablename__ = "inc_events_details_categories"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    details_table: Mapped[str | None] = mapped_column(String, nullable=True)


class RemoteIncEventType(Base):
    __tablename__ = "inc_events_types"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    short_title: Mapped[str | None] = mapped_column(String, nullable=True)
    details_category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    seq_numb: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RemoteIncEvent(Base):
    __tablename__ = "inc_events"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mh_rn: Mapped[int] = mapped_column(Integer, nullable=False)
    event_timestamp: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)


class RemoteIncGroupDiagnosis(Base):
    __tablename__ = "inc_group_diagnosis"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)


class RemoteIncForModel(Base):
    __tablename__ = "inc_for_model"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mh_rn: Mapped[int] = mapped_column(Integer, nullable=False)
    group_diagnosis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_complication: Mapped[bool] = mapped_column(Boolean, nullable=False)
    probability: Mapped[float | None] = mapped_column(Numeric, nullable=True)


class FullEvent(Base):
    __tablename__ = "inc_v_events_with_details"
    __table_args__ = {"schema": "remote"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mh_rn: Mapped[int] = mapped_column(Integer, nullable=False)
    event_timestamp: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    details: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)


RemoteIncVEventsWithDetails = FullEvent
