from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from ..dependencies import get_repository
from ..models import TrackRecord


router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=list[TrackRecord])
def list_tracks(
    query: str | None = Query(default=None, description="Free-text search against title, artist, or genre."),
    genre: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TrackRecord]:
    repository = get_repository()
    return repository.list_tracks(query=query, genre=genre, limit=limit)


@router.get("/{track_id}", response_model=TrackRecord)
def get_track(track_id: str) -> TrackRecord:
    repository = get_repository()
    return repository.get_track(track_id)


@router.get("/{track_id}/stream")
def stream_track(track_id: str) -> FileResponse:
    repository = get_repository()
    path, media_type = repository.resolve_stream_path(track_id)
    return FileResponse(path=path, media_type=media_type, filename=path.name)
