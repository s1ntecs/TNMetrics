from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.schemas.record import RecordCreate, RecordRead
from src.application.services.record_service import RecordService
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.db.models import User
from src.presentation.api.deps import get_current_user, get_record_service

router = APIRouter(prefix="/api/metrics", tags=["records"])


@router.get("/{metric_id}/records/", response_model=list[RecordRead])
async def list_metric_records(
    metric_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    record_service: RecordService = Depends(get_record_service),
) -> list[RecordRead]:
    try:
        return await record_service.list_records(
            user_id=current_user.id,
            metric_id=metric_id,
            limit=limit,
            offset=offset,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{metric_id}/records/{record_id}", response_model=RecordRead)
async def get_metric_record(
    metric_id: UUID,
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    record_service: RecordService = Depends(get_record_service),
) -> RecordRead:
    try:
        return await record_service.get_record(
            user_id=current_user.id,
            metric_id=metric_id,
            record_id=record_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{metric_id}/records/", response_model=RecordRead, status_code=201)
async def create_metric_record(
    metric_id: UUID,
    payload: RecordCreate,
    current_user: User = Depends(get_current_user),
    record_service: RecordService = Depends(get_record_service),
) -> RecordRead:
    try:
        return await record_service.create_record(
            user_id=current_user.id,
            metric_id=metric_id,
            data=payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
