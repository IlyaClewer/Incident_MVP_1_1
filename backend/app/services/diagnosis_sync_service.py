from __future__ import annotations

import re
from typing import Set

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.diagnoses import DiagnosisType, DiagnosisEventDirectory
from app.db.models.events import EventType
from app.services.is_diagnosis import normalize_formula  # normalize/tokenize


def extract_event_ids(formula: str) -> Set[int]:
    normalized = normalize_formula(formula or "")
    return {int(x) for x in re.findall(r"\d+", normalized)}


class DiagnosisSyncService:
    @staticmethod
    async def sync_diagnosis_events_directory(session: AsyncSession) -> None:
        # 1. грузим все диагнозы
        result = await session.execute(select(DiagnosisType))
        diagnoses = result.scalars().all()
        if not diagnoses:
            return

        # 2. грузим все типы событий (id, seq_numb) в память
        ev_result = await session.execute(select(EventType.id, EventType.seq_numb))
        ev_rows = ev_result.all()
        seq_to_event_id = {
            seq: ev_id for ev_id, seq in ev_rows if seq is not None
        }

        if not seq_to_event_id:
            return

        total_links = 0

        for diag in diagnoses:
            # полная очистка индекса для конкретного диагноза
            await session.execute(
                DiagnosisEventDirectory.__table__.delete().where(
                    DiagnosisEventDirectory.diagnosis_id == diag.id
                )
            )

            if not diag.formula:
                continue

            event_nums = extract_event_ids(diag.formula)
            if not event_nums:
                continue

            values = []
            for n in event_nums:
                events_type_id = seq_to_event_id.get(n)
                if events_type_id is None:
                    # нет такого события с таким seq_numb — пропускаем
                    continue
                values.append(
                    {
                        "events_type_id": events_type_id,
                        "diagnosis_id": diag.id,
                    }
                )

            if not values:
                continue

            stmt = pg_insert(DiagnosisEventDirectory).values(values)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[
                    DiagnosisEventDirectory.events_type_id,
                    DiagnosisEventDirectory.diagnosis_id,
                ]
            )
            await session.execute(stmt)
            total_links += len(values)

        # total_links можно залогировать снаружи
