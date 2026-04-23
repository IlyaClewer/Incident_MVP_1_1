from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.diagnosis import DEFAULT_WORKER_DIAGNOSIS_STATUS_ID
from app.db.models.diagnoses import (
    DiagnosisEventDirectory,
    DiagnosisType,
    ExpGroupDiagnosis,
)
from app.db.models.events import Event, EventType
from app.services.is_diagnosis import DiagnosisRule, matched_events

DEFAULT_STATUS_ID = int(DEFAULT_WORKER_DIAGNOSIS_STATUS_ID)


def build_indexes(
    rows: list[tuple[int, int, int | None]],
) -> tuple[dict[int, set[int]], dict[int, dict[int, list[int]]]]:
    mhrn_to_event_nums: dict[int, set[int]] = {}
    mhrn_seq_to_event_ids: dict[int, dict[int, list[int]]] = {}

    for event_id, mh_rn, seq_numb in rows:
        if seq_numb is None:
            continue

        seq = int(seq_numb)
        mhrn_to_event_nums.setdefault(mh_rn, set()).add(seq)
        mhrn_seq_to_event_ids.setdefault(mh_rn, {}).setdefault(seq, []).append(event_id)

    return mhrn_to_event_nums, mhrn_seq_to_event_ids


async def calculate_all_diagnoses_bulk(
    session: AsyncSession,
    default_status_id: int = DEFAULT_STATUS_ID,
) -> dict[int, dict[str, list[dict[str, Any]]]]:
    ev_result = await session.execute(
        select(Event.id, Event.mh_rn, EventType.seq_numb, Event.event_type_id)
        .join(EventType, Event.event_type_id == EventType.id)
    )
    ev_rows_raw: list[tuple[int, int, int | None, int]] = ev_result.all()
    if not ev_rows_raw:
        return {}

    seq_rows = [
        (event_id, mh_rn, seq_numb)
        for event_id, mh_rn, seq_numb, _event_type_id in ev_rows_raw
    ]
    mhrn_to_event_nums, mhrn_seq_to_event_ids = build_indexes(seq_rows)

    mhrn_to_event_type_ids: dict[int, set[int]] = {}
    for _event_id, mh_rn, _seq_numb, event_type_id in ev_rows_raw:
        mhrn_to_event_type_ids.setdefault(mh_rn, set()).add(event_type_id)

    diagnoses = (await session.execute(select(DiagnosisType))).scalars().all()
    if not diagnoses:
        return {}

    rules_by_diag_id: dict[int, DiagnosisRule] = {}
    for diagnosis in diagnoses:
        if not diagnosis.formula:
            continue
        rules_by_diag_id[diagnosis.id] = DiagnosisRule(
            diagnosis.id,
            diagnosis.title,
            diagnosis.formula,
        )
    if not rules_by_diag_id:
        return {}

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

    use_candidates = bool(event_type_to_diag_ids)
    bulk_result: dict[int, dict[str, list[dict[str, Any]]]] = {}

    for mh_rn, active_event_nums in mhrn_to_event_nums.items():
        diagnosis_state_rows: list[dict[str, Any]] = []
        diagnosis_events_state_rows: list[dict[str, Any]] = []
        seq_to_event_ids = mhrn_seq_to_event_ids.get(mh_rn, {})

        if use_candidates:
            candidate_diag_ids: set[int] = set()
            for event_type_id in mhrn_to_event_type_ids.get(mh_rn, set()):
                candidate_diag_ids.update(event_type_to_diag_ids.get(event_type_id, set()))
            rules_iter = (
                rules_by_diag_id[diag_id]
                for diag_id in candidate_diag_ids
                if diag_id in rules_by_diag_id
            )
        else:
            rules_iter = rules_by_diag_id.values()

        for rule in rules_iter:
            assigned_group_ids = sorted(
                diagnosis_to_expert_group_ids.get(rule.diagnosis_id, set())
            )
            if not assigned_group_ids:
                continue

            matched = rule.check(active_event_nums)
            if not matched:
                continue

            matched_nums = matched_events(rule.ast, active_event_nums)
            if not matched_nums:
                continue

            event_ids_for_diag: set[int] = set()
            for seq_num in matched_nums:
                event_ids_for_diag.update(seq_to_event_ids.get(seq_num, []))
            if not event_ids_for_diag:
                continue

            now = datetime.now()
            for experts_group_id in assigned_group_ids:
                diagnosis_state_rows.append(
                    {
                        "experts_group_id": experts_group_id,
                        "mh_rn": mh_rn,
                        "diagnosis_types_id": rule.diagnosis_id,
                        "status_id": default_status_id,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

                for event_id in sorted(event_ids_for_diag):
                    diagnosis_events_state_rows.append(
                        {
                            "experts_group_id": experts_group_id,
                            "diagnosis_types_id": rule.diagnosis_id,
                            "events_id": event_id,
                            "is_transferred": False,
                            "transferred_by": None,
                        }
                    )

        bulk_result[mh_rn] = {
            "diagnosis_state_rows": diagnosis_state_rows,
            "diagnosis_events_state_rows": diagnosis_events_state_rows,
        }

    return bulk_result
