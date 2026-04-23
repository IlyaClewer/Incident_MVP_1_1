from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    DiagnosisEventState,
    DiagnosisState,
    Event,
    Expert,
    ExpertExpGroup,
    ExpertsGroup,
    IsbpIncident,
    Log,
    StacCard,
)
from app.schemas.isbp import (
    IsbpCreateIncidentRequest,
    IsbpCreateIncidentResponse,
    IsbpDiagnosisPayload,
    IsbpEventPayload,
    IsbpIncidentStatusResponse,
    IsbpPatientPayload,
    IsbpPollTarget,
    IsbpStacCardPayload,
    IsbpStatus,
    IsbpUserPayload,
)
from app.services.isbp_client import IsbpApiClient, IsbpClientError
from app.services.patients_service import normalize_status_title


PENDING_ISBP_STATUSES = {
    IsbpStatus.CREATED_DRAFT.value,
    IsbpStatus.IN_PROGRESS.value,
}
FINAL_ISBP_STATUSES = {
    IsbpStatus.CONFIRMED.value,
    IsbpStatus.REJECTED.value,
    IsbpStatus.ERROR.value,
    IsbpStatus.NOT_FOUND.value,
}


class IsbpIntegrationService:
    @staticmethod
    async def build_create_payload(
        session: AsyncSession,
        *,
        diagnosis_state_id: int,
        comment: str,
        expert_id: int | None = None,
    ) -> IsbpCreateIncidentRequest:
        diagnosis_state = await IsbpIntegrationService._get_diagnosis_state(
            session,
            diagnosis_state_id,
        )
        expert = await IsbpIntegrationService._resolve_expert(
            session,
            diagnosis_state.experts_group,
            expert_id=expert_id,
        )

        stac_card = diagnosis_state.stac_card
        if stac_card is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Diagnosis state is not linked to a stac card",
            )

        amb_card = stac_card.amb_card
        patient_name = amb_card.patient_name if amb_card else None
        if not patient_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to build ISBP payload: patient name is missing",
            )

        return IsbpCreateIncidentRequest(
            mh_rn=diagnosis_state.mh_rn,
            diagnosis_state_id=diagnosis_state.id,
            comment=comment.strip(),
            diagnosis=IsbpDiagnosisPayload(
                id=diagnosis_state.diagnosis_types_id,
                title=diagnosis_state.diagnosis_type.title,
                status=normalize_status_title(
                    diagnosis_state.status.title if diagnosis_state.status else None
                ),
            ),
            patient=IsbpPatientPayload(
                amb_card_number=amb_card.amb_card_number if amb_card else None,
                external_patient_id=stac_card.external_patient_id
                or (amb_card.external_patient_id if amb_card else None),
                patient_name=patient_name,
                birth_date=amb_card.birth_date if amb_card else None,
                sex=amb_card.sex if amb_card else None,
            ),
            stac_card=IsbpStacCardPayload(
                card_number=stac_card.card_numb,
                mht_numb=stac_card.mht_numb,
                department=stac_card.department,
                admission_date=stac_card.admission_date,
                discharge_date=stac_card.daisharge_date,
                weight=float(stac_card.weight) if stac_card.weight is not None else None,
                height=float(stac_card.height) if stac_card.height is not None else None,
            ),
            user=IsbpIntegrationService._build_user_payload(
                expert=expert,
                experts_group=diagnosis_state.experts_group,
            ),
            events=IsbpIntegrationService._build_event_payloads(diagnosis_state),
        )

    @staticmethod
    async def create_incident(
        session: AsyncSession,
        *,
        diagnosis_state_id: int,
        comment: str,
        expert_id: int | None = None,
        client: IsbpApiClient | None = None,
    ) -> IsbpCreateIncidentResponse:
        payload = await IsbpIntegrationService.build_create_payload(
            session,
            diagnosis_state_id=diagnosis_state_id,
            comment=comment,
            expert_id=expert_id,
        )
        client = client or IsbpApiClient()

        try:
            response = await client.create_incident(payload)
        except IsbpClientError as error:
            await IsbpIntegrationService._upsert_isbp_incident_error(
                session,
                mh_rn=payload.mh_rn,
                diagnosis_state_id=payload.diagnosis_state_id,
                experts_group_id=await IsbpIntegrationService._get_experts_group_id(
                    session,
                    payload.diagnosis_state_id,
                ),
                expert_id=expert_id,
                request_payload=payload.model_dump(mode="json", exclude_none=True),
                error=error,
            )
            await IsbpIntegrationService._log_isbp_error(
                session,
                action="isbp.incident.create_failed",
                mh_rn=payload.mh_rn,
                diagnosis_state_id=payload.diagnosis_state_id,
                experts_group_id=await IsbpIntegrationService._get_experts_group_id(
                    session,
                    payload.diagnosis_state_id,
                ),
                expert_id=expert_id,
                error=error,
            )
            await session.commit()
            raise

        await IsbpIntegrationService._upsert_isbp_incident_response(
            session,
            mh_rn=payload.mh_rn,
            diagnosis_state_id=payload.diagnosis_state_id,
            experts_group_id=await IsbpIntegrationService._get_experts_group_id(
                session,
                payload.diagnosis_state_id,
            ),
            expert_id=expert_id,
            request_payload=payload.model_dump(mode="json", exclude_none=True),
            create_response=response,
        )
        await IsbpIntegrationService._log_isbp_response(
            session,
            action="isbp.incident.created",
            mh_rn=payload.mh_rn,
            diagnosis_state_id=payload.diagnosis_state_id,
            experts_group_id=await IsbpIntegrationService._get_experts_group_id(
                session,
                payload.diagnosis_state_id,
            ),
            expert_id=expert_id,
            response=response,
        )
        await session.commit()
        return response

    @staticmethod
    async def check_incident_status(
        session: AsyncSession,
        *,
        mh_rn: int,
        diagnosis_state_id: int,
        client: IsbpApiClient | None = None,
    ) -> IsbpIncidentStatusResponse:
        client = client or IsbpApiClient()
        response = await client.get_incident_status(
            mh_rn=mh_rn,
            diagnosis_state_id=diagnosis_state_id,
        )

        await IsbpIntegrationService._update_isbp_incident_status(
            session,
            mh_rn=mh_rn,
            diagnosis_state_id=diagnosis_state_id,
            response=response,
        )
        await IsbpIntegrationService._log_isbp_response(
            session,
            action="isbp.incident.status_checked",
            mh_rn=mh_rn,
            diagnosis_state_id=diagnosis_state_id,
            experts_group_id=await IsbpIntegrationService._get_experts_group_id(
                session,
                diagnosis_state_id,
            ),
            expert_id=None,
            response=response,
        )
        await session.commit()
        return response

    @staticmethod
    async def collect_pending_poll_targets(
        session: AsyncSession,
        *,
        limit: int = 100,
    ) -> list[IsbpPollTarget]:
        result = await session.execute(
            select(IsbpIncident)
            .where(
                IsbpIncident.last_status.in_(PENDING_ISBP_STATUSES)
            )
            .order_by(IsbpIncident.last_checked_at.asc().nulls_first(), IsbpIncident.sent_at.asc())
            .limit(limit)
        )

        return [
            IsbpPollTarget(
                mh_rn=item.mh_rn,
                diagnosis_state_id=item.diagnosis_state_id,
                isbp_incident_id=item.isbp_incident_id,
                last_status=item.last_status,
            )
            for item in result.scalars().all()
        ]

    @staticmethod
    async def _get_diagnosis_state(
        session: AsyncSession,
        diagnosis_state_id: int,
    ) -> DiagnosisState:
        result = await session.execute(
            select(DiagnosisState)
            .where(DiagnosisState.id == diagnosis_state_id)
            .options(
                selectinload(DiagnosisState.status),
                selectinload(DiagnosisState.diagnosis_type),
                selectinload(DiagnosisState.stac_card).selectinload(StacCard.amb_card),
                selectinload(DiagnosisState.experts_group)
                .selectinload(ExpertsGroup.expert_links)
                .selectinload(ExpertExpGroup.expert),
                selectinload(DiagnosisState.event_states)
                .selectinload(DiagnosisEventState.event)
                .selectinload(Event.event_type),
            )
        )
        diagnosis_state = result.scalar_one_or_none()
        if diagnosis_state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis state not found",
            )
        return diagnosis_state

    @staticmethod
    async def _resolve_expert(
        session: AsyncSession,
        experts_group: ExpertsGroup,
        *,
        expert_id: int | None,
    ) -> Expert | None:
        if expert_id is not None:
            result = await session.execute(
                select(Expert).where(Expert.id == expert_id)
            )
            expert = result.scalar_one_or_none()
            if expert is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Expert not found",
                )
            return expert

        linked_experts = sorted(
            (link.expert for link in experts_group.expert_links if link.expert),
            key=lambda expert: expert.id,
        )
        return linked_experts[0] if linked_experts else None

    @staticmethod
    def _build_user_payload(
        *,
        expert: Expert | None,
        experts_group: ExpertsGroup,
    ) -> IsbpUserPayload:
        if expert is None:
            return IsbpUserPayload(
                id=f"experts_group:{experts_group.id}",
                ad_username=None,
                display_name=experts_group.title,
            )

        return IsbpUserPayload(
            id=expert.id,
            ad_username=expert.ad_username,
            display_name=expert.display_name
            or expert.ad_username
            or experts_group.title,
        )

    @staticmethod
    def _build_event_payloads(
        diagnosis_state: DiagnosisState,
    ) -> list[IsbpEventPayload]:
        events = [
            event_state.event
            for event_state in diagnosis_state.event_states
            if event_state.event is not None
        ]
        events = sorted(events, key=lambda event: event.id)

        return [
            IsbpEventPayload(
                id=event.id,
                event_type_id=event.event_type_id,
                event_type_title=event.event_type.title if event.event_type else None,
                event_type_short_title=event.event_type.short_title
                if event.event_type
                else None,
                event_timestamp=event.event_timestamp,
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            for event in events
        ]

    @staticmethod
    async def _get_experts_group_id(
        session: AsyncSession,
        diagnosis_state_id: int,
    ) -> int | None:
        result = await session.execute(
            select(DiagnosisState.experts_group_id).where(
                DiagnosisState.id == diagnosis_state_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_or_create_isbp_incident(
        session: AsyncSession,
        *,
        diagnosis_state_id: int,
        mh_rn: int,
    ) -> IsbpIncident:
        result = await session.execute(
            select(IsbpIncident).where(
                IsbpIncident.diagnosis_state_id == diagnosis_state_id
            )
        )
        incident = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if incident is not None:
            return incident

        incident = IsbpIncident(
            diagnosis_state_id=diagnosis_state_id,
            mh_rn=mh_rn,
            created_at=now,
        )
        session.add(incident)
        return incident

    @staticmethod
    async def _upsert_isbp_incident_response(
        session: AsyncSession,
        *,
        mh_rn: int,
        diagnosis_state_id: int,
        experts_group_id: int | None,
        expert_id: int | None,
        request_payload: dict,
        create_response: IsbpCreateIncidentResponse,
    ) -> None:
        now = datetime.now(timezone.utc)
        incident = await IsbpIntegrationService._get_or_create_isbp_incident(
            session,
            diagnosis_state_id=diagnosis_state_id,
            mh_rn=mh_rn,
        )
        incident.experts_group_id = experts_group_id
        incident.expert_id = expert_id
        incident.isbp_incident_id = create_response.isbp_incident_id
        incident.create_request_payload = request_payload
        incident.create_response_payload = create_response.model_dump(
            mode="json",
            exclude_none=True,
        )
        incident.last_status = create_response.status
        incident.last_error_code = create_response.error_code
        incident.last_error_message = None if create_response.success else create_response.message
        incident.sent_at = now
        incident.updated_at = now

    @staticmethod
    async def _upsert_isbp_incident_error(
        session: AsyncSession,
        *,
        mh_rn: int,
        diagnosis_state_id: int,
        experts_group_id: int | None,
        expert_id: int | None,
        request_payload: dict,
        error: IsbpClientError,
    ) -> None:
        now = datetime.now(timezone.utc)
        incident = await IsbpIntegrationService._get_or_create_isbp_incident(
            session,
            diagnosis_state_id=diagnosis_state_id,
            mh_rn=mh_rn,
        )
        incident.experts_group_id = experts_group_id
        incident.expert_id = expert_id
        incident.create_request_payload = request_payload
        incident.last_status = IsbpStatus.ERROR.value
        incident.last_error_code = (
            "HTTP_ERROR" if error.status_code is not None else "NETWORK_ERROR"
        )
        incident.last_error_message = str(error)
        incident.updated_at = now

    @staticmethod
    async def _update_isbp_incident_status(
        session: AsyncSession,
        *,
        mh_rn: int,
        diagnosis_state_id: int,
        response: IsbpIncidentStatusResponse,
    ) -> None:
        now = datetime.now(timezone.utc)
        incident = await IsbpIntegrationService._get_or_create_isbp_incident(
            session,
            diagnosis_state_id=diagnosis_state_id,
            mh_rn=mh_rn,
        )
        incident.isbp_incident_id = response.isbp_incident_id or incident.isbp_incident_id
        incident.last_status = response.status
        incident.last_error_code = response.error_code
        incident.last_error_message = None if response.success else response.message
        incident.last_status_response_payload = response.model_dump(
            mode="json",
            exclude_none=True,
        )
        incident.confirmed_at = response.confirmed_at or incident.confirmed_at
        incident.last_checked_at = now
        incident.updated_at = now

    @staticmethod
    async def _log_isbp_response(
        session: AsyncSession,
        *,
        action: str,
        mh_rn: int,
        diagnosis_state_id: int,
        experts_group_id: int | None,
        expert_id: int | None,
        response: IsbpCreateIncidentResponse | IsbpIncidentStatusResponse,
    ) -> None:
        session.add(
            Log(
                id=uuid4(),
                action=action,
                expert_id=expert_id,
                experts_group_id=experts_group_id,
                mh_rn=mh_rn,
                created_at=datetime.now(timezone.utc),
                details={
                    "mh_rn": mh_rn,
                    "diagnosis_state_id": diagnosis_state_id,
                    "status": response.status,
                    "success": response.success,
                    "message": response.message,
                    "isbp_incident_id": response.isbp_incident_id,
                    "confirmed_at": response.confirmed_at.isoformat()
                    if getattr(response, "confirmed_at", None)
                    else None,
                    "error_code": response.error_code,
                },
            )
        )

    @staticmethod
    async def _log_isbp_error(
        session: AsyncSession,
        *,
        action: str,
        mh_rn: int,
        diagnosis_state_id: int,
        experts_group_id: int | None,
        expert_id: int | None,
        error: IsbpClientError,
    ) -> None:
        session.add(
            Log(
                id=uuid4(),
                action=action,
                expert_id=expert_id,
                experts_group_id=experts_group_id,
                mh_rn=mh_rn,
                created_at=datetime.now(timezone.utc),
                details={
                    "mh_rn": mh_rn,
                    "diagnosis_state_id": diagnosis_state_id,
                    "status": IsbpStatus.ERROR.value,
                    "success": False,
                    "message": str(error),
                    "error_code": "HTTP_ERROR"
                    if error.status_code is not None
                    else "NETWORK_ERROR",
                    "http_status_code": error.status_code,
                    "payload": error.payload,
                },
            )
        )
