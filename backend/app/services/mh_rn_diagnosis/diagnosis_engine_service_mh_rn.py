from typing import List, Dict, Any, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.is_diagnosis import DiagnosisRule, matched_events
from app.db.models.events import Event, EventType
from app.db.models.diagnoses import DiagnosisType


DEFAULT_EXPERTS_GROUP_ID = 1  # временно константа
DEFAULT_STATUS_ID = 2         # например, "Предварительный"


async def calculate_diagnoses_for_mhrn(
    session: AsyncSession,
    mh_rn: int,
    experts_group_id: int = DEFAULT_EXPERTS_GROUP_ID,
    default_status_id: int = DEFAULT_STATUS_ID,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Считает диагнозы для одной стацкарты (mh_rn) и
    возвращает заготовки для diagnosis_state и diagnosis_events_state.
    Ничего в БД не пишет.
    """
    # 1. События по карте с их seq_numb
    q = (
        select(Event.id, Event.event_type_id, Event.event_timestamp, Event.created_at,
               Event.updated_at, EventType.seq_numb)
        .join(EventType, Event.event_type_id == EventType.id)
        .where(Event.mh_rn == mh_rn)
    )
    result = await session.execute(q)
    rows = result.all()

    if not rows:
        return {
            "diagnosis_state_rows": [],
            "diagnosis_events_state_rows": [],
        }

    # построить множество номеров и карту номер -> ids событий
    active_event_nums: Set[int] = set()
    event_num_to_event_ids: Dict[int, Set[int]] = {}

    for event_id, _, _, _, _, seq_numb in rows:
        if seq_numb is None:
            continue
        num = int(seq_numb)
        active_event_nums.add(num)
        event_num_to_event_ids.setdefault(num, set()).add(event_id)

    # 2. Все диагнозы
    diag_result = await session.execute(select(DiagnosisType))
    diagnoses = diag_result.scalars().all()

      # твой движок

    diagnosis_state_rows: List[Dict[str, Any]] = []
    diagnosis_events_state_rows: List[Dict[str, Any]] = []

    for diag in diagnoses:
        if not diag.formula:
            continue

        rule = DiagnosisRule(diag.id, diag.title, diag.formula)
        matched = rule.check(active_event_nums)
        if not matched:
            continue

        # номера событий, реально удовлетворившие формулу
        matched_nums = matched_events(rule.ast, active_event_nums)
        if not matched_nums:
            continue

        # все реальные event.id по этим номерам
        event_ids_for_diag: Set[int] = set()
        for num in matched_nums:
            event_ids_for_diag |= event_num_to_event_ids.get(num, set())

        if not event_ids_for_diag:
            continue

        # diagnosis_state — пока без id, его получим на шаге вставки
        diagnosis_state_rows.append({
            "experts_group_id": experts_group_id,
            "mh_rn": mh_rn,
            "diagnosis_types_id": diag.id,
            "status_id": default_status_id,
        })

        # diagnosis_events_state — привяжем позже к diagnosis_state_id,
        # здесь запомнили только diagnosis_types_id + events_id
        for eid in sorted(event_ids_for_diag):
            diagnosis_events_state_rows.append({
                "diagnosis_types_id": diag.id,  # временно, потом заменим на diagnosis_state_id
                "events_id": eid,
                "is_transferred": False,
                "transferred_by": None,
            })

    return {
        "diagnosis_state_rows": diagnosis_state_rows,
        "diagnosis_events_state_rows": diagnosis_events_state_rows,
    }
