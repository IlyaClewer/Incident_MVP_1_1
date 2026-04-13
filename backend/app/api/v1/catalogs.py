from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogs import (
    DiagnosisTypeCatalogItem,
    DiagnosisTypeCreate,
    DiagnosisTypeUpdate,
    EventTypeCatalogItem,
    EventTypeCreate,
    EventTypeUpdate,
    ExpertGroupCatalogItem,
    ExpertGroupCreate,
    ExpertGroupUpdate,
)
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/expert-groups", response_model=list[ExpertGroupCatalogItem])
async def list_expert_groups(db: AsyncSession = Depends(get_db)) -> list[ExpertGroupCatalogItem]:
    return await CatalogService.list_expert_groups(db)


@router.post("/expert-groups", response_model=ExpertGroupCatalogItem, status_code=status.HTTP_201_CREATED)
async def create_expert_group(
    payload: ExpertGroupCreate,
    db: AsyncSession = Depends(get_db),
) -> ExpertGroupCatalogItem:
    return await CatalogService.create_expert_group(db, payload.title, payload.diagnosis_ids)


@router.patch("/expert-groups/{group_id}", response_model=ExpertGroupCatalogItem)
async def update_expert_group(
    group_id: int,
    payload: ExpertGroupUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExpertGroupCatalogItem:
    return await CatalogService.update_expert_group(db, group_id, payload.title, payload.diagnosis_ids)


@router.delete("/expert-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expert_group(group_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    await CatalogService.delete_expert_group(db, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/diagnosis-types", response_model=list[DiagnosisTypeCatalogItem])
async def list_diagnosis_types(db: AsyncSession = Depends(get_db)) -> list[DiagnosisTypeCatalogItem]:
    return await CatalogService.list_diagnosis_types(db)


@router.post("/diagnosis-types", response_model=DiagnosisTypeCatalogItem, status_code=status.HTTP_201_CREATED)
async def create_diagnosis_type(
    payload: DiagnosisTypeCreate,
    db: AsyncSession = Depends(get_db),
) -> DiagnosisTypeCatalogItem:
    return await CatalogService.create_diagnosis_type(
        db,
        title=payload.title,
        formula=payload.formula,
        event_type_ids=payload.event_type_ids,
        expert_group_ids=payload.expert_group_ids,
    )


@router.patch("/diagnosis-types/{diagnosis_id}", response_model=DiagnosisTypeCatalogItem)
async def update_diagnosis_type(
    diagnosis_id: int,
    payload: DiagnosisTypeUpdate,
    db: AsyncSession = Depends(get_db),
) -> DiagnosisTypeCatalogItem:
    return await CatalogService.update_diagnosis_type(
        db,
        diagnosis_id=diagnosis_id,
        title=payload.title,
        formula=payload.formula,
        event_type_ids=payload.event_type_ids,
        expert_group_ids=payload.expert_group_ids,
    )


@router.delete("/diagnosis-types/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagnosis_type(diagnosis_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    await CatalogService.delete_diagnosis_type(db, diagnosis_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/event-types", response_model=list[EventTypeCatalogItem])
async def list_event_types(db: AsyncSession = Depends(get_db)) -> list[EventTypeCatalogItem]:
    return await CatalogService.list_event_types(db)


@router.post("/event-types", response_model=EventTypeCatalogItem, status_code=status.HTTP_201_CREATED)
async def create_event_type(
    payload: EventTypeCreate,
    db: AsyncSession = Depends(get_db),
) -> EventTypeCatalogItem:
    return await CatalogService.create_event_type(db, payload)


@router.patch("/event-types/{event_type_id}", response_model=EventTypeCatalogItem)
async def update_event_type(
    event_type_id: int,
    payload: EventTypeUpdate,
    db: AsyncSession = Depends(get_db),
) -> EventTypeCatalogItem:
    return await CatalogService.update_event_type(db, event_type_id, payload)


@router.delete("/event-types/{event_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_type(event_type_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    await CatalogService.delete_event_type(db, event_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
