from __future__ import annotations

from typing import Dict, Any, List, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.diagnosis import DEFAULT_WORKER_DIAGNOSIS_STATUS_ID
from app.db.models.events import Event, EventType
from app.db.models.diagnoses import DiagnosisType, DiagnosisEventDirectory
from app.services.is_diagnosis import DiagnosisRule, matched_events
from datetime import datetime

DEFAULT_EXPERTS_GROUP_ID = 1
DEFAULT_STATUS_ID = int(DEFAULT_WORKER_DIAGNOSIS_STATUS_ID)


def build_indexes(
    rows: List[Tuple[int, int, int | None]],
) -> tuple[Dict[int, Set[int]], Dict[int, Dict[int, List[int]]]]:
    """
    rows: список (event_id, mh_rn, seq_numb)

    Возвращает два индекса:
      1) mhrn_to_event_nums: { mh_rn: {seq_numb1, seq_numb2, ...} }
      2) mhrn_seq_to_event_ids: { mh_rn: { seq_numb: [event_id1, event_id2, ...] } }
    """
    mhrn_to_event_nums: Dict[int, Set[int]] = {}
    mhrn_seq_to_event_ids: Dict[int, Dict[int, List[int]]] = {}

    for event_id, mh_rn, seq_numb in rows:
        if seq_numb is None:
            continue
        seq = int(seq_numb)

        nums_bucket = mhrn_to_event_nums.get(mh_rn)
        if nums_bucket is None:
            nums_bucket = set()
            mhrn_to_event_nums[mh_rn] = nums_bucket
        nums_bucket.add(seq)

        seq_map = mhrn_seq_to_event_ids.get(mh_rn)
        if seq_map is None:
            seq_map = {}
            mhrn_seq_to_event_ids[mh_rn] = seq_map
        ev_list = seq_map.get(seq)
        if ev_list is None:
            ev_list = []
            seq_map[seq] = ev_list
        ev_list.append(event_id)

    return mhrn_to_event_nums, mhrn_seq_to_event_ids


