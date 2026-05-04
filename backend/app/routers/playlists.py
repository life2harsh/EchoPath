from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from ..dependencies import get_repository
from ..models import PlaylistRequest, PlaylistResult


router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post("/generate", response_model=PlaylistResult)
def generate_playlist(request: PlaylistRequest) -> PlaylistResult:
    repository = get_repository()
    return repository.generate_playlist(request)


@router.get("/{playlist_id}", response_model=PlaylistResult)
def get_playlist(playlist_id: str) -> PlaylistResult:
    repository = get_repository()
    return repository.get_playlist(playlist_id)


@router.get("/{playlist_id}/export")
def export_playlist(playlist_id: str, format: str = Query(default="json", alias="format")):
    repository = get_repository()
    payload = repository.export_playlist(playlist_id, format)
    if format == "m3u":
        return PlainTextResponse(payload, media_type="audio/x-mpegurl")
    return JSONResponse(payload)
