from __future__ import annotations

from typing import Any, Literal
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
    energy: float | None = Field(default=None, ge=0.0)
    tempo: float | None = Field(default=None, ge=0.0)
    valence: float | None = Field(default=None, ge=0.0)
    explicit: bool = False
    audio_path: str | None = None
    stream_url: str | None = None
    spectrogram_url: str | None = None
    summary: str | None = None

    preference_score: float | None = Field(default=None, ge=0.0, le=1.0)
    mood_fit_score: float | None = Field(default=None, ge=0.0, le=1.0)
    cnn_genre_prediction: str | None = None
    cnn_genre_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    signal_source: str | None = None


class TrackAnalysisResponse(BaseModel):
    track: TrackRecord
    detected_features: dict[str, float | int]
    assigned_cluster_id: int | None = None
    predicted_genre: str | None = None
    predicted_genre_confidence: float = Field(ge=0.0, le=1.0)
    nearest_neighbors: list[dict[str, Any]]
    explanation: str


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


class PlaylistQualityMetrics(BaseModel):
    average_transition_cost: float = Field(ge=0.0)
    tempo_variance: float = Field(ge=0.0)
    energy_variance: float = Field(ge=0.0)
    genre_diversity: float = Field(ge=0.0, le=1.0)
    artist_diversity: float = Field(ge=0.0, le=1.0)
    preference_mean: float = Field(ge=0.0, le=1.0)
    cnn_target_alignment: float = Field(ge=0.0, le=1.0)
    constraint_satisfaction_rate: float = Field(ge=0.0, le=1.0)
    hill_climbing_improvement: float = Field(ge=0.0)
    refinement_applied: bool


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
    quality_metrics: PlaylistQualityMetrics
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
