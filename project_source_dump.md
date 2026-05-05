# Project Source Dump

## File Tree

```text
aimlpbl/
├── clustering.py
├── feature_extraction.py
├── main.py
├── README.md
├── test_audio.py
├── artifacts
│   └── sample-data
│       └── demo_library.json
├── backend
│   ├── pyproject.toml
│   ├── app
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── routers
│   │       ├── __init__.py
│   │       ├── analytics.py
│   │       ├── health.py
│   │       ├── playlists.py
│   │       └── tracks.py
│   ├── echopath_backend.egg-info
│   │   ├── dependency_links.txt
│   │   ├── requires.txt
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   └── tests
│       └── test_api.py
├── fma_small
│   └── README.txt
├── frontend
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.d.ts
│   ├── vite.config.js
│   ├── vite.config.ts
│   └── src
│       ├── App.tsx
│       ├── main.tsx
│       ├── styles.css
│       ├── vite-env.d.ts
│       ├── components
│       │   ├── AudioPreview.tsx
│       │   ├── SectionCard.tsx
│       │   ├── Shell.tsx
│       │   └── TrackCard.tsx
│       ├── lib
│       │   ├── api.ts
│       │   ├── format.ts
│       │   └── types.ts
│       └── pages
│           ├── AnalyticsPage.tsx
│           ├── BuilderPage.tsx
│           ├── LibraryPage.tsx
│           └── ResultsPage.tsx
└── training
    ├── pyproject.toml
    ├── echopath
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── cli.py
    │   ├── config.py
    │   └── commands
    │       ├── __init__.py
    │       ├── benchmark_search.py
    │       ├── ingest.py
    │       ├── train_classical.py
    │       └── train_cnn.py
    └── echopath_training.egg-info
        ├── dependency_links.txt
        ├── entry_points.txt
        ├── requires.txt
        ├── SOURCES.txt
        └── top_level.txt
```

## Files

./artifacts/sample-data/demo_library.json
```json
[
  {
    "track_id": "dawn-receiver",
    "title": "Dawn Receiver",
    "artist": "Mirra Vale",
    "duration_sec": 248,
    "genre_label": "ambient",
    "cluster_id": 0,
    "energy": 0.22,
    "tempo": 76.0,
    "valence": 0.38,
    "explicit": false,
    "audio_path": null,
    "summary": "A low-light opener with gentle pads and slow harmonic motion."
  },
  {
    "track_id": "amber-signal",
    "title": "Amber Signal",
    "artist": "North Arcade",
    "duration_sec": 214,
    "genre_label": "chillhop",
    "cluster_id": 0,
    "energy": 0.34,
    "tempo": 88.0,
    "valence": 0.49,
    "explicit": false,
    "audio_path": null,
    "summary": "Warm drums and dusty keys that keep the mood grounded but moving."
  },
  {
    "track_id": "glass-arteries",
    "title": "Glass Arteries",
    "artist": "Static Bloom",
    "duration_sec": 201,
    "genre_label": "indie-electronic",
    "cluster_id": 1,
    "energy": 0.51,
    "tempo": 104.0,
    "valence": 0.53,
    "explicit": false,
    "audio_path": null,
    "summary": "A clean bridge track with brighter synth textures and a firmer pulse."
  },
  {
    "track_id": "velvet-parallel",
    "title": "Velvet Parallel",
    "artist": "Luna Morn",
    "duration_sec": 227,
    "genre_label": "neo-soul",
    "cluster_id": 1,
    "energy": 0.46,
    "tempo": 98.0,
    "valence": 0.61,
    "explicit": false,
    "audio_path": null,
    "summary": "Smooth vocal phrasing and restrained percussion keep the playlist breathable."
  },
  {
    "track_id": "night-circuit",
    "title": "Night Circuit",
    "artist": "Chromeline",
    "duration_sec": 236,
    "genre_label": "synthwave",
    "cluster_id": 2,
    "energy": 0.68,
    "tempo": 116.0,
    "valence": 0.58,
    "explicit": false,
    "audio_path": null,
    "summary": "Mid-tempo neon propulsion that makes a clean jump into more assertive territory."
  },
  {
    "track_id": "delta-runner",
    "title": "Delta Runner",
    "artist": "Chrome Habitat",
    "duration_sec": 244,
    "genre_label": "house",
    "cluster_id": 2,
    "energy": 0.74,
    "tempo": 122.0,
    "valence": 0.66,
    "explicit": false,
    "audio_path": null,
    "summary": "Higher energy four-on-the-floor momentum for upward-trending sets."
  },
  {
    "track_id": "midnight-map",
    "title": "Midnight Map",
    "artist": "Cinder Coast",
    "duration_sec": 289,
    "genre_label": "post-rock",
    "cluster_id": 1,
    "energy": 0.44,
    "tempo": 92.0,
    "valence": 0.34,
    "explicit": false,
    "audio_path": null,
    "summary": "Broader cinematic texture that can cool things down without going static."
  },
  {
    "track_id": "tidal-vault",
    "title": "Tidal Vault",
    "artist": "Signal Choir",
    "duration_sec": 193,
    "genre_label": "drum-and-bass",
    "cluster_id": 3,
    "energy": 0.9,
    "tempo": 168.0,
    "valence": 0.57,
    "explicit": false,
    "audio_path": null,
    "summary": "A high-velocity peak-state option for ambitious mood climbs."
  },
  {
    "track_id": "ultraviolet-letters",
    "title": "Ultraviolet Letters",
    "artist": "Ari Phae",
    "duration_sec": 219,
    "genre_label": "alt-pop",
    "cluster_id": 2,
    "energy": 0.63,
    "tempo": 112.0,
    "valence": 0.71,
    "explicit": false,
    "audio_path": null,
    "summary": "A bright pop edge that works when the set needs more lift and payoff."
  },
  {
    "track_id": "echo-river",
    "title": "Echo River",
    "artist": "Blue Hour Unit",
    "duration_sec": 265,
    "genre_label": "jazz-hop",
    "cluster_id": 0,
    "energy": 0.29,
    "tempo": 84.0,
    "valence": 0.44,
    "explicit": false,
    "audio_path": null,
    "summary": "A textured, late-night groove that pairs well with reflective openings."
  },
  {
    "track_id": "saffron-grid",
    "title": "Saffron Grid",
    "artist": "Analog Current",
    "duration_sec": 232,
    "genre_label": "synthwave",
    "cluster_id": 2,
    "energy": 0.71,
    "tempo": 118.0,
    "valence": 0.64,
    "explicit": false,
    "audio_path": null,
    "summary": "A close cousin to the synthwave target, useful for smooth end-state convergence."
  },
  {
    "track_id": "quartz-ember",
    "title": "Quartz Ember",
    "artist": "Frame District",
    "duration_sec": 208,
    "genre_label": "indie-electronic",
    "cluster_id": 3,
    "energy": 0.82,
    "tempo": 132.0,
    "valence": 0.59,
    "explicit": false,
    "audio_path": null,
    "summary": "Aggressive upper-mid energy that can bridge between danceable and urgent."
  }
]
```

./backend/app/__init__.py
```python
"""EchoPath backend application package."""
```

./backend/app/config.py
```python
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    repo_root: Path
    sample_data_path: Path
    dataset_manifest_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[2]
    default_manifest = repo_root / "data" / "library" / "tracks.json"
    manifest_value = os.getenv("ECHOPATH_LIBRARY_PATH", str(default_manifest))

    return Settings(
        app_name="EchoPath API",
        repo_root=repo_root,
        sample_data_path=repo_root / "artifacts" / "sample-data" / "demo_library.json",
        dataset_manifest_path=Path(manifest_value).expanduser(),
    )
```

./backend/app/dependencies.py
```python
from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .repository import Repository


@lru_cache(maxsize=1)
def get_repository() -> Repository:
    return Repository(get_settings())
```

./backend/app/main.py
```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .dependencies import get_repository
from .routers import analytics, health, playlists, tracks

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.repository = get_repository()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tracks.router)
    app.include_router(playlists.router)
    app.include_router(analytics.router)
    return app


app = create_app()
```

./backend/app/models.py
```python
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


AlgorithmName = Literal["bfs", "dfs", "ucs", "ids", "astar", "idastar"]
TargetType = Literal["genre", "cluster"]
TempoPolicy = Literal["any", "steady", "lift", "cooldown"]


class TrackRecord(BaseModel):
    track_id: str
    title: str
    artist: str
    duration_sec: int = Field(ge=1)
    genre_label: str | None = None
    cluster_id: int | None = None
    energy: float | None = Field(default=None, ge=0.0, le=1.0)
    tempo: float | None = Field(default=None, ge=0.0)
    valence: float | None = Field(default=None, ge=0.0, le=1.0)
    explicit: bool = False
    audio_path: str | None = None
    stream_url: str | None = None
    spectrogram_url: str | None = None
    summary: str | None = None


class ConstraintSet(BaseModel):
    artist_repeat_limit: int = Field(default=1, ge=1, le=3)
    explicit_filter: bool = True
    tempo_policy: TempoPolicy = "any"


class PlaylistRequest(BaseModel):
    seed_track_id: str
    target_type: TargetType
    target_value: str
    algorithm: AlgorithmName = "astar"
    playlist_length: int = Field(default=5, ge=3, le=12)
    max_total_duration_sec: int | None = Field(default=None, ge=60)
    constraints: ConstraintSet = Field(default_factory=ConstraintSet)
    personalization_profile: str | None = None


class PlaylistStep(BaseModel):
    order: int
    track: TrackRecord
    edge_cost: float = Field(ge=0.0)
    explanation: str


class PlaylistResult(BaseModel):
    playlist_id: str
    algorithm: AlgorithmName
    target_type: TargetType
    target_value: str
    total_cost: float = Field(ge=0.0)
    runtime_ms: float = Field(ge=0.0)
    nodes_expanded: int = Field(ge=0)
    target_hit: bool
    constraint_summary: str
    explanation: str
    steps: list[PlaylistStep]


class ClusterSummary(BaseModel):
    cluster_id: int
    size: int
    avg_tempo: float
    avg_energy: float
    avg_valence: float
    anchor_genres: list[str]
    descriptor: str


class ModelSummary(BaseModel):
    model_name: str
    family: Literal["classical", "cnn"]
    status: Literal["planned", "ready", "trained"]
    notes: str


class SearchAlgorithmSummary(BaseModel):
    algorithm: AlgorithmName
    readiness: Literal["wired", "planned", "benchmarked"]
    notes: str


class DatasetStatus(BaseModel):
    source: str
    using_sample_data: bool
    track_count: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app_name: str
    dataset: DatasetStatus
```

