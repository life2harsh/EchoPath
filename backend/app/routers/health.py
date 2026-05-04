from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..dependencies import get_repository
from ..models import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def read_health() -> HealthResponse:
    settings = get_settings()
    repository = get_repository()
    return HealthResponse(status="ok", app_name=settings.app_name, dataset=repository.dataset_status)
