from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    DiagnosisEventDirectory,
    DiagnosisType,
    EventType,
    ExpGroupGroupDiagnosis,
    ExpGroupDiagnosis,
    ExpertsGroup,
    GroupDiagnosis,
)
from app.schemas.catalogs import (
    DiagnosisTypeCatalogItem,
    EventTypeCatalogItem,
    ExpertGroupCatalogItem,
)


async def _ensure_existing_ids(
    session: AsyncSession,
    model,
    ids: list[int],
    field_name: str,
) -> list[int]:
    normalized_ids = sorted({int(item) for item in ids})
    if not normalized_ids:
        return []

    result = await session.execute(select(model.id).where(model.id.in_(normalized_ids)))
    existing_ids = {row[0] for row in result.all()}
    missing_ids = [item for item in normalized_ids if item not in existing_ids]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown {field_name}: {missing_ids}",
        )

    return normalized_ids


class CatalogService:
    @staticmethod
    async def list_expert_groups(session: AsyncSession) -> list[ExpertGroupCatalogItem]:
        result = await session.execute(
            select(ExpertsGroup)
            .options(
                selectinload(ExpertsGroup.diagnosis_links),
                selectinload(ExpertsGroup.diagnosis_group_links),
            )
            .order_by(ExpertsGroup.id)
        )
        groups = result.scalars().unique().all()

        return [
            ExpertGroupCatalogItem(
                id=group.id,
                title=group.title,
                diagnosis_ids=sorted({link.diagnosis_type_id for link in group.diagnosis_links}),
                group_diagnosis_ids=sorted(
                    {link.group_diagnosis_id for link in group.diagnosis_group_links}
                ),
                primary_group_diagnosis_id=group.group_diagnosis_id,
            )
            for group in groups
        ]

    @staticmethod
    async def create_expert_group(
        session: AsyncSession,
        title: str,
        diagnosis_ids: list[int],
        group_diagnosis_ids: list[int],
        primary_group_diagnosis_id: int | None,
    ) -> ExpertGroupCatalogItem:
        valid_diagnosis_ids = await _ensure_existing_ids(session, DiagnosisType, diagnosis_ids, "diagnosis_ids")
        valid_group_diagnosis_ids = await _ensure_existing_ids(
            session,
            GroupDiagnosis,
            group_diagnosis_ids,
            "group_diagnosis_ids",
        )
        if primary_group_diagnosis_id is not None:
            primary_group_diagnosis_id = (
                await _ensure_existing_ids(
                    session,
                    GroupDiagnosis,
                    [primary_group_diagnosis_id],
                    "primary_group_diagnosis_id",
                )
            )[0]

        group = ExpertsGroup(
            title=title.strip(),
            group_diagnosis_id=primary_group_diagnosis_id,
        )
        session.add(group)
        await session.flush()

        for diagnosis_id in valid_diagnosis_ids:
            session.add(
                ExpGroupDiagnosis(
                    experts_group_id=group.id,
                    diagnosis_type_id=diagnosis_id,
                )
            )

        for group_diagnosis_id in valid_group_diagnosis_ids:
            session.add(
                ExpGroupGroupDiagnosis(
                    experts_group_id=group.id,
                    group_diagnosis_id=group_diagnosis_id,
                )
            )

        await session.commit()
        await session.refresh(group)

        return ExpertGroupCatalogItem(
            id=group.id,
            title=group.title,
            diagnosis_ids=valid_diagnosis_ids,
            group_diagnosis_ids=valid_group_diagnosis_ids,
            primary_group_diagnosis_id=group.group_diagnosis_id,
        )

    @staticmethod
    async def update_expert_group(
        session: AsyncSession,
        group_id: int,
        title: str | None,
        diagnosis_ids: list[int] | None,
        group_diagnosis_ids: list[int] | None,
        primary_group_diagnosis_id: int | None,
    ) -> ExpertGroupCatalogItem:
        result = await session.execute(
            select(ExpertsGroup)
            .where(ExpertsGroup.id == group_id)
            .options(
                selectinload(ExpertsGroup.diagnosis_links),
                selectinload(ExpertsGroup.diagnosis_group_links),
            )
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise HTTPException(status_code=404, detail="Expert group not found")

        if title is not None:
            group.title = title.strip()

        resolved_diagnosis_ids: list[int]
        resolved_group_diagnosis_ids = sorted(
            {link.group_diagnosis_id for link in group.diagnosis_group_links}
        )
        if diagnosis_ids is not None:
            resolved_diagnosis_ids = await _ensure_existing_ids(session, DiagnosisType, diagnosis_ids, "diagnosis_ids")
            await session.execute(
                delete(ExpGroupDiagnosis).where(ExpGroupDiagnosis.experts_group_id == group_id)
            )
            for diagnosis_id in resolved_diagnosis_ids:
                session.add(
                    ExpGroupDiagnosis(
                        experts_group_id=group_id,
                        diagnosis_type_id=diagnosis_id,
                    )
                )
        else:
            resolved_diagnosis_ids = sorted({link.diagnosis_type_id for link in group.diagnosis_links})

        if group_diagnosis_ids is not None:
            resolved_group_diagnosis_ids = await _ensure_existing_ids(
                session,
                GroupDiagnosis,
                group_diagnosis_ids,
                "group_diagnosis_ids",
            )
            await session.execute(
                delete(ExpGroupGroupDiagnosis).where(
                    ExpGroupGroupDiagnosis.experts_group_id == group_id
                )
            )
            for group_diagnosis_id in resolved_group_diagnosis_ids:
                session.add(
                    ExpGroupGroupDiagnosis(
                        experts_group_id=group_id,
                        group_diagnosis_id=group_diagnosis_id,
                    )
                )

        if primary_group_diagnosis_id is not None:
            group.group_diagnosis_id = (
                await _ensure_existing_ids(
                    session,
                    GroupDiagnosis,
                    [primary_group_diagnosis_id],
                    "primary_group_diagnosis_id",
                )
            )[0]

        await session.commit()
        return ExpertGroupCatalogItem(
            id=group.id,
            title=group.title,
            diagnosis_ids=resolved_diagnosis_ids,
            group_diagnosis_ids=resolved_group_diagnosis_ids,
            primary_group_diagnosis_id=group.group_diagnosis_id,
        )

    @staticmethod
    async def delete_expert_group(session: AsyncSession, group_id: int) -> None:
        await session.execute(delete(ExpGroupDiagnosis).where(ExpGroupDiagnosis.experts_group_id == group_id))
        await session.execute(
            delete(ExpGroupGroupDiagnosis).where(ExpGroupGroupDiagnosis.experts_group_id == group_id)
        )
        result = await session.execute(select(ExpertsGroup).where(ExpertsGroup.id == group_id))
        group = result.scalar_one_or_none()
        if group is None:
            raise HTTPException(status_code=404, detail="Expert group not found")

        await session.delete(group)
        await session.commit()

    @staticmethod
    async def list_diagnosis_types(session: AsyncSession) -> list[DiagnosisTypeCatalogItem]:
        result = await session.execute(
            select(DiagnosisType)
            .options(
                selectinload(DiagnosisType.event_directory_links),
                selectinload(DiagnosisType.exp_group_links),
            )
            .order_by(DiagnosisType.id)
        )
        diagnoses = result.scalars().unique().all()

        return [
            DiagnosisTypeCatalogItem(
                id=diagnosis.id,
                title=diagnosis.title,
                formula=diagnosis.formula,
                event_type_ids=sorted({link.events_type_id for link in diagnosis.event_directory_links}),
                expert_group_ids=sorted({link.experts_group_id for link in diagnosis.exp_group_links}),
            )
            for diagnosis in diagnoses
        ]

    @staticmethod
    async def create_diagnosis_type(
        session: AsyncSession,
        title: str,
        formula: str | None,
        event_type_ids: list[int],
        expert_group_ids: list[int],
    ) -> DiagnosisTypeCatalogItem:
        valid_event_type_ids = await _ensure_existing_ids(session, EventType, event_type_ids, "event_type_ids")
        valid_group_ids = await _ensure_existing_ids(session, ExpertsGroup, expert_group_ids, "expert_group_ids")

        diagnosis = DiagnosisType(title=title.strip(), formula=formula.strip() if formula else None)
        session.add(diagnosis)
        await session.flush()

        for event_type_id in valid_event_type_ids:
            session.add(
                DiagnosisEventDirectory(
                    events_type_id=event_type_id,
                    diagnosis_id=diagnosis.id,
                )
            )

        for group_id in valid_group_ids:
            session.add(
                ExpGroupDiagnosis(
                    experts_group_id=group_id,
                    diagnosis_type_id=diagnosis.id,
                )
            )

        await session.commit()
        return DiagnosisTypeCatalogItem(
            id=diagnosis.id,
            title=diagnosis.title,
            formula=diagnosis.formula,
            event_type_ids=valid_event_type_ids,
            expert_group_ids=valid_group_ids,
        )

    @staticmethod
    async def update_diagnosis_type(
        session: AsyncSession,
        diagnosis_id: int,
        title: str | None,
        formula: str | None,
        event_type_ids: list[int] | None,
        expert_group_ids: list[int] | None,
    ) -> DiagnosisTypeCatalogItem:
        result = await session.execute(
            select(DiagnosisType)
            .where(DiagnosisType.id == diagnosis_id)
            .options(
                selectinload(DiagnosisType.event_directory_links),
                selectinload(DiagnosisType.exp_group_links),
            )
        )
        diagnosis = result.scalar_one_or_none()
        if diagnosis is None:
            raise HTTPException(status_code=404, detail="Diagnosis type not found")

        if title is not None:
            diagnosis.title = title.strip()
        if formula is not None:
            diagnosis.formula = formula.strip() or None

        resolved_event_type_ids = sorted({link.events_type_id for link in diagnosis.event_directory_links})
        resolved_group_ids = sorted({link.experts_group_id for link in diagnosis.exp_group_links})

        if event_type_ids is not None:
            resolved_event_type_ids = await _ensure_existing_ids(session, EventType, event_type_ids, "event_type_ids")
            await session.execute(
                delete(DiagnosisEventDirectory).where(DiagnosisEventDirectory.diagnosis_id == diagnosis_id)
            )
            for event_type_id in resolved_event_type_ids:
                session.add(
                    DiagnosisEventDirectory(
                        events_type_id=event_type_id,
                        diagnosis_id=diagnosis_id,
                    )
                )

        if expert_group_ids is not None:
            resolved_group_ids = await _ensure_existing_ids(session, ExpertsGroup, expert_group_ids, "expert_group_ids")
            await session.execute(
                delete(ExpGroupDiagnosis).where(ExpGroupDiagnosis.diagnosis_type_id == diagnosis_id)
            )
            for group_id in resolved_group_ids:
                session.add(
                    ExpGroupDiagnosis(
                        experts_group_id=group_id,
                        diagnosis_type_id=diagnosis_id,
                    )
                )

        await session.commit()
        return DiagnosisTypeCatalogItem(
            id=diagnosis.id,
            title=diagnosis.title,
            formula=diagnosis.formula,
            event_type_ids=resolved_event_type_ids,
            expert_group_ids=resolved_group_ids,
        )

    @staticmethod
    async def delete_diagnosis_type(session: AsyncSession, diagnosis_id: int) -> None:
        result = await session.execute(select(DiagnosisType).where(DiagnosisType.id == diagnosis_id))
        diagnosis = result.scalar_one_or_none()
        if diagnosis is None:
            raise HTTPException(status_code=404, detail="Diagnosis type not found")

        await session.execute(delete(DiagnosisEventDirectory).where(DiagnosisEventDirectory.diagnosis_id == diagnosis_id))
        await session.execute(delete(ExpGroupDiagnosis).where(ExpGroupDiagnosis.diagnosis_type_id == diagnosis_id))

        try:
            await session.delete(diagnosis)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Diagnosis type is in use and cannot be deleted",
            ) from exc

    @staticmethod
    async def list_event_types(session: AsyncSession) -> list[EventTypeCatalogItem]:
        result = await session.execute(select(EventType).order_by(EventType.id))
        event_types = result.scalars().all()

        return [
            EventTypeCatalogItem(
                id=item.id,
                details_category_id=item.details_category_id,
                events_class_id=item.events_class_id,
                short_title=item.short_title,
                title=item.title,
                category=item.category,
                query=item.query,
                active=item.active,
                seq_numb=item.seq_numb,
            )
            for item in event_types
        ]

    @staticmethod
    async def create_event_type(session: AsyncSession, payload) -> EventTypeCatalogItem:
        event_type = EventType(**payload.model_dump())
        session.add(event_type)
        await session.commit()
        await session.refresh(event_type)
        return EventTypeCatalogItem.model_validate(event_type)

    @staticmethod
    async def update_event_type(session: AsyncSession, event_type_id: int, payload) -> EventTypeCatalogItem:
        result = await session.execute(select(EventType).where(EventType.id == event_type_id))
        event_type = result.scalar_one_or_none()
        if event_type is None:
            raise HTTPException(status_code=404, detail="Event type not found")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(event_type, key, value)

        await session.commit()
        await session.refresh(event_type)
        return EventTypeCatalogItem.model_validate(event_type)

    @staticmethod
    async def delete_event_type(session: AsyncSession, event_type_id: int) -> None:
        result = await session.execute(select(EventType).where(EventType.id == event_type_id))
        event_type = result.scalar_one_or_none()
        if event_type is None:
            raise HTTPException(status_code=404, detail="Event type not found")

        try:
            await session.delete(event_type)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Event type is in use and cannot be deleted",
            ) from exc