./backend/app/repository.py
```python
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import heapq
import json
import mimetypes
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException

from .config import Settings
from .models import (
    ClusterSummary,
    DatasetStatus,
    ModelSummary,
    PlaylistRequest,
    PlaylistResult,
    PlaylistStep,
    SearchAlgorithmSummary,
    TrackRecord,
)


MAX_EXPANSIONS = 3_000
NEIGHBOR_LIMIT = 6


@dataclass
class SearchOutcome:
    path: list[str]
    cost: float
    nodes_expanded: int
    target_hit: bool


class Repository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tracks: list[TrackRecord] = []
        self._track_index: dict[str, TrackRecord] = {}
        self._playlists: dict[str, PlaylistResult] = {}
        self.reload()

    def reload(self) -> None:
        data_path, using_sample = self._resolve_library_path()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        raw_tracks = [TrackRecord.model_validate(item) for item in payload]

        self._tracks = [self._attach_urls(track) for track in raw_tracks]
        self._track_index = {track.track_id: track for track in self._tracks}
        self._dataset_status = DatasetStatus(
            source=str(data_path),
            using_sample_data=using_sample,
            track_count=len(self._tracks),
        )

    def _resolve_library_path(self) -> tuple[Path, bool]:
        manifest = self.settings.dataset_manifest_path
        if manifest.exists():
            return manifest, False
        if self.settings.sample_data_path.exists():
            return self.settings.sample_data_path, True
        raise FileNotFoundError(
            f"No dataset manifest found at {manifest} and sample data is missing."
        )

    def _attach_urls(self, track: TrackRecord) -> TrackRecord:
        stream_url = None
        if track.audio_path:
            stream_url = f"/tracks/{track.track_id}/stream"
        spectrogram_url = track.spectrogram_url or None
        return track.model_copy(update={"stream_url": stream_url, "spectrogram_url": spectrogram_url})

    @property
    def dataset_status(self) -> DatasetStatus:
        return self._dataset_status

    def list_tracks(self, query: str | None = None, genre: str | None = None, limit: int = 100) -> list[TrackRecord]:
        tracks = self._tracks
        if query:
            needle = query.lower().strip()
            tracks = [
                track
                for track in tracks
                if needle in track.title.lower()
                or needle in track.artist.lower()
                or (track.genre_label and needle in track.genre_label.lower())
            ]
        if genre:
            tracks = [track for track in tracks if track.genre_label == genre]
        return tracks[:limit]

    def list_genres(self) -> list[str]:
        return sorted({track.genre_label for track in self._tracks if track.genre_label})

    def get_track(self, track_id: str) -> TrackRecord:
        track = self._track_index.get(track_id)
        if not track:
            raise HTTPException(status_code=404, detail=f"Track '{track_id}' not found")
        return track

    def resolve_stream_path(self, track_id: str) -> tuple[Path, str]:
        track = self.get_track(track_id)
        if not track.audio_path:
            raise HTTPException(status_code=404, detail="Audio is not available for this track yet")

        path = Path(track.audio_path)
        if not path.is_absolute():
            path = (self.settings.repo_root / path).resolve()

        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Audio file not found at {path}")

        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return path, media_type

    def get_playlist(self, playlist_id: str) -> PlaylistResult:
        playlist = self._playlists.get(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail=f"Playlist '{playlist_id}' not found")
        return playlist

    def export_playlist(self, playlist_id: str, fmt: str) -> str | dict[str, object]:
        playlist = self.get_playlist(playlist_id)
        if fmt == "json":
            return playlist.model_dump(mode="json")

        if fmt != "m3u":
            raise HTTPException(status_code=400, detail="Supported formats are 'json' and 'm3u'")

        lines = ["#EXTM3U"]
        for step in playlist.steps:
            track = step.track
            lines.append(f"#EXTINF:{track.duration_sec},{track.artist} - {track.title}")
            lines.append(track.audio_path or f"# Missing audio for {track.track_id}")
        return "\n".join(lines)

    def generate_playlist(self, request: PlaylistRequest) -> PlaylistResult:
        seed = self.get_track(request.seed_track_id)
        start = perf_counter()

        strategy = {
            "bfs": self._search_bfs,
            "dfs": self._search_dfs,
            "ucs": self._search_ucs,
            "ids": self._search_ids,
            "astar": self._search_astar,
            "idastar": self._search_idastar,
        }[request.algorithm]

        outcome = strategy(seed.track_id, request)
        if outcome is None:
            outcome = self._greedy_fallback(seed.track_id, request)

        runtime_ms = round((perf_counter() - start) * 1000, 2)
        playlist_id = uuid4().hex[:10]
        steps = self._build_playlist_steps(outcome.path)
        result = PlaylistResult(
            playlist_id=playlist_id,
            algorithm=request.algorithm,
            target_type=request.target_type,
            target_value=request.target_value,
            total_cost=round(outcome.cost, 4),
            runtime_ms=runtime_ms,
            nodes_expanded=outcome.nodes_expanded,
            target_hit=outcome.target_hit,
            constraint_summary=self._summarize_constraints(request),
            explanation=self._playlist_explanation(request, outcome.target_hit),
            steps=steps,
        )
        self._playlists[playlist_id] = result
        return result

    def cluster_summaries(self) -> list[ClusterSummary]:
        by_cluster: dict[int, list[TrackRecord]] = {}
        for track in self._tracks:
            if track.cluster_id is None:
                continue
            by_cluster.setdefault(track.cluster_id, []).append(track)

        summaries: list[ClusterSummary] = []
        for cluster_id, tracks in sorted(by_cluster.items()):
            tempos = [track.tempo or 0.0 for track in tracks]
            energies = [track.energy or 0.0 for track in tracks]
            valences = [track.valence or 0.0 for track in tracks]
            anchor_genres = [
                genre
                for genre, _ in Counter(track.genre_label or "unknown" for track in tracks).most_common(3)
            ]
            descriptor = self._describe_cluster(sum(energies) / len(energies), sum(valences) / len(valences))
            summaries.append(
                ClusterSummary(
                    cluster_id=cluster_id,
                    size=len(tracks),
                    avg_tempo=round(sum(tempos) / len(tempos), 1),
                    avg_energy=round(sum(energies) / len(energies), 2),
                    avg_valence=round(sum(valences) / len(valences), 2),
                    anchor_genres=anchor_genres,
                    descriptor=descriptor,
                )
            )
        return summaries

    def model_summaries(self) -> list[ModelSummary]:
        return [
            ModelSummary(
                model_name="Logistic Regression",
                family="classical",
                status="ready",
                notes="Wired into the project structure and waiting for real feature matrices.",
            ),
            ModelSummary(
                model_name="Random Forest",
                family="classical",
                status="ready",
                notes="Reserved for proxy preference modeling once track-level labels are extracted.",
            ),
            ModelSummary(
                model_name="LeNet Spectrogram CNN",
                family="cnn",
                status="planned",
                notes="Will be the smallest PyTorch baseline for quick GPU sanity checks.",
            ),
            ModelSummary(
                model_name="VGG-style Spectrogram CNN",
                family="cnn",
                status="planned",
                notes="Intended for deeper convolutional comparisons on mel-spectrogram images.",
            ),
            ModelSummary(
                model_name="ResNet-style Spectrogram CNN",
                family="cnn",
                status="planned",
                notes="Planned as the strongest architecture for final report comparisons and heuristics.",
            ),
        ]

    def search_summaries(self) -> list[SearchAlgorithmSummary]:
        return [
            SearchAlgorithmSummary(
                algorithm=algorithm,
                readiness="wired",
                notes="Implemented against the shared similarity graph and ready for real benchmarks."
                if algorithm in {"bfs", "dfs", "ucs", "ids", "astar", "idastar"}
                else "",
            )
            for algorithm in ("bfs", "dfs", "ucs", "ids", "astar", "idastar")
        ]

    def _build_playlist_steps(self, path: list[str]) -> list[PlaylistStep]:
        steps: list[PlaylistStep] = []
        previous: TrackRecord | None = None
        for index, track_id in enumerate(path, start=1):
            track = self.get_track(track_id)
            edge_cost = 0.0 if previous is None else round(self._edge_cost(previous, track, "any"), 4)
            explanation = (
                "Seed track anchors the path."
                if previous is None
                else self._transition_explanation(previous, track)
            )
            steps.append(PlaylistStep(order=index, track=track, edge_cost=edge_cost, explanation=explanation))
            previous = track
        return steps

    def _transition_explanation(self, previous: TrackRecord, current: TrackRecord) -> str:
        tempo_delta = abs((previous.tempo or 0.0) - (current.tempo or 0.0))
        energy_delta = abs((previous.energy or 0.0) - (current.energy or 0.0))
        cluster_phrase = (
            "stays in the same mood cluster"
            if previous.cluster_id == current.cluster_id
            else f"moves from cluster {previous.cluster_id} to {current.cluster_id}"
        )
        genre_phrase = (
            f"keeps the {current.genre_label} lane"
            if previous.genre_label == current.genre_label
            else f"crossfades toward {current.genre_label or 'a new texture'}"
        )
        return (
            f"{cluster_phrase}, {genre_phrase}, tempo shift {tempo_delta:.1f} BPM, "
            f"energy delta {energy_delta:.2f}."
        )

    def _playlist_explanation(self, request: PlaylistRequest, target_hit: bool) -> str:
        target_text = f"{request.target_type} '{request.target_value}'"
        if target_hit:
            return (
                f"The path reaches the requested {target_text} while preserving "
                f"{request.constraints.tempo_policy} tempo movement and the artist repetition cap."
            )
        return (
            f"The current sample library could not fully hit {target_text}, so the generator returned "
            f"the smoothest feasible approximation under the active constraints."
        )

    def _summarize_constraints(self, request: PlaylistRequest) -> str:
        explicit = "explicit tracks removed" if request.constraints.explicit_filter else "explicit tracks allowed"
        duration = (
            f"max {request.max_total_duration_sec // 60} min"
            if request.max_total_duration_sec
            else "no duration cap"
        )
        return (
            f"artist repeat <= {request.constraints.artist_repeat_limit}, "
            f"{explicit}, tempo policy {request.constraints.tempo_policy}, {duration}"
        )

    def _search_bfs(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        queue = deque([(seed_track_id, [seed_track_id], 0.0)])
        expansions = 0
        while queue and expansions < MAX_EXPANSIONS:
            _, path, cost = queue.popleft()
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                queue.append((neighbor.track_id, path + [neighbor.track_id], cost + self._edge_cost(last, neighbor, request.constraints.tempo_policy)))
        return None

    def _search_dfs(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        stack = [(seed_track_id, [seed_track_id], 0.0)]
        expansions = 0
        while stack and expansions < MAX_EXPANSIONS:
            _, path, cost = stack.pop()
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in reversed(self._neighbors(last, path, request)):
                next_cost = cost + self._edge_cost(last, neighbor, request.constraints.tempo_policy)
                stack.append((neighbor.track_id, path + [neighbor.track_id], next_cost))
        return None

    def _search_ucs(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        heap: list[tuple[float, int, list[str]]] = [(0.0, 0, [seed_track_id])]
        expansions = 0
        sequence = 0
        while heap and expansions < MAX_EXPANSIONS:
            cost, _, path = heapq.heappop(heap)
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                sequence += 1
                next_cost = cost + self._edge_cost(last, neighbor, request.constraints.tempo_policy)
                heapq.heappush(heap, (next_cost, sequence, path + [neighbor.track_id]))
        return None

    def _search_astar(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        heap: list[tuple[float, float, int, list[str]]] = []
        sequence = 0
        start_h = self._heuristic(self.get_track(seed_track_id), [seed_track_id], request)
        heapq.heappush(heap, (start_h, 0.0, sequence, [seed_track_id]))
        expansions = 0

        while heap and expansions < MAX_EXPANSIONS:
            _, cost, _, path = heapq.heappop(heap)
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                sequence += 1
                edge = self._edge_cost(last, neighbor, request.constraints.tempo_policy)
                next_path = path + [neighbor.track_id]
                next_cost = cost + edge
                priority = next_cost + self._heuristic(neighbor, next_path, request)
                heapq.heappush(heap, (priority, next_cost, sequence, next_path))
        return None

    def _search_ids(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        expansions = 0
        max_depth = request.playlist_length

        def depth_limited(path: list[str], depth_limit: int, cost: float) -> SearchOutcome | None:
            nonlocal expansions
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)
            if len(path) >= depth_limit:
                return None

            last = self.get_track(path[-1])
            expansions += 1
            if expansions >= MAX_EXPANSIONS:
                return None

            for neighbor in self._neighbors(last, path, request):
                next_cost = cost + self._edge_cost(last, neighbor, request.constraints.tempo_policy)
                found = depth_limited(path + [neighbor.track_id], depth_limit, next_cost)
                if found is not None:
                    return found
            return None

        for depth in range(2, max_depth + 1):
            found = depth_limited([seed_track_id], depth, 0.0)
            if found is not None:
                return found
        return None

    def _search_idastar(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        seed = self.get_track(seed_track_id)
        threshold = self._heuristic(seed, [seed_track_id], request)
        expansions = 0

        def visit(path: list[str], g_cost: float, bound: float) -> tuple[SearchOutcome | None, float]:
            nonlocal expansions
            last = self.get_track(path[-1])
            f_cost = g_cost + self._heuristic(last, path, request)
            if f_cost > bound:
                return None, f_cost
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=g_cost, nodes_expanded=expansions, target_hit=True), f_cost

            minimum = float("inf")
            expansions += 1
            if expansions >= MAX_EXPANSIONS:
                return None, minimum

            for neighbor in self._neighbors(last, path, request):
                edge = self._edge_cost(last, neighbor, request.constraints.tempo_policy)
                result, candidate_bound = visit(path + [neighbor.track_id], g_cost + edge, bound)
                if result is not None:
                    return result, candidate_bound
                minimum = min(minimum, candidate_bound)
            return None, minimum

        while expansions < MAX_EXPANSIONS:
            result, next_threshold = visit([seed_track_id], 0.0, threshold)
            if result is not None:
                return result
            if next_threshold == float("inf"):
                return None
            threshold = next_threshold
        return None

    def _greedy_fallback(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome:
        path = [seed_track_id]
        total_cost = 0.0
        expansions = 0
        while len(path) < request.playlist_length:
            last = self.get_track(path[-1])
            neighbors = self._neighbors(last, path, request)
            if not neighbors:
                break
            best = neighbors[0]
            total_cost += self._edge_cost(last, best, request.constraints.tempo_policy)
            path.append(best.track_id)
            expansions += 1

        target_hit = self._matches_target(self.get_track(path[-1]), request)
        return SearchOutcome(path=path, cost=total_cost, nodes_expanded=expansions, target_hit=target_hit)

    def _is_goal(self, path: list[str], request: PlaylistRequest) -> bool:
        if len(path) != request.playlist_length:
            return False
        final_track = self.get_track(path[-1])
        return self._matches_target(final_track, request)

    def _matches_target(self, track: TrackRecord, request: PlaylistRequest) -> bool:
        if request.target_type == "genre":
            return track.genre_label == request.target_value
        try:
            return track.cluster_id == int(request.target_value)
        except ValueError:
            return False

    def _neighbors(self, current: TrackRecord, path: list[str], request: PlaylistRequest) -> list[TrackRecord]:
        candidates = [
            track
            for track in self._tracks
            if self._can_add_to_path(track, path, request)
        ]
        ranked = sorted(
            candidates,
            key=lambda track: (
                self._edge_cost(current, track, request.constraints.tempo_policy)
                + self._target_penalty(track, request) * 0.4
            ),
        )
        return ranked[:NEIGHBOR_LIMIT]

    def _can_add_to_path(self, track: TrackRecord, path: list[str], request: PlaylistRequest) -> bool:
        if track.track_id in path:
            return False
        if request.constraints.explicit_filter and track.explicit:
            return False

        artists = Counter(self.get_track(track_id).artist for track_id in path)
        if artists[track.artist] >= request.constraints.artist_repeat_limit:
            return False

        if request.max_total_duration_sec:
            current_total = sum(self.get_track(track_id).duration_sec for track_id in path)
            if current_total + track.duration_sec > request.max_total_duration_sec:
                return False

        return True

    def _heuristic(self, track: TrackRecord, path: list[str], request: PlaylistRequest) -> float:
        remaining = max(request.playlist_length - len(path), 0)
        return self._target_penalty(track, request) + remaining * 0.08

    def _target_penalty(self, track: TrackRecord, request: PlaylistRequest) -> float:
        if request.target_type == "genre":
            return 0.0 if track.genre_label == request.target_value else 0.75
        try:
            target_cluster = int(request.target_value)
        except ValueError:
            return 1.0
        if track.cluster_id is None:
            return 1.0
        return abs(track.cluster_id - target_cluster) * 0.35

    def _edge_cost(self, source: TrackRecord, target: TrackRecord, tempo_policy: str) -> float:
        tempo_delta = abs((source.tempo or 0.0) - (target.tempo or 0.0)) / 120.0
        energy_delta = abs((source.energy or 0.0) - (target.energy or 0.0))
        valence_delta = abs((source.valence or 0.0) - (target.valence or 0.0))
        genre_penalty = 0.0 if source.genre_label == target.genre_label else 0.18
        cluster_penalty = 0.0 if source.cluster_id == target.cluster_id else 0.1

        policy_penalty = 0.0
        if tempo_policy == "steady":
            policy_penalty = tempo_delta * 0.6
        elif tempo_policy == "lift":
            policy_penalty = max(0.0, (source.tempo or 0.0) - (target.tempo or 0.0)) / 120.0
        elif tempo_policy == "cooldown":
            policy_penalty = max(0.0, (target.tempo or 0.0) - (source.tempo or 0.0)) / 120.0

        return 0.45 * tempo_delta + 0.30 * energy_delta + 0.20 * valence_delta + genre_penalty + cluster_penalty + policy_penalty

    def _describe_cluster(self, energy: float, valence: float) -> str:
        if energy < 0.4 and valence < 0.5:
            return "reflective and low-lit"
        if energy < 0.5:
            return "steady and spacious"
        if valence > 0.6:
            return "bright and forward-moving"
        return "driving with a little tension"
```

