from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from ..audio_analysis import build_uploaded_track_analysis, safe_track_slug, validate_audio_filename
from ..dependencies import get_repository
from ..models import TrackAnalysisResponse, TrackRecord


router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=list[TrackRecord])
def list_tracks(
    query: str | None = Query(default=None, description="Free-text search against title, artist, genre, or CNN/proxy signal."),
    genre: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TrackRecord]:
    repository = get_repository()
    return repository.list_tracks(query=query, genre=genre, limit=limit)


@router.post("/analyze", response_model=TrackAnalysisResponse)
async def analyze_track_upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    artist: str | None = Form(default=None),
) -> TrackAnalysisResponse:
    repository = get_repository()

    filename = file.filename or "uploaded-audio.mp3"
    try:
        validate_audio_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    suffix = Path(filename).suffix.lower()
    upload_dir = repository.settings.repo_root / "artifacts" / "uploads"
    spectrogram_dir = repository.settings.repo_root / "artifacts" / "spectrograms"
    upload_dir.mkdir(parents=True, exist_ok=True)
    spectrogram_dir.mkdir(parents=True, exist_ok=True)

    slug = safe_track_slug(title or Path(filename).stem)
    storage_name = f"{slug}-{uuid4().hex[:8]}{suffix}"
    upload_path = upload_dir / storage_name

    try:
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        upload_path.write_bytes(payload)

        # Use a temporary spectrogram path first; rename after the generated track id is known.
        temp_spectrogram_path = spectrogram_dir / f"pending-{uuid4().hex[:8]}.png"

        analysis = build_uploaded_track_analysis(
            audio_path=upload_path,
            original_filename=filename,
            title=title,
            artist=artist,
            known_tracks=repository.list_tracks(limit=100_000),
            spectrogram_path=temp_spectrogram_path,
        )

        final_spectrogram_path = spectrogram_dir / f"{analysis.track.track_id}.png"
        if temp_spectrogram_path.exists():
            temp_spectrogram_path.replace(final_spectrogram_path)

        # Add this track to the in-memory graph so it can immediately be used as
        # a playlist seed. It remains available until backend restart.
        track = analysis.track
        if track.track_id not in repository._track_index:
            repository._tracks.insert(0, track)
            repository._track_index[track.track_id] = track
            if hasattr(repository, "_neighbor_cache"):
                repository._neighbor_cache.clear()

        return analysis

    except HTTPException:
        raise
    except Exception as exc:
        if upload_path.exists():
            upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Could not analyze uploaded audio: {exc}") from exc


@router.get("/{track_id}", response_model=TrackRecord)
def get_track(track_id: str) -> TrackRecord:
    repository = get_repository()
    return repository.get_track(track_id)


@router.get("/{track_id}/stream")
def stream_track(track_id: str) -> FileResponse:
    repository = get_repository()
    path, media_type = repository.resolve_stream_path(track_id)
    return FileResponse(path=path, media_type=media_type, filename=path.name)


@router.get("/{track_id}/spectrogram")
def get_track_spectrogram(track_id: str) -> FileResponse:
    repository = get_repository()
    path = repository.settings.repo_root / "artifacts" / "spectrograms" / f"{track_id}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Spectrogram is not available for this track")
    return FileResponse(path=path, media_type="image/png", filename=path.name)
