from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import DiagnosisEventState, DiagnosisState, DiagnosisStateStatus, Event, Log
from app.schemas.diagnosis_states import DiagnosisStateResponse
from app.schemas.common import DiagnosisStateStatus as DiagnosisStateStatusValue
from app.services.patients_service import normalize_status_title


class DiagnosisStateService:
    @staticmethod
    async def _get_state_or_404(
        session: AsyncSession,
        diagnosis_state_id: int,
    ) -> DiagnosisState:
        result = await session.execute(
            select(DiagnosisState)
            .where(DiagnosisState.id == diagnosis_state_id)
            .execution_options(populate_existing=True)
            .options(selectinload(DiagnosisState.status))
        )
        diagnosis_state = result.scalar_one_or_none()
        if diagnosis_state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis state not found",
            )
        return diagnosis_state

    @staticmethod
    async def _resolve_status_id(
        session: AsyncSession,
        target_status: DiagnosisStateStatusValue,
    ) -> int:
        result = await session.execute(select(DiagnosisStateStatus))
        statuses = result.scalars().all()

        for status_row in statuses:
            if normalize_status_title(status_row.title) == target_status.value:
                return status_row.id

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to resolve database status for '{target_status.value}'",
        )

    @staticmethod
    def _serialize_state(diagnosis_state: DiagnosisState) -> DiagnosisStateResponse:
        return DiagnosisStateResponse(
            id=diagnosis_state.id,
            stac_card_id=diagnosis_state.mh_rn,
            diagnosis_id=diagnosis_state.diagnosis_types_id,
            expert_group_id=diagnosis_state.experts_group_id,
            status=normalize_status_title(
                diagnosis_state.status.title if diagnosis_state.status else None
            ),
        )

    @staticmethod
    async def update_status(
        session: AsyncSession,
        diagnosis_state_id: int,
        target_status: DiagnosisStateStatusValue,
        comment: str | None,
    ) -> DiagnosisStateResponse:
        diagnosis_state = await DiagnosisStateService._get_state_or_404(session, diagnosis_state_id)
        old_status = normalize_status_title(diagnosis_state.status.title if diagnosis_state.status else None)
        target_status_id = await DiagnosisStateService._resolve_status_id(session, target_status)

        diagnosis_state.status_id = target_status_id
        diagnosis_state.updated_at = datetime.utcnow()

        session.add(
            Log(
                id=uuid4(),
                action="diagnosis_state.status_changed",
                expert_id=None,
                experts_group_id=diagnosis_state.experts_group_id,
                mh_rn=diagnosis_state.mh_rn,
                created_at=datetime.now(timezone.utc),
                details={
                    "diagnosis_state_id": diagnosis_state.id,
                    "from_status": old_status,
                    "to_status": target_status.value,
                    "comment": comment,
                },
            )
        )

        await session.commit()
        refreshed_state = await DiagnosisStateService._get_state_or_404(session, diagnosis_state_id)
        return DiagnosisStateService._serialize_state(refreshed_state)

    @staticmethod
    async def transfer_events(
        session: AsyncSession,
        source_diagnosis_state_id: int,
        target_diagnosis_state_id: int,
        event_ids: list[int],
        transferred_by: str | None,
    ) -> list[int]:
        if not event_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="event_ids must not be empty",
            )

        source_state = await DiagnosisStateService._get_state_or_404(session, source_diagnosis_state_id)
        target_state = await DiagnosisStateService._get_state_or_404(session, target_diagnosis_state_id)

        if source_state.mh_rn != target_state.mh_rn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target diagnosis state must belong to the same stac card",
            )

        unique_event_ids = sorted(set(event_ids))

        event_result = await session.execute(
            select(Event.id)
            .where(Event.id.in_(unique_event_ids), Event.mh_rn == source_state.mh_rn)
        )
        existing_event_ids = {row[0] for row in event_result.all()}

        missing_event_ids = sorted(set(unique_event_ids) - existing_event_ids)
        if missing_event_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Some events do not belong to the source stac card",
                    "event_ids": missing_event_ids,
                },
            )

        source_links_result = await session.execute(
            select(DiagnosisEventState.events_id).where(
                DiagnosisEventState.diagnosis_state_id == source_diagnosis_state_id,
                DiagnosisEventState.events_id.in_(unique_event_ids),
            )
        )
        source_linked_ids = {row[0] for row in source_links_result.all()}

        invalid_event_ids = sorted(set(unique_event_ids) - source_linked_ids)
        if invalid_event_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Some events are not linked to the source diagnosis state",
                    "event_ids": invalid_event_ids,
                },
            )

        target_links_result = await session.execute(
            select(DiagnosisEventState).where(
                DiagnosisEventState.diagnosis_state_id == target_diagnosis_state_id,
                DiagnosisEventState.events_id.in_(unique_event_ids),
            )
        )
        target_links = {link.events_id: link for link in target_links_result.scalars().all()}

        actor = transferred_by or "system"

        for event_id in unique_event_ids:
            existing_link = target_links.get(event_id)
            if existing_link is not None:
                existing_link.is_transferred = True
                existing_link.transferred_by = actor
                continue

            session.add(
                DiagnosisEventState(
                    diagnosis_state_id=target_diagnosis_state_id,
                    events_id=event_id,
                    is_transferred=True,
                    transferred_by=actor,
                )
            )

        session.add(
            Log(
                id=uuid4(),
                action="diagnosis_state.events_transferred",
                expert_id=None,
                experts_group_id=target_state.experts_group_id,
                mh_rn=target_state.mh_rn,
                created_at=datetime.now(timezone.utc),
                details={
                    "source_diagnosis_state_id": source_diagnosis_state_id,
                    "target_diagnosis_state_id": target_diagnosis_state_id,
                    "event_ids": unique_event_ids,
                    "transferred_by": actor,
                },
            )
        )

        await session.commit()
        return unique_event_ids
