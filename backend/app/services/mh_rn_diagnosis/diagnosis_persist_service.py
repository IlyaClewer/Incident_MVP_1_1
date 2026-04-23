from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.diagnoses import DiagnosisEventState, DiagnosisState


async def persist_diagnoses_for_mhrn(
    session: AsyncSession,
    mh_rn: int,
    calc_result: dict[str, list[dict[str, Any]]],
) -> None:
    state_rows = calc_result["diagnosis_state_rows"]
    events_rows = calc_result["diagnosis_events_state_rows"]

    if not state_rows:
        return

    now = datetime.now()
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
        },
    )
    await session.execute(stmt)

    rows = (
        await session.execute(
            select(
                DiagnosisState.id,
                DiagnosisState.experts_group_id,
                DiagnosisState.diagnosis_types_id,
            ).where(DiagnosisState.mh_rn == mh_rn)
        )
    ).all()
    state_id_by_group_and_diag = {
        (experts_group_id, diagnosis_types_id): diagnosis_state_id
        for diagnosis_state_id, experts_group_id, diagnosis_types_id in rows
    }

    state_ids = list(state_id_by_group_and_diag.values())
    if state_ids:
        await session.execute(
            DiagnosisEventState.__table__.delete().where(
                DiagnosisEventState.diagnosis_state_id.in_(state_ids)
            )
        )

    if not events_rows:
        return

    insert_values: list[dict[str, Any]] = []
    for row in events_rows:
        state_id = state_id_by_group_and_diag.get(
            (row["experts_group_id"], row["diagnosis_types_id"])
        )
        if state_id is None:
            continue
        insert_values.append(
            {
                "diagnosis_state_id": state_id,
                "events_id": row["events_id"],
                "is_transferred": row.get("is_transferred", False),
                "transferred_by": row.get("transferred_by"),
            }
        )

    if insert_values:
        await session.execute(pg_insert(DiagnosisEventState).values(insert_values))
