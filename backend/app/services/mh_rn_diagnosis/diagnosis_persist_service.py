from __future__ import annotations

from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.diagnoses import DiagnosisState, DiagnosisEventState
from datetime import datetime

async def persist_diagnoses_for_mhrn(
    session: AsyncSession,
    mh_rn: int,
    calc_result: Dict[str, List[Dict[str, Any]]],
    experts_group_id: int,
) -> None:
    """
    Принимает результат calculate_diagnoses_for_mhrn и
    делает UPSERT в diagnosis_state + полную перезапись diagnosis_events_state
    для данного mh_rn + experts_group_id.
    """
    state_rows = calc_result["diagnosis_state_rows"]
    events_rows = calc_result["diagnosis_events_state_rows"]

    if not state_rows:
        # пока ничего не делаем, позже можно добавить снятие диагнозов
        return

    # 1. UPSERT diagnosis_state по (mh_rn, experts_group_id, diagnosis_types_id)
    #    и собрать map (diagnosis_types_id -> diagnosis_state.id)
    now=datetime.now()
    stmt = pg_insert(DiagnosisState).values(state_rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            DiagnosisState.mh_rn,
            DiagnosisState.experts_group_id,
            DiagnosisState.diagnosis_types_id,
        ],
        set_={
            "status_id": stmt.excluded.status_id,
            "updated_at": now,
            # created_at/updated_at пусть триггеры/ORM обновляют, если есть
        },
    )
    await session.execute(stmt)

    # вытащить актуальные id после UPSERT
    q = select(DiagnosisState.id, DiagnosisState.diagnosis_types_id).where(
        DiagnosisState.mh_rn == mh_rn,
        DiagnosisState.experts_group_id == experts_group_id,
    )
    res = await session.execute(q)
    rows = res.all()
    diag_type_to_state_id = {dt_id: ds_id for ds_id, dt_id in rows}

    if not events_rows:
        return

    # 2. Полная перезапись diagnosis_events_state для этих состояний
    state_ids = list(diag_type_to_state_id.values())
    await session.execute(
        DiagnosisEventState.__table__.delete().where(
            DiagnosisEventState.diagnosis_state_id.in_(state_ids)
        )
    )

    insert_values: List[Dict[str, Any]] = []
    for r in events_rows:
        state_id = diag_type_to_state_id.get(r["diagnosis_types_id"])
        if state_id is None:
            continue
        insert_values.append({
            "diagnosis_state_id": state_id,
            "events_id": r["events_id"],
            "is_transferred": r.get("is_transferred", False),
            "transferred_by": r.get("transferred_by"),
        })

    if not insert_values:
        return

    stmt2 = pg_insert(DiagnosisEventState).values(insert_values)
    await session.execute(stmt2)