./backend/app/routers/__init__.py
```python
"""API router modules for EchoPath."""
```

./backend/app/routers/analytics.py
```python
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
```

./backend/app/routers/health.py
```python
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
```

./backend/app/routers/playlists.py
```python
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
```

./backend/app/routers/tracks.py
```python
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
```

./backend/echopath_backend.egg-info/dependency_links.txt
```

```

./backend/echopath_backend.egg-info/requires.txt
```
fastapi<1.0,>=0.115
uvicorn[standard]<1.0,>=0.32
pydantic<3.0,>=2.9

[dev]
httpx<1.0,>=0.28
pytest<9.0,>=8.3
```

./backend/echopath_backend.egg-info/SOURCES.txt
```
pyproject.toml
app/__init__.py
app/config.py
app/dependencies.py
app/main.py
app/models.py
app/repository.py
app/routers/__init__.py
app/routers/analytics.py
app/routers/health.py
app/routers/playlists.py
app/routers/tracks.py
echopath_backend.egg-info/PKG-INFO
echopath_backend.egg-info/SOURCES.txt
echopath_backend.egg-info/dependency_links.txt
echopath_backend.egg-info/requires.txt
echopath_backend.egg-info/top_level.txt
tests/test_api.py
```

./backend/echopath_backend.egg-info/top_level.txt
```
app
```

