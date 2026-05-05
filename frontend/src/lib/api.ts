import type {
  ClusterSummary,
  HealthResponse,
  ModelSummary,
  PlaylistRequest,
  PlaylistResult,
  SearchAlgorithmSummary,
  TrackAnalysisResponse,
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

export async function analyzeTrackUpload(file: File, title?: string, artist?: string) {
  const body = new FormData();
  body.append("file", file);
  if (title) {
    body.append("title", title);
  }
  if (artist) {
    body.append("artist", artist);
  }

  const response = await fetch(`${EFFECTIVE_BASE_URL}/tracks/analyze`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Upload analysis failed with status ${response.status}`);
  }

  return response.json() as Promise<TrackAnalysisResponse>;
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
