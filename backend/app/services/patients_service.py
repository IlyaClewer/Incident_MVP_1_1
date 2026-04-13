from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import DiagnosisState, DiagnosisType, Event, ExpertsGroup, FullEvent, StacCard
from app.schemas.events import EventDetailField, StacCardEventItem
from app.schemas.meta import DiagnosisMeta, DiagnosisStateMeta, ExpertGroupMeta
from app.schemas.patients import PatientSummary, StacCardSummary

STATUS_ALIASES = {
    "new": {"new", "pending", "preliminary", "draft", "новый", "предварительный"},
    "confirmed": {
        "confirmed",
        "approved",
        "accepted",
        "confirmed_by_expert",
        "подтвержден",
        "подтверждено",
        "принят",
        "принято",
    },
    "rejected": {"rejected", "declined", "revoke", "отклонен", "отклонено"},
}


def normalize_status_title(value: str | None) -> str:
    if not value:
        return "new"

    normalized = value.strip().lower().replace("ё", "е")
    for canonical, aliases in STATUS_ALIASES.items():
        if normalized in aliases:
            return canonical
    return normalized


def _to_date(value: Any) -> date | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None

        for candidate in (
            normalized,
            normalized.replace("Z", "+00:00"),
            normalized.split("T")[0],
            normalized.split(" ")[0],
        ):
            try:
                return datetime.fromisoformat(candidate).date()
            except ValueError:
                try:
                    return date.fromisoformat(candidate)
                except ValueError:
                    continue

    return None


def _iter_candidate_values(value: Any):
    if value is None:
        return

    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield item
        return

    yield value


def _resolve_operation_date(card: StacCard) -> date | None:
    for candidate in (card.oper_timestamp, card.oper_dates):
        if not candidate:
            continue

        for item in _iter_candidate_values(candidate):
            resolved = _to_date(item)
            if resolved is not None:
                return resolved

    return None


def _aggregate_card_status(card: StacCard) -> str:
    statuses = {
        normalize_status_title(state.status.title if state.status else None)
        for state in card.diagnosis_states
    }
    if "new" in statuses:
        return "new"
    if "rejected" in statuses:
        return "rejected"
    if "confirmed" in statuses:
        return "confirmed"
    return "new"


