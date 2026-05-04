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
