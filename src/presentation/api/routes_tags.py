from fastapi import APIRouter, Depends

from src.application.schemas.tag import TagRead
from src.application.services.tag_service import TagService
from src.infrastructure.db.models import User
from src.presentation.api.deps import get_current_user, get_tag_service

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/", response_model=list[TagRead])
async def list_tags(
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagRead]:
    _ = current_user
    tags = await tag_service.list_tags()
    return [TagRead.model_validate(item) for item in tags]
