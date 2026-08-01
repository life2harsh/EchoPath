export type AlgorithmName = "bfs" | "dfs" | "ucs" | "ids" | "idastar" | "astar";
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

  preference_score: number | null;
  mood_fit_score: number | null;
  cnn_genre_prediction: string | null;
  cnn_genre_confidence: number | null;
  signal_source: string | null;
  evaluation_split: "train" | "validation" | "test" | null;
}

export interface TrackAnalysisResponse {
  track: TrackRecord;
  detected_features: Record<string, number>;
  assigned_cluster_id: number | null;
  predicted_genre: string | null;
  predicted_genre_confidence: number;
  nearest_neighbors: Array<{
    track_id: string;
    title: string;
    artist: string;
    genre_label: string | null;
    cluster_id: number | null;
    distance: number;
  }>;
  explanation: string;
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

export interface PlaylistQualityMetrics {
  average_transition_cost: number;
  tempo_variance: number;
  energy_variance: number;
  genre_diversity: number;
  artist_diversity: number;
  preference_mean: number;
  cnn_target_alignment: number;
  constraint_satisfaction_rate: number;
  hill_climbing_improvement: number;
  refinement_applied: boolean;
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
  quality_metrics: PlaylistQualityMetrics;
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
