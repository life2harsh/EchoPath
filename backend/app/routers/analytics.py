from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import get_repository
from ..models import ClusterSummary, ModelSummary, SearchAlgorithmSummary


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/clusters", response_model=list[ClusterSummary])
def cluster_summaries() -> list[ClusterSummary]:
    repository = get_repository()
    return repository.cluster_summaries()


@router.get("/models", response_model=list[ModelSummary])
def model_summaries() -> list[ModelSummary]:
    repository = get_repository()
    return repository.model_summaries()


@router.get("/search", response_model=list[SearchAlgorithmSummary])
def search_summaries() -> list[SearchAlgorithmSummary]:
    repository = get_repository()
    return repository.search_summaries()