def _humanize_detail_key(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().capitalize()


def _stringify_detail_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ")
    if isinstance(value, (list, tuple, set)):
        parts = [_stringify_detail_value(item) for item in value]
        return ", ".join(part for part in parts if part and part != "—") or "—"
    if isinstance(value, dict):
        parts = [
            f"{_humanize_detail_key(str(key))}: {_stringify_detail_value(item)}"
            for key, item in value.items()
        ]
        return "; ".join(parts) or "—"

    text = str(value).strip()
    return text or "—"


def _normalize_event_details(details: Any) -> list[EventDetailField]:
    if not details:
        return []

    normalized: list[EventDetailField] = []

    if isinstance(details, list):
        for index, item in enumerate(details):
            if isinstance(item, dict):
                key = str(item.get("key") or f"detail_{index}")
                label = str(item.get("translate") or item.get("label") or _humanize_detail_key(key))
                normalized.append(
                    EventDetailField(
                        key=key,
                        label=label,
                        value=_stringify_detail_value(item.get("value")),
                        order=int(item.get("order") or index),
                    )
                )
            else:
                normalized.append(
                    EventDetailField(
                        key=f"detail_{index}",
                        label=f"Параметр {index + 1}",
                        value=_stringify_detail_value(item),
                        order=index,
                    )
                )
    elif isinstance(details, dict):
        for index, (key, value) in enumerate(details.items()):
            normalized.append(
                EventDetailField(
                    key=str(key),
                    label=_humanize_detail_key(str(key)),
                    value=_stringify_detail_value(value),
                    order=index,
                )
            )
    else:
        normalized.append(
            EventDetailField(
                key="details",
                label="Детали",
                value=_stringify_detail_value(details),
                order=0,
            )
        )

    return sorted(normalized, key=lambda item: (item.order, item.label))


class PatientsService:
    @staticmethod
    async def list_patients(session: AsyncSession) -> list[PatientSummary]:
        result = await session.execute(
            select(StacCard)
            .join(StacCard.diagnosis_states)
            .options(
                selectinload(StacCard.amb_card),
                selectinload(StacCard.diagnosis_states).selectinload(DiagnosisState.status),
            )
            .order_by(
                StacCard.amd_card_numb.asc().nulls_last(),
                StacCard.admission_date.desc().nulls_last(),
                StacCard.mh_rn.desc(),
            )
        )
        cards = result.scalars().unique().all()

        grouped: dict[str, PatientSummary] = {}
        ordered_keys: list[str] = []

        for card in cards:
            amb_card_num = (
                card.amb_card.amb_card_number
                if card.amb_card is not None
                else (card.amd_card_numb or f"UNKNOWN-{card.mh_rn}")
            )

            if amb_card_num not in grouped:
                grouped[amb_card_num] = PatientSummary(
                    amb_card_num=amb_card_num,
                    patientName=card.amb_card.patient_name if card.amb_card else None,
                    birthDate=_to_date(card.amb_card.birth_date if card.amb_card else None),
                    stac_cards=[],
                )
                ordered_keys.append(amb_card_num)

            grouped[amb_card_num].stac_cards.append(
                StacCardSummary(
                    id=card.mh_rn,
                    amb_card_num=amb_card_num,
                    cardNumber=card.card_numb or card.mht_numb,
                    department=card.department,
                    date_hosp=_to_date(card.admission_date),
                    date_operation=_resolve_operation_date(card),
                    date_discharge=_to_date(card.daisharge_date),
                    status=_aggregate_card_status(card),
                )
            )

        return [grouped[key] for key in ordered_keys]

    @staticmethod
    async def get_meta(
        session: AsyncSession,
    ) -> tuple[list[ExpertGroupMeta], list[DiagnosisMeta], list[DiagnosisStateMeta], dict[str, list[int]]]:
        group_result = await session.execute(
            select(ExpertsGroup)
            .options(selectinload(ExpertsGroup.diagnosis_links))
            .order_by(ExpertsGroup.id)
        )
        groups = group_result.scalars().unique().all()

        diagnosis_result = await session.execute(
            select(DiagnosisType)
            .options(
                selectinload(DiagnosisType.diagnosis_states).selectinload(DiagnosisState.status),
                selectinload(DiagnosisType.event_directory_links),
            )
            .order_by(DiagnosisType.id)
        )
        diagnoses = diagnosis_result.scalars().unique().all()

        expert_groups_payload = [
            ExpertGroupMeta(
                id=group.id,
                title=group.title,
                diagnosis_ids=sorted({link.diagnosis_type_id for link in group.diagnosis_links}),
            )
            for group in groups
        ]

        stac_card_diagnosis_index: dict[str, set[int]] = defaultdict(set)
        diagnosis_states_payload: list[DiagnosisStateMeta] = []
        diagnosis_payload: list[DiagnosisMeta] = []

        for diagnosis in diagnoses:
            stac_card_ids = sorted({state.mh_rn for state in diagnosis.diagnosis_states})
            event_type_ids = sorted({link.events_type_id for link in diagnosis.event_directory_links})

            diagnosis_payload.append(
                DiagnosisMeta(
                    id=diagnosis.id,
                    name=diagnosis.title,
                    description=None,
                    stac_card_ids=stac_card_ids,
                    formulas=[diagnosis.formula] if diagnosis.formula else [],
                    event_type_ids=event_type_ids,
                )
            )

            for state in diagnosis.diagnosis_states:
                diagnosis_states_payload.append(
                    DiagnosisStateMeta(
                        id=state.id,
                        stac_card_id=state.mh_rn,
                        diagnosis_id=state.diagnosis_types_id,
                        expert_group_id=state.experts_group_id,
                        status=normalize_status_title(state.status.title if state.status else None),
                    )
                )
                stac_card_diagnosis_index[str(state.mh_rn)].add(state.diagnosis_types_id)

        diagnosis_states_payload.sort(
            key=lambda item: (item.stac_card_id, item.expert_group_id, item.diagnosis_id)
        )

        return (
            expert_groups_payload,
            diagnosis_payload,
            diagnosis_states_payload,
            {
                key: sorted(values)
                for key, values in sorted(
                    stac_card_diagnosis_index.items(),
                    key=lambda item: int(item[0]),
                )
            },
        )

    @staticmethod
    async def list_stac_card_events(
        session: AsyncSession,
        stac_card_id: int,
    ) -> list[StacCardEventItem]:
        result = await session.execute(
            select(Event)
            .where(Event.mh_rn == stac_card_id)
            .options(
                selectinload(Event.event_type),
                selectinload(Event.diagnosis_event_states),
            )
            .order_by(Event.event_timestamp.desc().nulls_last(), Event.id.desc())
        )
        events = result.scalars().unique().all()

        full_events_map: dict[int, FullEvent] = {}
        if events:
            full_result = await session.execute(
                select(FullEvent).where(FullEvent.id.in_([event.id for event in events]))
            )
            full_events_map = {item.id: item for item in full_result.scalars().all()}

        payload: list[StacCardEventItem] = []
        for event in events:
            full_event = full_events_map.get(event.id)
            payload.append(
                StacCardEventItem(
                    id=event.id,
                    event_type_id=event.event_type_id,
                    date_trigger=_to_date(event.event_timestamp),
                    trigger=(
                        event.event_type.short_title
                        if event.event_type and event.event_type.short_title
                        else (
                            event.event_type.title
                            if event.event_type and event.event_type.title
                            else f"Event {event.event_type_id}"
                        )
                    ),
                    event_ids=[event.event_type_id],
                    diagnosis_state_ids=sorted(
                        {
                            link.diagnosis_state_id
                            for link in event.diagnosis_event_states
                            if link.diagnosis_state_id is not None
                        }
                    ),
                    details=_normalize_event_details(full_event.details if full_event else None),
                )
            )

        return payload
