from fastapi import APIRouter, Depends, HTTPException

from src.application.schemas.metric import MetricCreate, MetricRead
from src.application.services.metric_service import MetricService
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models import User
from src.presentation.api.deps import get_current_user, get_metric_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.post("/", response_model=MetricRead, status_code=201)
async def create_metric(
    payload: MetricCreate,
    current_user: User = Depends(get_current_user),
    metric_service: MetricService = Depends(get_metric_service),
) -> MetricRead:
    try:
        metric = await metric_service.create_metric(user_id=current_user.id, data=payload)
        return MetricRead.model_validate(metric)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=list[MetricRead])
async def list_metrics(
    current_user: User = Depends(get_current_user),
    metric_service: MetricService = Depends(get_metric_service),
) -> list[MetricRead]:
    metrics = await metric_service.list_metrics(user_id=current_user.id)
    return [MetricRead.model_validate(item) for item in metrics]
