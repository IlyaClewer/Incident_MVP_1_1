from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, TypeVar, List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cards import AmbCard, StacCard
from app.db.models.events import Event, EventType, EventDetailsCategory
from app.db.models.remote import (
    RemoteIncPatientMainInfo,
    RemoteIncPatientMh,
    RemoteIncPatientMhExtraInfo,
    RemoteIncEvent,
    RemoteIncEventsDetailsCategory,
    RemoteIncEventType,
)

T = TypeVar("T")

BATCH_SIZE = 500  # при необходимости можно подстроить


def chunked(seq: List[T], size: int) -> Iterable[List[T]]:
    if not seq:
        return
    for i in range(0, len(seq), size):
        chunk = seq[i : i + size]
        if chunk:
            yield chunk


def _serialize_ts_list(values: list | None) -> list | None:
    if values is None:
        return None
    out: list[str] = []
    for v in values:
        if isinstance(v, (datetime, date)):
            out.append(v.isoformat())
        else:
            out.append(str(v))
    return out


class SyncService:
    # ------------------------------------------------------------------
    # amb_cards <- remote.inc_patients_main_info
    # ------------------------------------------------------------------
    @staticmethod
    async def sync_amb_cards(session: AsyncSession) -> None:
        result = await session.execute(
            select(RemoteIncPatientMainInfo).where(
                RemoteIncPatientMainInfo.amb_card_numb.isnot(None)
            )
        )
        rows = result.scalars().all()

        if not rows:
            return

        for chunk in chunked(rows, BATCH_SIZE):
            stmt = pg_insert(AmbCard).values([
                {
                    "amb_card_number": r.amb_card_numb,
                    "patient_name": r.patient_name or "",
                    "birth_date": r.patient_birthday,
                    "external_patient_id": r.id,
                    "amb_card_rn": r.amb_card_rn,
                    "sex": r.sex,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in chunk
            ])
            stmt = stmt.on_conflict_do_update(
                index_elements=[AmbCard.amb_card_number],
                set_={
                    "patient_name": stmt.excluded.patient_name,
                    "birth_date": stmt.excluded.birth_date,
                    "external_patient_id": stmt.excluded.external_patient_id,
                    "amb_card_rn": stmt.excluded.amb_card_rn,
                    "sex": stmt.excluded.sex,
                    "created_at": stmt.excluded.created_at,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            await session.execute(stmt)

    # ------------------------------------------------------------------
    # stac_cards <- remote.inc_patients_mh + extra_info + main_info
    # ------------------------------------------------------------------
    @staticmethod
    async def sync_stac_cards(session: AsyncSession) -> None:
        mh_result = await session.execute(select(RemoteIncPatientMh))
        mh_rows = mh_result.scalars().all()

        if not mh_rows:
            return

        # extra с датами операций
        extra_result = await session.execute(select(RemoteIncPatientMhExtraInfo))
        extra_map: dict[int, RemoteIncPatientMhExtraInfo] = {
            r.mh_rn: r for r in extra_result.scalars().all()
        }

        # main info для связи с амбулаторной картой
        patient_result = await session.execute(select(RemoteIncPatientMainInfo))
        patient_map: dict[int, RemoteIncPatientMainInfo] = {
            r.id: r for r in patient_result.scalars().all()
        }

        all_values: list[dict] = []
        for mh in mh_rows:
            extra = extra_map.get(mh.mh_rn)
            patient = patient_map.get(mh.patient_id) if mh.patient_id else None

            oper_dates = _serialize_ts_list(extra.oper_date) if extra else None
            oper_ts = _serialize_ts_list(extra.oper_timestamp) if extra else None

            all_values.append({
                "mh_rn": mh.mh_rn,
                "card_numb": mh.card_numb,
                "mht_numb": mh.mht_numb,
                "amd_card_numb": patient.amb_card_numb if patient else None,
                "department": mh.dep,
                "admission_date": mh.admission_date,
                "daisharge_date": mh.discharge_date,
                "created_at": mh.created_at,
                "external_patient_id": mh.patient_id,
                "updated_at": mh.updated_at,
                "weight": mh.weight,
                "height": mh.height,
                "oper_dates": oper_dates,
                "oper_timestamp": oper_ts,
            })

        if not all_values:
            return

        for chunk in chunked(all_values, BATCH_SIZE):
            stmt = pg_insert(StacCard).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=[StacCard.mh_rn],
                set_={
                    "card_numb": stmt.excluded.card_numb,
                    "mht_numb": stmt.excluded.mht_numb,
                    "amd_card_numb": stmt.excluded.amd_card_numb,
                    "department": stmt.excluded.department,
                    "admission_date": stmt.excluded.admission_date,
                    "daisharge_date": stmt.excluded.daisharge_date,
                    "created_at": stmt.excluded.created_at,
                    "external_patient_id": stmt.excluded.external_patient_id,
                    "updated_at": stmt.excluded.updated_at,
                    "weight": stmt.excluded.weight,
                    "height": stmt.excluded.height,
                    "oper_dates": stmt.excluded.oper_dates,
                    "oper_timestamp": stmt.excluded.oper_timestamp,
                },
            )
            await session.execute(stmt)

    # ------------------------------------------------------------------
    # events_details_categories <- remote.inc_events_details_categories
    # ------------------------------------------------------------------
    @staticmethod
    async def sync_event_details_categories(session: AsyncSession) -> None:
        result = await session.execute(select(RemoteIncEventsDetailsCategory))
        rows = result.scalars().all()

        if not rows:
            return

        stmt = pg_insert(EventDetailsCategory).values([
            {
                "id": r.id,
                "title": r.title or "",
                "details_table": r.details_table or "",
            }
            for r in rows
        ])
        stmt = stmt.on_conflict_do_update(
            index_elements=[EventDetailsCategory.id],
            set_={
                "title": stmt.excluded.title,
                "details_table": stmt.excluded.details_table,
            },
        )
        await session.execute(stmt)

    # ------------------------------------------------------------------
    # events_types <- remote.inc_events_types
    # ------------------------------------------------------------------
    @staticmethod
    async def sync_event_types(session: AsyncSession, default_events_class_id: int) -> None:
        result = await session.execute(select(RemoteIncEventType))
        rows = result.scalars().all()

        if not rows:
            return

        # все текущие типы, чтобы понять, какие уже существуют
        existing_result = await session.execute(select(EventType))
        existing: dict[int, int] = {
            row.id: row.events_class_id for row in existing_result.scalars().all()
        }

        ORIGINAL_CLASS_ID = 1  # твой "Оригинальное"

        values = []
        for r in rows:
            if r.details_category_id is None:
                continue

            if r.id in existing:
                # тип уже есть — сохраняем текущий класс
                events_class_id = existing[r.id]
            else:
                # новый тип — всегда "Оригинальное"
                events_class_id = ORIGINAL_CLASS_ID

            values.append({
                "id": r.id,
                "details_category_id": r.details_category_id,
                "events_class_id": events_class_id,
                "short_title": r.short_title or "",
                "title": r.title or "",
                "category": r.category,
                "query": r.query,
                "active": r.active,
                "seq_numb": r.seq_numb,
            })

        if not values:
            return

        stmt = pg_insert(EventType).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[EventType.id],
            set_={
                "details_category_id": stmt.excluded.details_category_id,
                "short_title": stmt.excluded.short_title,
                "title": stmt.excluded.title,
                "category": stmt.excluded.category,
                "query": stmt.excluded.query,
                "active": stmt.excluded.active,
                "seq_numb": stmt.excluded.seq_numb,
                # ВАЖНО: events_class_id здесь НЕ трогаем,
                # чтобы не затирать уже вручную изменённые классы.
            },
        )
        await session.execute(stmt)

    # ------------------------------------------------------------------
    # events <- remote.inc_events
    # ------------------------------------------------------------------
    @staticmethod
    async def sync_events(session: AsyncSession) -> None:
        result = await session.execute(select(RemoteIncEvent))
        rows = result.scalars().all()

        if not rows:
            return

        for chunk in chunked(rows, BATCH_SIZE):
            stmt = pg_insert(Event).values([
                {
                    "id": r.id,
                    "event_type_id": r.event_type_id,
                    "mh_rn": r.mh_rn,
                    "event_timestamp": r.event_timestamp,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in chunk
            ])
            stmt = stmt.on_conflict_do_update(
                index_elements=[Event.id],
                set_={
                    "event_type_id": stmt.excluded.event_type_id,
                    "mh_rn": stmt.excluded.mh_rn,
                    "event_timestamp": stmt.excluded.event_timestamp,
                    "created_at": stmt.excluded.created_at,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            await session.execute(stmt)

    # ------------------------------------------------------------------
    # Полный прогон
    # ------------------------------------------------------------------
    @classmethod
    async def run_full_sync(cls, session: AsyncSession, default_events_class_id: int = 1) -> None:
        try:
            await cls.sync_amb_cards(session)
            await cls.sync_stac_cards(session)
            await cls.sync_event_details_categories(session)
            await cls.sync_event_types(session, default_events_class_id)
            await cls.sync_events(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
