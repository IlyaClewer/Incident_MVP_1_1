from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.diagnosis import DEFAULT_WORKER_DIAGNOSIS_STATUS_ID
from app.db.models.diagnoses import DiagnosisEventDirectory, DiagnosisType, ExpGroupDiagnosis
from app.db.models.events import Event, EventType
from app.services.is_diagnosis import DiagnosisRule, matched_events

DEFAULT_STATUS_ID = int(DEFAULT_WORKER_DIAGNOSIS_STATUS_ID)


async def calculate_diagnoses_for_mhrn(
    session: AsyncSession,
    mh_rn: int,
    default_status_id: int = DEFAULT_STATUS_ID,
) -> dict[str, list[dict[str, Any]]]:
    result = await session.execute(
        select(
            Event.id,
            Event.event_type_id,
            EventType.seq_numb,
        )
        .join(EventType, Event.event_type_id == EventType.id)
        .where(Event.mh_rn == mh_rn)
    )
    rows = result.all()
    if not rows:
        return {
            "diagnosis_state_rows": [],
            "diagnosis_events_state_rows": [],
        }

    active_event_nums: set[int] = set()
    event_num_to_event_ids: dict[int, set[int]] = {}
    event_type_ids: set[int] = set()
    for event_id, event_type_id, seq_numb in rows:
        event_type_ids.add(event_type_id)
        if seq_numb is None:
            continue
        seq_num = int(seq_numb)
        active_event_nums.add(seq_num)
        event_num_to_event_ids.setdefault(seq_num, set()).add(event_id)

    diagnoses = (await session.execute(select(DiagnosisType))).scalars().all()
    directory_rows = (
        await session.execute(
            select(
                DiagnosisEventDirectory.events_type_id,
                DiagnosisEventDirectory.diagnosis_id,
            )
        )
    ).all()
    event_type_to_diag_ids: dict[int, set[int]] = {}
    for events_type_id, diagnosis_id in directory_rows:
        event_type_to_diag_ids.setdefault(events_type_id, set()).add(diagnosis_id)

    candidate_diag_ids: set[int] = set()
    for event_type_id in event_type_ids:
        candidate_diag_ids.update(event_type_to_diag_ids.get(event_type_id, set()))

    diagnosis_group_rows = (
        await session.execute(
            select(
                ExpGroupDiagnosis.diagnosis_type_id,
                ExpGroupDiagnosis.experts_group_id,
            )
        )
    ).all()
    diagnosis_to_expert_group_ids: dict[int, set[int]] = {}
    for diagnosis_type_id, experts_group_id in diagnosis_group_rows:
        diagnosis_to_expert_group_ids.setdefault(diagnosis_type_id, set()).add(experts_group_id)

    diagnosis_state_rows: list[dict[str, Any]] = []
    diagnosis_events_state_rows: list[dict[str, Any]] = []

    for diagnosis in diagnoses:
        if diagnosis.id not in candidate_diag_ids or not diagnosis.formula:
            continue

        assigned_group_ids = sorted(
            diagnosis_to_expert_group_ids.get(diagnosis.id, set())
        )
        if not assigned_group_ids:
            continue

        rule = DiagnosisRule(diagnosis.id, diagnosis.title, diagnosis.formula)
        matched = rule.check(active_event_nums)
        if not matched:
            continue

        matched_nums = matched_events(rule.ast, active_event_nums)
        if not matched_nums:
            continue

        event_ids_for_diag: set[int] = set()
        for seq_num in matched_nums:
            event_ids_for_diag.update(event_num_to_event_ids.get(seq_num, set()))
        if not event_ids_for_diag:
            continue

        for experts_group_id in assigned_group_ids:
            diagnosis_state_rows.append(
                {
                    "experts_group_id": experts_group_id,
                    "mh_rn": mh_rn,
                    "diagnosis_types_id": diagnosis.id,
                    "status_id": default_status_id,
                }
            )
            for event_id in sorted(event_ids_for_diag):
                diagnosis_events_state_rows.append(
                    {
                        "experts_group_id": experts_group_id,
                        "diagnosis_types_id": diagnosis.id,
                        "events_id": event_id,
                        "is_transferred": False,
                        "transferred_by": None,
                    }
                )

    return {
        "diagnosis_state_rows": diagnosis_state_rows,
        "diagnosis_events_state_rows": diagnosis_events_state_rows,
    }