./backend/pyproject.toml
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "echopath-backend"
version = "0.1.0"
description = "FastAPI backend for the EchoPath playlist generation project."
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.32,<1.0",
  "pydantic>=2.9,<3.0",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.28,<1.0",
  "pytest>=8.3,<9.0",
]

[tool.setuptools]
packages = ["app", "app.routers"]
```

./backend/tests/test_api.py
```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["dataset"]["track_count"] >= 1


def test_track_listing() -> None:
    response = client.get("/tracks", params={"query": "amber"})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any("Amber" in track["title"] for track in payload)


def test_playlist_generation() -> None:
    seed_track_id = client.get("/tracks").json()[0]["track_id"]
    response = client.post(
        "/playlists/generate",
        json={
            "seed_track_id": seed_track_id,
            "target_type": "genre",
            "target_value": "synthwave",
            "algorithm": "astar",
            "playlist_length": 5,
            "constraints": {
                "artist_repeat_limit": 1,
                "explicit_filter": True,
                "tempo_policy": "lift",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["playlist_id"]
    assert len(payload["steps"]) >= 3
```

./clustering.py
```python
import json
import numpy as np
from sklearn.cluster import KMeans

INPUT_FILE = "data/library/tracks_updated.json"
OUTPUT_FILE = "data/library/tracks_clustered.json"

# Load data
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

X = []
valid_indices = []

# Extract usable features
for i, track in enumerate(data):
    tempo = track.get("tempo", 0)
    energy = track.get("energy", 0)
    valence = track.get("valence", 0)

    if tempo > 0:
        X.append([tempo, energy, valence])
        valid_indices.append(i)

X = np.array(X)

print(f"Using {len(X)} tracks for clustering")

# KMeans
kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(X)

# Assign cluster IDs
for idx, label in zip(valid_indices, labels):
    data[idx]["cluster_id"] = int(label)

# Save output
with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Clustering complete!")
print(f"Saved to: {OUTPUT_FILE}")
```

./feature_extraction.py
```python
import json
import librosa
import numpy as np
from tqdm import tqdm

INPUT_FILE = "data/library/tracks.json"
OUTPUT_FILE = "data/library/tracks_updated.json"

def extract_features(audio_path):
    try:
        # Load audio safely (force mono)
        y, sr = librosa.load(audio_path, duration=30, mono=True)

        if y is None or len(y) == 0:
            print(f"Empty audio: {audio_path}")
            return 0.0, 0.0, 0.0

        # Ensure it's 1D
        y = np.asarray(y).flatten()

        # Tempo
        tempo = librosa.beat.tempo(y=y, sr=sr)
        tempo = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)

        # Energy (RMS)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms)) if rms is not None else 0.0

        # Valence approximation
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        valence = float(np.mean(spec_centroid) / 5000) if spec_centroid is not None else 0.0

        print(f"✔ {audio_path} | tempo={tempo:.2f}, energy={energy:.4f}")

        return tempo, energy, valence

    except Exception as e:
        print(f"❌ Error processing {audio_path}: {e}")
        return 0.0, 0.0, 0.0

def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    updated_data = []

    for track in tqdm(data):
        audio_path = track.get("path")

        tempo, energy, valence = extract_features(audio_path)

        updated_track = {
            "track_id": track["track_id"],
            "title": track["title"],
            "artist": track.get("artist", "Unknown"),

            # FIXED FIELD NAMES
            "genre_label": track.get("genre", "unknown"),
            "duration_sec": track.get("duration_sec", 180),
            "audio_path": audio_path,

            # NEW FEATURES
            "tempo": tempo,
            "energy": energy,
            "valence": valence,

            # TEMP DEFAULT (we'll fix in Step 2)
            "cluster_id": 0,

            "explicit": False
        }

        updated_data.append(updated_track)
        # Save progress every 50 tracks
        if len(updated_data) % 50 == 0:
         with open(OUTPUT_FILE, "w") as f:
          json.dump(updated_data, f, indent=2)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(updated_data, f, indent=2)

    print("\n✅ Feature extraction complete!")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

./fma_small/README.txt
```
This .zip archive is part of the FMA, a dataset for music analysis.
Code & data: https://github.com/mdeff/fma
Paper: https://arxiv.org/abs/1612.01840

Each .mp3 is licensed by its artist.

The content's integrity can be verified with sha1sum -c checksums.
```

./frontend/index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>EchoPath</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

./frontend/package.json
```json
{
  "name": "echopath-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.80.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.20",
    "@types/react-dom": "^18.3.7",
    "@vitejs/plugin-react": "^4.5.2",
    "typescript": "^5.8.3",
    "vite": "^5.4.19"
  }
}
```

./frontend/src/App.tsx
```tsx
import { Route, Routes } from "react-router-dom";

import { Shell } from "./components/Shell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { BuilderPage } from "./pages/BuilderPage";
import { LibraryPage } from "./pages/LibraryPage";
import { ResultsPage } from "./pages/ResultsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Shell />}>
        <Route index element={<LibraryPage />} />
        <Route path="/builder" element={<BuilderPage />} />
        <Route path="/results">
          <Route path=":playlistId" element={<ResultsPage />} />
          <Route index element={<ResultsPage />} />
        </Route>
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  );
}
```

./frontend/src/components/AudioPreview.tsx
```tsx
import { buildStreamUrl } from "../lib/api";
import { formatDuration } from "../lib/format";
import type { TrackRecord } from "../lib/types";

interface AudioPreviewProps {
  track: TrackRecord | null;
}

export function AudioPreview({ track }: AudioPreviewProps) {
  if (!track) {
    return (
      <div className="preview-card preview-card--empty">
        <p>Select a track to inspect its metadata and preview surface.</p>
      </div>
    );
  }

  const streamUrl = buildStreamUrl(track);

  return (
    <div className="preview-card">
      <div className="preview-card__hero">
        <div>
          <p className="eyebrow">Selected Track</p>
          <h2>{track.title}</h2>
          <p className="preview-card__artist">{track.artist}</p>
        </div>
        <div className="pill-row">
          <span className="pill">{track.genre_label ?? "Genre pending"}</span>
          <span className="pill">Cluster {track.cluster_id ?? "?"}</span>
          <span className="pill">{formatDuration(track.duration_sec)}</span>
        </div>
      </div>

      <div className="preview-stats">
        <div>
          <strong>{track.tempo?.toFixed(0) ?? "--"}</strong>
          <span>Tempo</span>
        </div>
        <div>
          <strong>{track.energy?.toFixed(2) ?? "--"}</strong>
          <span>Energy</span>
        </div>
        <div>
          <strong>{track.valence?.toFixed(2) ?? "--"}</strong>
          <span>Valence</span>
        </div>
      </div>

      <p className="preview-card__summary">
        {track.summary ??
          "This slot is ready for waveform, spectrogram, and embedding explanations once the real dataset is loaded."}
      </p>

      {streamUrl ? (
        <audio key={track.track_id} controls className="audio-player" src={streamUrl}>
          Your browser does not support audio playback.
        </audio>
      ) : (
        <div className="preview-card__notice">
          Audio files are not wired yet for this sample library. The stream endpoint is ready for the real dataset.
        </div>
      )}
    </div>
  );
}
```

./frontend/src/components/SectionCard.tsx
```tsx
import type { PropsWithChildren, ReactNode } from "react";

interface SectionCardProps extends PropsWithChildren {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function SectionCard({ eyebrow, title, subtitle, actions, children }: SectionCardProps) {
  return (
    <section className="section-card">
      <div className="section-card__header">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2>{title}</h2>
          {subtitle ? <p className="section-card__subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="section-card__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
```

./frontend/src/components/Shell.tsx
```tsx
import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";

import { fetchHealth } from "../lib/api";

const navItems = [
  { to: "/", label: "Library" },
  { to: "/builder", label: "Builder" },
  { to: "/results", label: "Results" },
  { to: "/analytics", label: "Analytics" },
];

export function Shell() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__content">
          <p className="eyebrow">EchoPath / Web Console</p>
          <h1>Graph-guided playlists with a frontend that already feels real.</h1>
          <p className="hero__lede">
            This first pass is wired for the course demo: browse the track universe, choose a search
            strategy, inspect transitions, and keep the dataset handoff clean.
          </p>
        </div>
        <div className="hero__status">
          <div className="status-panel">
            <span>Dataset</span>
            <strong>{data?.dataset.track_count ?? "--"} tracks</strong>
            <small>{data?.dataset.using_sample_data ? "Sample metadata active" : "Real manifest loaded"}</small>
          </div>
          <div className="status-panel">
            <span>Backend</span>
            <strong>{data?.status ?? "starting"}</strong>
            <small>{data?.app_name ?? "Connecting to API"}</small>
          </div>
        </div>
      </header>

      <nav className="top-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `top-nav__link ${isActive ? "top-nav__link--active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="page-shell">
        <Outlet />
      </main>
    </div>
  );
}
```

./frontend/src/components/TrackCard.tsx
```tsx
import { formatDuration } from "../lib/format";
import type { TrackRecord } from "../lib/types";

interface TrackCardProps {
  track: TrackRecord;
  active: boolean;
  onSelect: (track: TrackRecord) => void;
}

export function TrackCard({ track, active, onSelect }: TrackCardProps) {
  return (
    <button
      type="button"
      className={`track-card ${active ? "track-card--active" : ""}`}
      onClick={() => onSelect(track)}
    >
      <div className="track-card__cluster">Cluster {track.cluster_id ?? "?"}</div>
      <h3>{track.title}</h3>
      <p className="track-card__artist">{track.artist}</p>
      <div className="track-card__meta">
        <span>{track.genre_label ?? "Unlabeled"}</span>
        <span>{formatDuration(track.duration_sec)}</span>
      </div>
      {track.summary ? <p className="track-card__summary">{track.summary}</p> : null}
    </button>
  );
}
```

./frontend/src/lib/api.ts
```typescript
import type {
  ClusterSummary,
  HealthResponse,
  ModelSummary,
  PlaylistRequest,
  PlaylistResult,
  SearchAlgorithmSummary,
  TrackRecord,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const EFFECTIVE_BASE_URL = API_BASE_URL || "/api";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${EFFECTIVE_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchHealth() {
  return apiRequest<HealthResponse>("/health");
}

export function fetchTracks(search?: string) {
  const query = search ? `?query=${encodeURIComponent(search)}` : "";
  return apiRequest<TrackRecord[]>(`/tracks${query}`);
}

export function fetchTrack(trackId: string) {
  return apiRequest<TrackRecord>(`/tracks/${trackId}`);
}

export function generatePlaylist(payload: PlaylistRequest) {
  return apiRequest<PlaylistResult>("/playlists/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchPlaylist(playlistId: string) {
  return apiRequest<PlaylistResult>(`/playlists/${playlistId}`);
}

export function fetchClusters() {
  return apiRequest<ClusterSummary[]>("/analytics/clusters");
}

export function fetchModels() {
  return apiRequest<ModelSummary[]>("/analytics/models");
}

export function fetchSearchAlgorithms() {
  return apiRequest<SearchAlgorithmSummary[]>("/analytics/search");
}

export function buildStreamUrl(track: TrackRecord) {
  if (!track.stream_url) {
    return null;
  }

  if (track.stream_url.startsWith("http")) {
    return track.stream_url;
  }

  return `${EFFECTIVE_BASE_URL}${track.stream_url}`;
}

export function buildApiUrl(path: string) {
  return `${EFFECTIVE_BASE_URL}${path}`;
}
```

./frontend/src/lib/format.ts
```typescript
export function formatDuration(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function titleCase(value: string) {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}
```

./frontend/src/lib/types.ts
```typescript
export type AlgorithmName = "bfs" | "dfs" | "ucs" | "ids" | "astar" | "idastar";
export type TargetType = "genre" | "cluster";
export type TempoPolicy = "any" | "steady" | "lift" | "cooldown";

export interface TrackRecord {
  track_id: string;
  title: string;
  artist: string;
  duration_sec: number;
  genre_label: string | null;
  cluster_id: number | null;
  energy: number | null;
  tempo: number | null;
  valence: number | null;
  explicit: boolean;
  audio_path: string | null;
  stream_url: string | null;
  spectrogram_url: string | null;
  summary: string | null;
}

export interface ConstraintSet {
  artist_repeat_limit: number;
  explicit_filter: boolean;
  tempo_policy: TempoPolicy;
}

export interface PlaylistRequest {
  seed_track_id: string;
  target_type: TargetType;
  target_value: string;
  algorithm: AlgorithmName;
  playlist_length: number;
  max_total_duration_sec?: number;
  constraints: ConstraintSet;
  personalization_profile?: string;
}

export interface PlaylistStep {
  order: number;
  track: TrackRecord;
  edge_cost: number;
  explanation: string;
}

export interface PlaylistResult {
  playlist_id: string;
  algorithm: AlgorithmName;
  target_type: TargetType;
  target_value: string;
  total_cost: number;
  runtime_ms: number;
  nodes_expanded: number;
  target_hit: boolean;
  constraint_summary: string;
  explanation: string;
  steps: PlaylistStep[];
}

export interface ClusterSummary {
  cluster_id: number;
  size: number;
  avg_tempo: number;
  avg_energy: number;
  avg_valence: number;
  anchor_genres: string[];
  descriptor: string;
}

export interface ModelSummary {
  model_name: string;
  family: "classical" | "cnn";
  status: "planned" | "ready" | "trained";
  notes: string;
}

export interface SearchAlgorithmSummary {
  algorithm: AlgorithmName;
  readiness: "wired" | "planned" | "benchmarked";
  notes: string;
}

export interface HealthResponse {
  status: "ok";
  app_name: string;
  dataset: {
    source: string;
    using_sample_data: boolean;
    track_count: number;
  };
}
```

./frontend/src/main.tsx
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import "./styles.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

./frontend/src/pages/AnalyticsPage.tsx
```tsx
import { useQuery } from "@tanstack/react-query";

import { SectionCard } from "../components/SectionCard";
import { fetchClusters, fetchModels, fetchSearchAlgorithms } from "../lib/api";
import { titleCase } from "../lib/format";

export function AnalyticsPage() {
  const { data: clusters = [] } = useQuery({ queryKey: ["analytics", "clusters"], queryFn: fetchClusters });
  const { data: models = [] } = useQuery({ queryKey: ["analytics", "models"], queryFn: fetchModels });
  const { data: searchAlgorithms = [] } = useQuery({
    queryKey: ["analytics", "search"],
    queryFn: fetchSearchAlgorithms,
  });

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Mood Clusters"
        title="Cluster summaries ready for the real embeddings"
        subtitle="These cards already match the outputs we’ll compute from the dataset pipeline."
      >
        <div className="analytics-grid">
          {clusters.map((cluster) => (
            <article key={cluster.cluster_id} className="analytics-card">
              <p className="eyebrow">Cluster {cluster.cluster_id}</p>
              <h3>{cluster.descriptor}</h3>
              <p>{cluster.anchor_genres.join(" / ")}</p>
              <dl className="stats-list">
                <div>
                  <dt>Tempo</dt>
                  <dd>{cluster.avg_tempo}</dd>
                </div>
                <div>
                  <dt>Energy</dt>
                  <dd>{cluster.avg_energy}</dd>
                </div>
                <div>
                  <dt>Valence</dt>
                  <dd>{cluster.avg_valence}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Search Stack"
        title="Algorithm surface already wired"
        subtitle="Benchmarks are still sample-backed, but the API and UI are ready for the real experiment outputs."
      >
        <div className="analytics-grid">
          {searchAlgorithms.map((item) => (
            <article key={item.algorithm} className="analytics-card">
              <p className="eyebrow">{titleCase(item.algorithm)}</p>
              <h3>{item.readiness}</h3>
              <p>{item.notes}</p>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Model Roadmap"
        title="Classical and CNN comparisons"
        subtitle="Once training runs exist, this page can swap from status cards to confusion matrices and benchmark charts."
      >
        <div className="analytics-grid">
          {models.map((model) => (
            <article key={model.model_name} className="analytics-card">
              <p className="eyebrow">{model.family}</p>
              <h3>{model.model_name}</h3>
              <p className={`status-badge status-badge--${model.status}`}>{model.status}</p>
              <p>{model.notes}</p>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
```

./frontend/src/pages/BuilderPage.tsx
```tsx
import { startTransition, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";
import { fetchClusters, fetchTracks, generatePlaylist } from "../lib/api";
import { titleCase } from "../lib/format";
import type { AlgorithmName, PlaylistRequest, TargetType, TempoPolicy } from "../lib/types";

const algorithms: AlgorithmName[] = ["astar", "idastar", "ucs", "bfs", "dfs", "ids"];
const tempoPolicies: TempoPolicy[] = ["any", "steady", "lift", "cooldown"];

export function BuilderPage() {
  const navigate = useNavigate();
  const { data: tracks = [] } = useQuery({ queryKey: ["builder-tracks"], queryFn: () => fetchTracks() });
  const { data: clusters = [] } = useQuery({ queryKey: ["clusters"], queryFn: fetchClusters });

  const genres = useMemo(
    () => Array.from(new Set(tracks.map((track) => track.genre_label).filter(Boolean))) as string[],
    [tracks],
  );

  const [seedTrackId, setSeedTrackId] = useState("");
  const [targetType, setTargetType] = useState<TargetType>("genre");
  const [targetValue, setTargetValue] = useState("");
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("astar");
  const [playlistLength, setPlaylistLength] = useState(5);
  const [tempoPolicy, setTempoPolicy] = useState<TempoPolicy>("lift");
  const [artistRepeatLimit, setArtistRepeatLimit] = useState(1);
  const [explicitFilter, setExplicitFilter] = useState(true);

  const mutation = useMutation({
    mutationFn: generatePlaylist,
    onSuccess: (result) => {
      startTransition(() => {
        navigate(`/results/${result.playlist_id}`);
      });
    },
  });

  const effectiveSeedTrackId = seedTrackId || tracks[0]?.track_id || "";
  const effectiveTargetValue =
    targetValue || (targetType === "genre" ? genres[0] ?? "" : clusters[0]?.cluster_id?.toString() ?? "");

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const payload: PlaylistRequest = {
      seed_track_id: effectiveSeedTrackId,
      target_type: targetType,
      target_value: effectiveTargetValue,
      algorithm,
      playlist_length: playlistLength,
      constraints: {
        artist_repeat_limit: artistRepeatLimit,
        explicit_filter: explicitFilter,
        tempo_policy: tempoPolicy,
      },
    };

    mutation.mutate(payload);
  };

  return (
    <div className="page-grid page-grid--builder">
      <SectionCard
        eyebrow="Playlist Builder"
        title="Set the graph search problem"
        subtitle="Same UI contract now, smarter heuristics later."
      >
        <form className="builder-form" onSubmit={submit}>
          <label>
            Seed track
            <select value={effectiveSeedTrackId} onChange={(event) => setSeedTrackId(event.target.value)}>
              {tracks.map((track) => (
                <option key={track.track_id} value={track.track_id}>
                  {track.title} / {track.artist}
                </option>
              ))}
            </select>
          </label>

          <label>
            Target type
            <select
              value={targetType}
              onChange={(event) => {
                const nextType = event.target.value as TargetType;
                setTargetType(nextType);
                setTargetValue("");
              }}
            >
              <option value="genre">Genre</option>
              <option value="cluster">Cluster</option>
            </select>
          </label>

          <label>
            Target value
            <select value={effectiveTargetValue} onChange={(event) => setTargetValue(event.target.value)}>
              {targetType === "genre"
                ? genres.map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))
                : clusters.map((cluster) => (
                    <option key={cluster.cluster_id} value={cluster.cluster_id}>
                      Cluster {cluster.cluster_id} / {cluster.descriptor}
                    </option>
                  ))}
            </select>
          </label>

          <label>
            Algorithm
            <select value={algorithm} onChange={(event) => setAlgorithm(event.target.value as AlgorithmName)}>
              {algorithms.map((item) => (
                <option key={item} value={item}>
                  {titleCase(item)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Playlist length
            <input
              type="range"
              min={3}
              max={10}
              value={playlistLength}
              onChange={(event) => setPlaylistLength(Number(event.target.value))}
            />
            <span>{playlistLength} tracks</span>
          </label>

          <label>
            Tempo policy
            <select value={tempoPolicy} onChange={(event) => setTempoPolicy(event.target.value as TempoPolicy)}>
              {tempoPolicies.map((policy) => (
                <option key={policy} value={policy}>
                  {titleCase(policy)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Artist repeat limit
            <input
              type="number"
              min={1}
              max={3}
              value={artistRepeatLimit}
              onChange={(event) => setArtistRepeatLimit(Number(event.target.value))}
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={explicitFilter}
              onChange={(event) => setExplicitFilter(event.target.checked)}
            />
            Filter explicit tracks
          </label>

          <button className="primary-button" type="submit" disabled={mutation.isPending || !effectiveSeedTrackId}>
            {mutation.isPending ? "Generating..." : "Generate playlist"}
          </button>

          {mutation.isError ? (
            <p className="error-text">{(mutation.error as Error).message}</p>
          ) : null}
        </form>
      </SectionCard>

      <SectionCard
        eyebrow="How To Read This"
        title="What this builder already proves"
        subtitle="Even before the real dataset lands, the UI and API contract are aligned with the final architecture."
      >
        <ul className="bullet-list">
          <li>The builder already sends a typed playlist-generation request to the backend.</li>
          <li>The backend already chooses between BFS, DFS, UCS, IDS, A*, and IDA*.</li>
          <li>Cluster and genre targets are first-class fields, not demo-only placeholders.</li>
          <li>When the dataset arrives, this form does not need redesign; it just gets better data.</li>
        </ul>
      </SectionCard>
    </div>
  );
}
```

./frontend/src/pages/LibraryPage.tsx
```tsx
import { useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AudioPreview } from "../components/AudioPreview";
import { SectionCard } from "../components/SectionCard";
import { TrackCard } from "../components/TrackCard";
import { fetchTracks } from "../lib/api";
import type { TrackRecord } from "../lib/types";

export function LibraryPage() {
  const [search, setSearch] = useState("");
  const [selectedTrack, setSelectedTrack] = useState<TrackRecord | null>(null);
  const deferredSearch = useDeferredValue(search);

  const tracksQuery = useQuery({
    queryKey: ["tracks", deferredSearch],
    queryFn: () => fetchTracks(deferredSearch),
  });

  useEffect(() => {
    if (!selectedTrack && tracksQuery.data?.length) {
      setSelectedTrack(tracksQuery.data[0]);
    }
  }, [selectedTrack, tracksQuery.data]);

  return (
    <div className="page-grid page-grid--library">
      <SectionCard
        eyebrow="Music Library"
        title="Search the working track universe"
        subtitle="This is the first surface we’ll swap from sample metadata to the real extracted library."
        actions={
          <label className="search-input">
            <span>Search</span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Try artist, title, or genre"
            />
          </label>
        }
      >
        <div className="track-grid">
          {tracksQuery.data?.map((track) => (
            <TrackCard
              key={track.track_id}
              track={track}
              active={selectedTrack?.track_id === track.track_id}
              onSelect={setSelectedTrack}
            />
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Track Inspector"
        title="Preview metadata, audio readiness, and feature cues"
        subtitle="Waveforms and spectrogram media can plug into this card later without changing the route shape."
      >
        <AudioPreview track={selectedTrack} />
      </SectionCard>
    </div>
  );
}
```

./frontend/src/pages/ResultsPage.tsx
```tsx
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";
import { buildApiUrl, fetchPlaylist } from "../lib/api";
import { formatDuration, titleCase } from "../lib/format";

export function ResultsPage() {
  const { playlistId } = useParams();
  const playlistQuery = useQuery({
    queryKey: ["playlist", playlistId],
    queryFn: () => fetchPlaylist(playlistId!),
    enabled: Boolean(playlistId),
  });

  if (!playlistId) {
    return (
      <SectionCard
        eyebrow="No Playlist Yet"
        title="Generate a path from the builder"
        subtitle="This route is ready to display the next playlist as soon as the generator returns."
      >
        <Link className="primary-button primary-button--inline" to="/builder">
          Open the builder
        </Link>
      </SectionCard>
    );
  }

  if (playlistQuery.isLoading) {
    return <SectionCard title="Loading playlist" subtitle="Pulling the generated path from the backend." />;
  }

  if (playlistQuery.isError || !playlistQuery.data) {
    return (
      <SectionCard title="Playlist unavailable" subtitle="The current playlist could not be loaded from the API." />
    );
  }

  const playlist = playlistQuery.data;

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Generated Playlist"
        title={`${titleCase(playlist.algorithm)} route to ${playlist.target_type} ${playlist.target_value}`}
        subtitle={playlist.explanation}
        actions={
          <a
            className="primary-button primary-button--inline"
            href={buildApiUrl(`/playlists/${playlist.playlist_id}/export?format=json`)}
          >
            Export JSON
          </a>
        }
      >
        <div className="metric-row">
          <div className="metric-card">
            <span>Runtime</span>
            <strong>{playlist.runtime_ms.toFixed(2)} ms</strong>
          </div>
          <div className="metric-card">
            <span>Nodes expanded</span>
            <strong>{playlist.nodes_expanded}</strong>
          </div>
          <div className="metric-card">
            <span>Total cost</span>
            <strong>{playlist.total_cost.toFixed(3)}</strong>
          </div>
          <div className="metric-card">
            <span>Target hit</span>
            <strong>{playlist.target_hit ? "Yes" : "Approximate"}</strong>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Transition Walkthrough"
        title="Why each jump was selected"
        subtitle={playlist.constraint_summary}
      >
        <div className="playlist-steps">
          {playlist.steps.map((step) => (
            <article key={step.track.track_id} className="playlist-step">
              <div className="playlist-step__order">{step.order}</div>
              <div className="playlist-step__body">
                <div className="playlist-step__head">
                  <h3>{step.track.title}</h3>
                  <span>{step.track.artist}</span>
                </div>
                <p>{step.explanation}</p>
                <div className="pill-row">
                  <span className="pill">{step.track.genre_label ?? "Unlabeled"}</span>
                  <span className="pill">Cluster {step.track.cluster_id ?? "?"}</span>
                  <span className="pill">{formatDuration(step.track.duration_sec)}</span>
                  <span className="pill">Edge {step.edge_cost.toFixed(3)}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
```

./frontend/src/styles.css
```css
@import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=Space+Grotesk:wght@400;500;700&display=swap");

:root {
  color-scheme: dark;
  font-family: "Space Grotesk", sans-serif;
  --bg: #101317;
  --bg-soft: #151c23;
  --bg-card: rgba(19, 28, 34, 0.78);
  --text: #f6efe6;
  --muted: #b7c0c8;
  --line: rgba(255, 255, 255, 0.08);
  --accent: #ffa25b;
  --accent-2: #79e1d7;
  --accent-3: #ffd77a;
  --danger: #ff7d79;
  --shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(255, 162, 91, 0.22), transparent 24%),
    radial-gradient(circle at top right, rgba(121, 225, 215, 0.2), transparent 22%),
    linear-gradient(180deg, #0f1418 0%, #161b22 52%, #101317 100%);
  background-attachment: fixed;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 100%);
  pointer-events: none;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
select {
  font: inherit;
}

#root {
  min-height: 100vh;
}

.app-shell {
  width: min(1280px, calc(100vw - 2rem));
  margin: 0 auto;
  padding: 1.25rem 0 3rem;
}

.hero {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 1rem;
  align-items: stretch;
  padding: 1.5rem 1.6rem;
  border: 1px solid var(--line);
  border-radius: 28px;
  background: linear-gradient(145deg, rgba(22, 29, 35, 0.92), rgba(16, 20, 24, 0.8));
  box-shadow: var(--shadow);
  animation: rise-in 420ms ease;
}

.hero h1,
.section-card h2,
.preview-card h2,
.analytics-card h3 {
  font-family: "Fraunces", serif;
  letter-spacing: -0.03em;
}

.hero h1 {
  margin: 0.2rem 0 0.8rem;
  font-size: clamp(2.3rem, 4vw, 4rem);
  line-height: 0.95;
}

.hero__lede,
.section-card__subtitle,
.preview-card__summary,
.analytics-card p,
.playlist-step p,
.track-card__summary {
  color: var(--muted);
}

.hero__status {
  display: grid;
  gap: 1rem;
}

.status-panel,
.metric-card,
.analytics-card,
.track-card,
.section-card,
.preview-card,
.playlist-step {
  border: 1px solid var(--line);
  background: var(--bg-card);
  backdrop-filter: blur(18px);
}

.status-panel {
  border-radius: 22px;
  padding: 1rem 1.1rem;
}

.status-panel span,
.metric-card span,
.stats-list dt {
  display: block;
  color: var(--muted);
  font-size: 0.88rem;
}

.status-panel strong,
.metric-card strong,
.preview-stats strong {
  display: block;
  margin-top: 0.2rem;
  font-size: 1.45rem;
}

.top-nav {
  display: flex;
  gap: 0.75rem;
  margin: 1.2rem 0;
  flex-wrap: wrap;
}

.top-nav__link {
  padding: 0.72rem 1rem;
  border-radius: 999px;
  border: 1px solid var(--line);
  color: var(--muted);
  background: rgba(255, 255, 255, 0.02);
  transition: transform 160ms ease, border-color 160ms ease, color 160ms ease;
}

.top-nav__link:hover,
.top-nav__link--active {
  color: var(--text);
  border-color: rgba(255, 162, 91, 0.4);
  transform: translateY(-1px);
}

.page-shell {
  display: grid;
  gap: 1rem;
}

.page-grid {
  display: grid;
  gap: 1rem;
}

.page-grid--library {
  grid-template-columns: 1.3fr 1fr;
}

.page-grid--builder {
  grid-template-columns: 1.1fr 0.9fr;
}

.section-card {
  border-radius: 28px;
  padding: 1.35rem;
  animation: rise-in 500ms ease;
}

.section-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.section-card h2 {
  margin: 0;
  font-size: clamp(1.55rem, 2vw, 2.3rem);
}

.eyebrow {
  margin: 0 0 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.72rem;
  color: var(--accent-2);
}

.search-input {
  display: grid;
  gap: 0.4rem;
  min-width: 220px;
}

.search-input input,
.builder-form input,
.builder-form select {
  width: 100%;
  padding: 0.82rem 0.95rem;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  background: rgba(8, 11, 14, 0.46);
  color: var(--text);
}

.track-grid,
.analytics-grid {
  display: grid;
  gap: 0.9rem;
}

.track-grid {
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}

.track-card {
  padding: 1rem;
  border-radius: 22px;
  text-align: left;
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}

.track-card:hover,
.track-card--active {
  transform: translateY(-2px);
  border-color: rgba(121, 225, 215, 0.4);
  background: rgba(26, 36, 44, 0.92);
}

.track-card h3 {
  margin: 0.4rem 0 0.2rem;
}

.track-card__cluster {
  color: var(--accent-3);
  font-size: 0.8rem;
}

.track-card__artist {
  margin: 0;
  color: var(--text);
}

.track-card__meta,
.pill-row,
.metric-row,
.preview-stats {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.track-card__meta {
  margin: 0.8rem 0 0.7rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.preview-card {
  display: grid;
  gap: 1rem;
  padding: 1.15rem;
  border-radius: 24px;
}

.preview-card--empty {
  min-height: 280px;
  place-items: center;
}

.preview-card__hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.preview-card__artist {
  margin: 0.2rem 0 0;
  color: var(--accent-3);
}

.preview-stats > div {
  flex: 1 1 120px;
  padding: 0.95rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line);
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 0.42rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.9rem;
}

.audio-player {
  width: 100%;
}

.preview-card__notice,
.error-text {
  padding: 0.95rem 1rem;
  border-radius: 18px;
  background: rgba(255, 125, 121, 0.08);
  border: 1px solid rgba(255, 125, 121, 0.24);
  color: #ffd1cf;
}

.builder-form {
  display: grid;
  gap: 1rem;
}

.builder-form label {
  display: grid;
  gap: 0.45rem;
}

.builder-form input[type="range"] {
  padding: 0;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.checkbox-row input {
  width: auto;
}

.primary-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.9rem 1.05rem;
  border-radius: 18px;
  border: 0;
  background: linear-gradient(135deg, var(--accent), #ffbe73);
  color: #231810;
  font-weight: 700;
  cursor: pointer;
}

.primary-button--inline {
  width: fit-content;
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.bullet-list {
  margin: 0;
  padding-left: 1.2rem;
  display: grid;
  gap: 0.7rem;
}

.metric-row {
  margin-top: 0.2rem;
}

.metric-card {
  flex: 1 1 180px;
  padding: 1rem;
  border-radius: 20px;
}

.playlist-steps {
  display: grid;
  gap: 0.9rem;
}

.playlist-step {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 1rem;
  padding: 1rem;
  border-radius: 22px;
}

.playlist-step__order {
  width: 60px;
  height: 60px;
  display: grid;
  place-items: center;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(255, 162, 91, 0.22), rgba(121, 225, 215, 0.16));
  font-size: 1.4rem;
  font-weight: 700;
}

.playlist-step__head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
}

.playlist-step__head h3 {
  margin: 0;
}

.analytics-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.analytics-card {
  padding: 1rem;
  border-radius: 22px;
}

.analytics-card h3 {
  margin: 0.1rem 0 0.6rem;
}

.stats-list {
  margin: 0.9rem 0 0;
  display: grid;
  gap: 0.5rem;
}

.stats-list div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.status-badge {
  display: inline-flex;
  width: fit-content;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
}

.status-badge--planned {
  background: rgba(255, 215, 122, 0.12);
  color: var(--accent-3);
}

.status-badge--ready {
  background: rgba(121, 225, 215, 0.12);
  color: var(--accent-2);
}

.status-badge--trained {
  background: rgba(255, 162, 91, 0.12);
  color: var(--accent);
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 960px) {
  .hero,
  .page-grid--library,
  .page-grid--builder {
    grid-template-columns: 1fr;
  }

  .preview-card__hero,
  .section-card__header {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .app-shell {
    width: min(100vw - 1rem, 100%);
    padding-top: 0.6rem;
  }

  .hero,
  .section-card {
    border-radius: 22px;
  }

  .playlist-step {
    grid-template-columns: 1fr;
  }
}
```

./frontend/src/vite-env.d.ts
```typescript
/// <reference types="vite/client" />
```

./frontend/tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

./frontend/tsconfig.node.json
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

./frontend/vite.config.d.ts
```typescript
declare const _default: import("vite").UserConfig;
export default _default;
```

./frontend/vite.config.js
```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ""); },
            },
        },
    },
});
```

./frontend/vite.config.ts
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

./main.py
````python
#!/usr/bin/env python3

from pathlib import Path
import argparse

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "env",
    ".env",
    "coverage",
}

DEFAULT_IGNORE_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
}

DEFAULT_SOURCE_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".sql",
    ".md",
    ".txt",
    ".dockerfile",
}

LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".ps1": "powershell",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".sql": "sql",
    ".md": "markdown",
    ".txt": "",
}


def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        return b"\0" in chunk
    except OSError:
        return True


def should_ignore(path: Path, root: Path, ignore_dirs: set[str], ignore_files: set[str]) -> bool:
    rel_parts = path.relative_to(root).parts

    if any(part in ignore_dirs for part in rel_parts):
        return True

    if path.name in ignore_files:
        return True

    return False


def collect_files(root: Path, source_exts: set[str], ignore_dirs: set[str], ignore_files: set[str]) -> list[Path]:
    files = []

    for path in root.rglob("*"):
        if should_ignore(path, root, ignore_dirs, ignore_files):
            continue

        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        # Special case for Dockerfile
        if path.name == "Dockerfile":
            files.append(path)
            continue

        if suffix not in source_exts:
            continue

        if is_probably_binary(path):
            continue

        files.append(path)

    return sorted(files, key=lambda p: str(p.relative_to(root)).lower())


def build_tree(root: Path, files: list[Path]) -> str:
    tree = {}

    for file in files:
        current = tree
        for part in file.relative_to(root).parts:
            current = current.setdefault(part, {})

    lines = [root.name + "/"]

    def walk(node: dict, prefix: str = ""):
        items = sorted(node.items(), key=lambda item: (
            bool(item[1]), item[0].lower()))

        for index, (name, children) in enumerate(items):
            is_last = index == len(items) - 1
            branch = "└── " if is_last else "├── "
            lines.append(prefix + branch + name)

            if children:
                extension = "    " if is_last else "│   "
                walk(children, prefix + extension)

    walk(tree)
    return "\n".join(lines)


def fence_content(content: str) -> tuple[str, str]:
    """
    Use a longer fence if the file content already contains triple backticks.
    """
    fence = "```"
    while fence in content:
        fence += "`"
    return fence, content


def read_text_file(path: Path) -> str:
    encodings = ["utf-8", "utf-8-sig", "latin-1"]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("unknown", b"", 0, 1, "Could not decode file")


def write_markdown(root: Path, files: list[Path], output: Path) -> None:
    with output.open("w", encoding="utf-8", newline="\n") as out:
        out.write("# Project Source Dump\n\n")

        out.write("## File Tree\n\n")
        out.write("```text\n")
        out.write(build_tree(root, files))
        out.write("\n```\n\n")

        out.write("## Files\n\n")

        for file in files:
            rel_path = "./" + file.relative_to(root).as_posix()

            try:
                content = read_text_file(file)
            except Exception as exc:
                content = f"[Could not read file: {exc}]"

            lang = LANG_BY_EXT.get(file.suffix.lower(), "")
            if file.name == "Dockerfile":
                lang = "dockerfile"

            fence, content = fence_content(content)

            out.write(f"{rel_path}\n")
            out.write(f"{fence}{lang}\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write(f"{fence}\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively dump project source files into a Markdown file."
    )

    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory to scan. Defaults to current directory.",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="project_source_dump.md",
        help="Output Markdown file. Defaults to project_source_dump.md.",
    )

    parser.add_argument(
        "--include-ext",
        action="append",
        default=[],
        help="Extra extension to include, for example: --include-ext .env",
    )

    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Extra directory name to ignore, for example: --ignore-dir logs",
    )

    parser.add_argument(
        "--ignore-file",
        action="append",
        default=[],
        help="Extra file name to ignore, for example: --ignore-file secrets.txt",
    )

    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    output = Path(args.output).resolve()

    if not root.exists() or not root.is_dir():
        raise SystemExit(
            f"Project directory does not exist or is not a directory: {root}")

    source_exts = DEFAULT_SOURCE_EXTS | {ext if ext.startswith(
        ".") else "." + ext for ext in args.include_ext}
    ignore_dirs = DEFAULT_IGNORE_DIRS | set(args.ignore_dir)
    ignore_files = DEFAULT_IGNORE_FILES | set(args.ignore_file)

    files = collect_files(root, source_exts, ignore_dirs, ignore_files)

    # Avoid including the generated output file if it is inside the project.
    files = [file for file in files if file.resolve() != output]

    write_markdown(root, files, output)

    print(f"Wrote {len(files)} files to {output}")


if __name__ == "__main__":
    main()
````

./README.md
````markdown
# EchoPath

EchoPath is an AI/ML playlist generator for the JIIT course project, built as a web-first experience.
This repository now contains:

- a FastAPI backend for tracks, playlist generation, analytics, and future dataset-backed streaming
- a React frontend for browsing the library, generating playlists, and reviewing model/search outputs
- a training scaffold for ingestion, classical ML, CNNs, and search benchmarking

`/home/life2harsh/rustplayer` stays separate. We are not coupling it here; the future handoff will be playlist exports and shared API contracts.

## Current Status

This first implementation is dataset-ready but does not require the real music files yet.
Until a manifest is provided, the backend serves a curated sample library from `artifacts/sample-data/demo_library.json`.

## Structure

```text
backend/   FastAPI app and API tests
frontend/  React + TypeScript + Vite web client
training/  Ingest and training entrypoints for the ML pipeline
artifacts/ Sample metadata and future experiment outputs
data/      Future dataset manifests and derived assets
```

## Quick Start

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` requests to `http://127.0.0.1:8000`.

## Dataset Hand-Off

When the real dataset is ready, point the backend to a manifest file:

```bash
export ECHOPATH_LIBRARY_PATH=/absolute/path/to/tracks.json
```

The manifest should follow the same schema used in `artifacts/sample-data/demo_library.json`.

## Training Scaffold

The training package is intentionally lightweight for now, but the command surface is ready:

```bash
cd training
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .
echopath ingest --dataset-root /path/to/fma
echopath train-classical
echopath train-cnn --hf-repo your-org/echopath-models
echopath benchmark-search
```

## Next Steps

1. Plug in the real dataset manifest and local audio files.
2. Replace sample analytics with feature-extracted outputs.
3. Expand the training commands into full data pipelines and model jobs.
````

./test_audio.py
```python
import librosa

path = "C:\\Dataset\\fma_small\\000\\000002.mp3"

y, sr = librosa.load(path, duration=10)
print("Loaded successfully", len(y))
```

./training/echopath/__init__.py
```python
"""Training and ingestion helpers for EchoPath."""
```

./training/echopath/__main__.py
```python
from .cli import main


if __name__ == "__main__":
    main()
```

./training/echopath/cli.py
```python
from __future__ import annotations

import argparse

from .commands.benchmark_search import run_benchmark_search
from .commands.ingest import run_ingest
from .commands.train_classical import run_train_classical
from .commands.train_cnn import run_train_cnn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echopath", description="EchoPath training command surface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Prepare the dataset manifest and extracted features.")
    ingest.add_argument("--dataset-root", dest="dataset_root", default=None)
    ingest.add_argument("--output-manifest", dest="output_manifest", default=None)

    train_classical = subparsers.add_parser("train-classical", help="Train the classical ML baselines.")
    train_classical.add_argument("--features", default=None)
    train_classical.add_argument("--label-column", default="preference_proxy")

    train_cnn = subparsers.add_parser("train-cnn", help="Train spectrogram CNNs on GPU or Hugging Face runners.")
    train_cnn.add_argument("--dataset-root", dest="dataset_root", default=None)
    train_cnn.add_argument("--hf-repo", dest="hf_repo", default=None)
    train_cnn.add_argument("--epochs", type=int, default=20)
    train_cnn.add_argument("--mixed-precision", action="store_true")

    benchmark = subparsers.add_parser("benchmark-search", help="Benchmark graph search algorithms on a fixed request set.")
    benchmark.add_argument("--manifest", default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args)
        return
    if args.command == "train-classical":
        run_train_classical(args)
        return
    if args.command == "train-cnn":
        run_train_cnn(args)
        return
    if args.command == "benchmark-search":
        run_benchmark_search(args)
        return

    parser.error("Unknown command")
```

./training/echopath/commands/__init__.py
```python
"""Training commands for EchoPath."""
```

./training/echopath/commands/benchmark_search.py
```python
from __future__ import annotations


def run_benchmark_search(args) -> None:
    print("EchoPath search benchmark scaffold")
    print(f"Manifest: {args.manifest or 'data/library/tracks.json'}")
    print("")
    print("Planned output metrics:")
    print("- runtime")
    print("- nodes expanded")
    print("- total path smoothness cost")
    print("- target hit rate")
    print("- artist and genre diversity")
```

./training/echopath/commands/ingest.py
```python
from __future__ import annotations

from pathlib import Path

from ..config import load_config


def run_ingest(args) -> None:
    config = load_config(args.dataset_root)
    manifest_path = Path(args.output_manifest).expanduser() if args.output_manifest else config.manifest_path

    print("EchoPath ingest scaffold")
    print(f"Dataset root: {config.dataset_root}")
    print(f"Output manifest: {manifest_path}")
    print("")
    print("Next implementation step:")
    print("- scan the dataset root for audio files and metadata")
    print("- extract classical features and mel-spectrogram tensors")
    print("- write a backend-compatible track manifest to the output path")
```

./training/echopath/commands/train_classical.py
```python
from __future__ import annotations


def run_train_classical(args) -> None:
    print("EchoPath classical training scaffold")
    print(f"Feature table: {args.features or 'data/features.parquet'}")
    print(f"Label column: {args.label_column}")
    print("")
    print("Planned models: Logistic Regression, SVM, Random Forest, MLPClassifier")
    print("This command will own split creation, metrics, artifact saving, and report tables.")
```

./training/echopath/commands/train_cnn.py
```python
from __future__ import annotations

from ..config import load_config


def run_train_cnn(args) -> None:
    config = load_config(args.dataset_root)
    print("EchoPath CNN training scaffold")
    print(f"Dataset root: {config.dataset_root}")
    print(f"Epochs: {args.epochs}")
    print(f"Mixed precision: {'enabled' if args.mixed_precision else 'disabled'}")
    print(f"Hugging Face repo: {args.hf_repo or 'not set'}")
    print("")
    print("Planned models: LeNet-style, VGG-style, ResNet-style")
    print("This command will manage Accelerate launch configs, checkpoint saving, and HF uploads.")
```

./training/echopath/config.py
```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class TrainingConfig:
    repo_root: Path
    dataset_root: Path
    manifest_path: Path
    artifacts_dir: Path


def load_config(dataset_root: str | None = None) -> TrainingConfig:
    repo_root = Path(__file__).resolve().parents[2]
    resolved_dataset_root = Path(dataset_root or os.getenv("ECHOPATH_DATASET_ROOT", repo_root / "data")).expanduser()
    return TrainingConfig(
        repo_root=repo_root,
        dataset_root=resolved_dataset_root,
        manifest_path=repo_root / "data" / "library" / "tracks.json",
        artifacts_dir=repo_root / "artifacts",
    )
```

./training/echopath_training.egg-info/dependency_links.txt
```

```

./training/echopath_training.egg-info/entry_points.txt
```
[console_scripts]
echopath = echopath.cli:main
```

./training/echopath_training.egg-info/requires.txt
```
numpy<3.0,>=2.0
pandas<3.0,>=2.2
scikit-learn<2.0,>=1.5
librosa<1.0,>=0.11
matplotlib<4.0,>=3.9
torch<3.0,>=2.5
torchaudio<3.0,>=2.5
accelerate<2.0,>=1.1
huggingface-hub<1.0,>=0.26
```

./training/echopath_training.egg-info/SOURCES.txt
```
pyproject.toml
echopath/__init__.py
echopath/__main__.py
echopath/cli.py
echopath/config.py
echopath/commands/__init__.py
echopath/commands/benchmark_search.py
echopath/commands/ingest.py
echopath/commands/train_classical.py
echopath/commands/train_cnn.py
echopath_training.egg-info/PKG-INFO
echopath_training.egg-info/SOURCES.txt
echopath_training.egg-info/dependency_links.txt
echopath_training.egg-info/entry_points.txt
echopath_training.egg-info/requires.txt
echopath_training.egg-info/top_level.txt
```

./training/echopath_training.egg-info/top_level.txt
```
echopath
```

./training/pyproject.toml
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "echopath-training"
version = "0.1.0"
description = "Training and ingestion entrypoints for the EchoPath project."
requires-python = ">=3.11"
dependencies = [
  "numpy>=2.0,<3.0",
  "pandas>=2.2,<3.0",
  "scikit-learn>=1.5,<2.0",
  "librosa>=0.11,<1.0",
  "matplotlib>=3.9,<4.0",
  "torch>=2.5,<3.0",
  "torchaudio>=2.5,<3.0",
  "accelerate>=1.1,<2.0",
  "huggingface-hub>=0.26,<1.0",
]

[project.scripts]
echopath = "echopath.cli:main"

[tool.setuptools]
packages = ["echopath", "echopath.commands"]
```