async def calculate_all_diagnoses_bulk(
    session: AsyncSession,
    experts_group_id: int = DEFAULT_EXPERTS_GROUP_ID,
    default_status_id: int = DEFAULT_STATUS_ID,
) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
    """
    1) Одним запросом забирает все события + seq_numb.
    2) Строит в памяти "json" по mh_rn: какие номера событий есть и какие events.id им соответствуют.
    3) Загружает диагнозы и формирует правила DiagnosisRule.
    4) Загружает diagnosis_events_directory и строит индекс event_type_id -> set[diagnosis_id].
    5) Для каждого mh_rn сначала собирает список кандидатных диагнозов по его типам событий,
       а потом прогоняет алгоритм is_diagnosis только по этим кандидатам.
    6) Формирует заготовки для diagnosis_state и diagnosis_events_state.

    Возвращает:
      {
        mh_rn1: {
          "diagnosis_state_rows": [...],
          "diagnosis_events_state_rows": [...],
        },
        mh_rn2: { ... },
        ...
      }
    """
    # 1. Забираем все события и seq_numb одним запросом
    ev_result = await session.execute(
        select(Event.id, Event.mh_rn, EventType.seq_numb, Event.event_type_id)
        .join(EventType, Event.event_type_id == EventType.id)
    )
    ev_rows_raw: List[Tuple[int, int, int | None, int]] = ev_result.all()

    if not ev_rows_raw:
        return {}

    # Выделяем часть для индексов по seq_numb
    seq_rows: List[Tuple[int, int, int | None]] = [
        (event_id, mh_rn, seq_numb)
        for (event_id, mh_rn, seq_numb, _event_type_id) in ev_rows_raw
    ]

    # 2. Строим индексы по mh_rn и seq_numb
    mhrn_to_event_nums, mhrn_seq_to_event_ids = build_indexes(seq_rows)

    # 2b. Строим индекс mh_rn -> множество event_type_id (для diagnosis_events_directory)
    mhrn_to_event_type_ids: Dict[int, Set[int]] = {}
    for event_id, mh_rn, seq_numb, event_type_id in ev_rows_raw:
        bucket = mhrn_to_event_type_ids.get(mh_rn)
        if bucket is None:
            bucket = set()
            mhrn_to_event_type_ids[mh_rn] = bucket
        bucket.add(event_type_id)

    # 3. Грузим все диагнозы и создаём правила
    diag_result = await session.execute(select(DiagnosisType))
    diagnoses = diag_result.scalars().all()
    if not diagnoses:
        return {}

    rules_by_diag_id: Dict[int, DiagnosisRule] = {}
    for diag in diagnoses:
        if not diag.formula:
            continue
        rules_by_diag_id[diag.id] = DiagnosisRule(diag.id, diag.title, diag.formula)

    if not rules_by_diag_id:
        return {}

    # 4. Грузим diagnosis_events_directory и строим индекс event_type_id -> set[diagnosis_id]
    dir_result = await session.execute(
        select(DiagnosisEventDirectory.events_type_id, DiagnosisEventDirectory.diagnosis_id)
    )
    dir_rows = dir_result.all()

    event_type_to_diag_ids: Dict[int, Set[int]] = {}
    for events_type_id, diagnosis_id in dir_rows:
        bucket = event_type_to_diag_ids.get(events_type_id)
        if bucket is None:
            bucket = set()
            event_type_to_diag_ids[events_type_id] = bucket
        bucket.add(diagnosis_id)

    # Если по какой-то причине индекс пустой, откатываемся к полному перебору
    use_candidates = bool(event_type_to_diag_ids)

    # 5. Прогоняем по всем mh_rn
    bulk_result: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}

    for mh_rn, active_event_nums in mhrn_to_event_nums.items():
        diagnosis_state_rows: List[Dict[str, Any]] = []
        diagnosis_events_state_rows: List[Dict[str, Any]] = []

        seq_to_event_ids = mhrn_seq_to_event_ids.get(mh_rn, {})

        # 5a. Определяем список кандидатных диагнозов по типам событий карты
        if use_candidates:
            candidate_diag_ids: Set[int] = set()
            for event_type_id in mhrn_to_event_type_ids.get(mh_rn, set()):
                diag_ids = event_type_to_diag_ids.get(event_type_id)
                if not diag_ids:
                    continue
                candidate_diag_ids.update(diag_ids)
            # переводим в набор правил
            rules_iter = (
                rules_by_diag_id[diag_id]
                for diag_id in candidate_diag_ids
                if diag_id in rules_by_diag_id
            )
        else:
            # fallback: все правила
            rules_iter = rules_by_diag_id.values()

        # 5b. Применяем движок только к кандидатам
        for rule in rules_iter:
            matched = rule.check(active_event_nums)
            if not matched:
                continue

            matched_nums = matched_events(rule.ast, active_event_nums)
            if not matched_nums:
                continue

            # Собираем реальные events.id по этим номерам
            event_ids_for_diag: Set[int] = set()
            for num in matched_nums:
                ids_for_num = seq_to_event_ids.get(num)
                if not ids_for_num:
                    continue
                event_ids_for_diag.update(ids_for_num)

            if not event_ids_for_diag:
                continue

            now = datetime.now()
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

            for eid in sorted(event_ids_for_diag):
                diagnosis_events_state_rows.append(
                    {
                        "diagnosis_types_id": rule.diagnosis_id,
                        "events_id": eid,
                        "is_transferred": False,
                        "transferred_by": None,
                    }
                )

        bulk_result[mh_rn] = {
            "diagnosis_state_rows": diagnosis_state_rows,
            "diagnosis_events_state_rows": diagnosis_events_state_rows,
        }

    return bulk_result
