from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import heapq
import json
import math
import mimetypes
from pathlib import Path
from statistics import pvariance
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException

from .config import Settings
from .models import (
    ClusterSummary,
    DatasetStatus,
    ModelSummary,
    PlaylistQualityMetrics,
    PlaylistRequest,
    PlaylistResult,
    PlaylistStep,
    SearchAlgorithmSummary,
    TrackRecord,
)


MAX_EXPANSIONS = 3_000
NEIGHBOR_LIMIT = 8
HILL_CLIMB_CANDIDATES = 10
HILL_CLIMB_PASSES = 2


@dataclass
class SearchOutcome:
    path: list[str]
    cost: float
    nodes_expanded: int
    target_hit: bool
    pre_refinement_cost: float | None = None
    refinement_applied: bool = False


class Repository:
    """Repository and playlist-search engine.

    The backend consumes the enriched manifest produced by the training
    pipeline. Each track can include classical/CNN-derived signals such as
    preference_score, mood_fit_score, and cnn_genre_prediction. These fields are
    optional so the app still runs on sample data, but when present they influence
    search cost and A* heuristics.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tracks: list[TrackRecord] = []
        self._track_index: dict[str, TrackRecord] = {}
        self._playlists: dict[str, PlaylistResult] = {}
        self._neighbor_cache: dict[tuple[str, str, str, str], list[str]] = {}
        self._cluster_centroids: dict[int, tuple[float, float, float]] = {}
        self.reload()

    def reload(self) -> None:
        data_path, using_sample = self._resolve_library_path()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        raw_tracks = [TrackRecord.model_validate(item) for item in payload]

        self._tracks = [self._attach_urls(track) for track in raw_tracks]
        self._track_index = {track.track_id: track for track in self._tracks}
        cluster_points: dict[int, list[tuple[float, float, float]]] = {}
        for track in self._tracks:
            if track.cluster_id is not None:
                cluster_points.setdefault(track.cluster_id, []).append(self._feature_point(track))
        self._cluster_centroids = {
            cluster_id: tuple(sum(point[index] for point in points) / len(points) for index in range(3))
            for cluster_id, points in cluster_points.items()
        }
        self._neighbor_cache.clear()
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
                or (track.cnn_genre_prediction and needle in track.cnn_genre_prediction.lower())
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

        refined = self._hill_climb_refine(outcome, request)

        runtime_ms = round((perf_counter() - start) * 1000, 2)
        playlist_id = uuid4().hex[:10]
        steps = self._build_playlist_steps(refined.path, request)
        quality_metrics = self._playlist_quality_metrics(refined, request)

        result = PlaylistResult(
            playlist_id=playlist_id,
            algorithm=request.algorithm,
            target_type=request.target_type,
            target_value=request.target_value,
            total_cost=round(refined.cost, 4),
            runtime_ms=runtime_ms,
            nodes_expanded=refined.nodes_expanded,
            target_hit=refined.target_hit,
            constraint_summary=self._summarize_constraints(request),
            explanation=self._playlist_explanation(request, refined.target_hit, refined.refinement_applied),
            quality_metrics=quality_metrics,
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
                model_name="Logistic Regression Mood-Cluster Classifier",
                family="classical",
                status="trained",
                notes="Strong classical mood-fit experiment reflected through enriched manifest signals.",
            ),
            ModelSummary(
                model_name="Extra Trees Top-5 Genre Classifier",
                family="classical",
                status="trained",
                notes="Best balanced top-5 handcrafted-feature genre baseline.",
            ),
            ModelSummary(
                model_name="LeNet Spectrogram CNN",
                family="cnn",
                status="trained",
                notes="Working mel-spectrogram baseline for genre classification.",
            ),
            ModelSummary(
                model_name="VGG-style Spectrogram CNN",
                family="cnn",
                status="planned",
                notes="Deeper architecture reserved for larger GPU experiments.",
            ),
            ModelSummary(
                model_name="ResNet-style Spectrogram CNN",
                family="cnn",
                status="planned",
                notes="Residual architecture reserved for final deep-learning comparison.",
            ),
        ]

    def search_summaries(self) -> list[SearchAlgorithmSummary]:
        return [
            SearchAlgorithmSummary(
                algorithm=algorithm,
                readiness="wired",
                notes="Runs on feature-similarity graph with target, preference, CNN/proxy, and constraint-aware scoring.",
            )
            for algorithm in ("bfs", "dfs", "ucs", "ids", "astar", "idastar")
        ]

    def _build_playlist_steps(self, path: list[str], request: PlaylistRequest) -> list[PlaylistStep]:
        steps: list[PlaylistStep] = []
        previous: TrackRecord | None = None
        for index, track_id in enumerate(path, start=1):
            track = self.get_track(track_id)
            edge_cost = 0.0 if previous is None else round(self._composite_edge_cost(previous, track, request), 4)
            explanation = (
                "Seed track anchors the path."
                if previous is None
                else self._transition_explanation(previous, track, request)
            )
            steps.append(PlaylistStep(order=index, track=track, edge_cost=edge_cost, explanation=explanation))
            previous = track
        return steps

    def _transition_explanation(self, previous: TrackRecord, current: TrackRecord, request: PlaylistRequest) -> str:
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

        signal_parts: list[str] = []
        if current.preference_score is not None:
            signal_parts.append(f"preference score {current.preference_score:.2f}")
        if current.cnn_genre_prediction:
            confidence = f" ({current.cnn_genre_confidence:.2f})" if current.cnn_genre_confidence is not None else ""
            signal_parts.append(f"CNN/proxy genre signal {current.cnn_genre_prediction}{confidence}")

        signal_text = f" Model signals: {', '.join(signal_parts)}." if signal_parts else ""
        target_text = " Target aligned." if self._matches_target(current, request) else ""

        return (
            f"{cluster_phrase}, {genre_phrase}, tempo shift {tempo_delta:.1f} BPM, "
            f"energy delta {energy_delta:.2f}.{target_text}{signal_text}"
        )

    def _playlist_explanation(self, request: PlaylistRequest, target_hit: bool, refined: bool) -> str:
        target_text = f"{request.target_type} '{request.target_value}'"
        refinement_text = " A hill-climbing refinement pass improved the local path cost." if refined else ""
        if target_hit:
            return (
                f"The path reaches the requested {target_text} while preserving "
                f"{request.constraints.tempo_policy} tempo movement, artist repetition limits, "
                f"and ML/CNN-derived preference signals.{refinement_text}"
            )
        return (
            f"The current library could not fully hit {target_text}, so the generator returned "
            f"the smoothest feasible approximation under the active constraints.{refinement_text}"
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
            if len(path) >= request.playlist_length:
                continue

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                queue.append((neighbor.track_id, path + [neighbor.track_id], cost + self._composite_edge_cost(last, neighbor, request)))
        return None

    def _search_dfs(self, seed_track_id: str, request: PlaylistRequest) -> SearchOutcome | None:
        stack = [(seed_track_id, [seed_track_id], 0.0)]
        expansions = 0
        while stack and expansions < MAX_EXPANSIONS:
            _, path, cost = stack.pop()
            if self._is_goal(path, request):
                return SearchOutcome(path=path, cost=cost, nodes_expanded=expansions, target_hit=True)
            if len(path) >= request.playlist_length:
                continue

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in reversed(self._neighbors(last, path, request)):
                next_cost = cost + self._composite_edge_cost(last, neighbor, request)
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
            if len(path) >= request.playlist_length:
                continue

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                sequence += 1
                next_cost = cost + self._composite_edge_cost(last, neighbor, request)
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
            if len(path) >= request.playlist_length:
                continue

            last = self.get_track(path[-1])
            expansions += 1
            for neighbor in self._neighbors(last, path, request):
                sequence += 1
                edge = self._composite_edge_cost(last, neighbor, request)
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
                next_cost = cost + self._composite_edge_cost(last, neighbor, request)
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
            if len(path) >= request.playlist_length:
                return None, float("inf")

            minimum = float("inf")
            expansions += 1
            if expansions >= MAX_EXPANSIONS:
                return None, minimum

            for neighbor in self._neighbors(last, path, request):
                edge = self._composite_edge_cost(last, neighbor, request)
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
            total_cost += self._composite_edge_cost(last, best, request)
            path.append(best.track_id)
            expansions += 1

        target_hit = self._matches_target(self.get_track(path[-1]), request)
        return SearchOutcome(path=path, cost=total_cost, nodes_expanded=expansions, target_hit=target_hit)

    def _hill_climb_refine(self, outcome: SearchOutcome, request: PlaylistRequest) -> SearchOutcome:
        if len(outcome.path) < 3:
            return SearchOutcome(
                path=outcome.path,
                cost=round(self._path_cost(outcome.path, request), 4),
                nodes_expanded=outcome.nodes_expanded,
                target_hit=outcome.target_hit,
                pre_refinement_cost=outcome.cost,
                refinement_applied=False,
            )

        best_path = outcome.path[:]
        best_cost = self._path_cost(best_path, request)
        original_cost = best_cost
        improved = False

        for _ in range(HILL_CLIMB_PASSES):
            pass_improved = False
            for position in range(1, len(best_path)):
                previous = self.get_track(best_path[position - 1])
                current_id = best_path[position]
                candidate_path_base = best_path[:position] + best_path[position + 1 :]

                candidates = [
                    track
                    for track in self._neighbors(previous, candidate_path_base, request, limit=HILL_CLIMB_CANDIDATES)
                    if track.track_id != current_id and track.track_id not in candidate_path_base
                ]

                for candidate in candidates:
                    candidate_path = best_path[:]
                    candidate_path[position] = candidate.track_id

                    if not self._path_respects_constraints(candidate_path, request):
                        continue
                    if not self._matches_target(self.get_track(candidate_path[-1]), request):
                        continue

                    candidate_cost = self._path_cost(candidate_path, request)
                    if candidate_cost + 1e-9 < best_cost:
                        best_path = candidate_path
                        best_cost = candidate_cost
                        improved = True
                        pass_improved = True
                        break

                if pass_improved:
                    break

            if not pass_improved:
                break

        return SearchOutcome(
            path=best_path,
            cost=round(best_cost, 4),
            nodes_expanded=outcome.nodes_expanded,
            target_hit=self._matches_target(self.get_track(best_path[-1]), request),
            pre_refinement_cost=round(original_cost, 4),
            refinement_applied=improved,
        )

    def _is_goal(self, path: list[str], request: PlaylistRequest) -> bool:
        if len(path) != request.playlist_length:
            return False
        final_track = self.get_track(path[-1])
        return self._matches_target(final_track, request)

    def _matches_target(self, track: TrackRecord, request: PlaylistRequest) -> bool:
        if request.target_type == "genre":
            return track.genre_label == request.target_value or track.cnn_genre_prediction == request.target_value
        try:
            return track.cluster_id == int(request.target_value)
        except ValueError:
            return False

    def _neighbors(self, current: TrackRecord, path: list[str], request: PlaylistRequest, limit: int = NEIGHBOR_LIMIT) -> list[TrackRecord]:
        cache_key = (
            current.track_id,
            request.constraints.tempo_policy,
            request.target_type,
            request.target_value,
        )

        ranked_ids = self._neighbor_cache.get(cache_key)
        if ranked_ids is None:
            ranked = sorted(
                (track for track in self._tracks if track.track_id != current.track_id),
                key=lambda track: (
                    self._composite_edge_cost(current, track, request)
                    + self._target_penalty(track, request) * 0.35
                ),
            )
            ranked_ids = [track.track_id for track in ranked[: max(64, limit * 8)]]
            self._neighbor_cache[cache_key] = ranked_ids

        candidates: list[TrackRecord] = []
        for track_id in ranked_ids:
            track = self.get_track(track_id)
            if self._can_add_to_path(track, path, request):
                candidates.append(track)
            if len(candidates) >= limit:
                break

        return candidates

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

    def _path_respects_constraints(self, path: list[str], request: PlaylistRequest) -> bool:
        tracks = [self.get_track(track_id) for track_id in path]

        if request.constraints.explicit_filter and any(track.explicit for track in tracks):
            return False

        artist_counts = Counter(track.artist for track in tracks)
        if any(count > request.constraints.artist_repeat_limit for count in artist_counts.values()):
            return False

        if request.max_total_duration_sec and sum(track.duration_sec for track in tracks) > request.max_total_duration_sec:
            return False

        return True

    def _heuristic(self, track: TrackRecord, path: list[str], request: PlaylistRequest) -> float:
        remaining = max(request.playlist_length - len(path), 0)
        return (
            self._target_penalty(track, request)
            + self._signal_penalty(track, request) * 0.5
            + remaining * 0.08
        )

    def _target_penalty(self, track: TrackRecord, request: PlaylistRequest) -> float:
        if request.target_type == "genre":
            if track.genre_label == request.target_value:
                return 0.0
            if track.cnn_genre_prediction == request.target_value:
                confidence = track.cnn_genre_confidence if track.cnn_genre_confidence is not None else 0.5
                return max(0.05, 0.35 * (1.0 - confidence))
            return 0.75

        try:
            target_cluster = int(request.target_value)
        except ValueError:
            return 1.0
        if track.cluster_id is None:
            return 1.0
        if track.cluster_id == target_cluster:
            return 0.0
        target_centroid = self._cluster_centroids.get(target_cluster)
        if target_centroid is None:
            return 1.0
        point = self._feature_point(track)
        return math.sqrt(sum((point[index] - target_centroid[index]) ** 2 for index in range(3)))

    def _feature_point(self, track: TrackRecord) -> tuple[float, float, float]:
        return ((track.tempo or 0.0) / 120.0, track.energy or 0.0, track.valence or 0.0)

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

    def _signal_penalty(self, track: TrackRecord, request: PlaylistRequest) -> float:
        penalty = 0.0

        if track.preference_score is not None:
            penalty += (1.0 - track.preference_score) * 0.12

        if track.mood_fit_score is not None:
            penalty += (1.0 - track.mood_fit_score) * 0.06

        if request.target_type == "genre" and track.cnn_genre_prediction:
            confidence = track.cnn_genre_confidence if track.cnn_genre_confidence is not None else 0.5
            if track.cnn_genre_prediction == request.target_value:
                penalty -= confidence * 0.04
            else:
                penalty += confidence * 0.08

        return max(0.0, penalty)

    def _composite_edge_cost(self, source: TrackRecord, target: TrackRecord, request: PlaylistRequest) -> float:
        base = self._edge_cost(source, target, request.constraints.tempo_policy)
        return max(0.0, base + self._signal_penalty(target, request))

    def _path_cost(self, path: list[str], request: PlaylistRequest) -> float:
        if len(path) < 2:
            return 0.0
        total = 0.0
        for source_id, target_id in zip(path, path[1:]):
            total += self._composite_edge_cost(self.get_track(source_id), self.get_track(target_id), request)
        return total

    def _playlist_quality_metrics(self, outcome: SearchOutcome, request: PlaylistRequest) -> PlaylistQualityMetrics:
        tracks = [self.get_track(track_id) for track_id in outcome.path]
        transition_costs = [
            self._composite_edge_cost(source, target, request)
            for source, target in zip(tracks, tracks[1:])
        ]

        tempos = [track.tempo or 0.0 for track in tracks]
        energies = [track.energy or 0.0 for track in tracks]
        genres = [track.genre_label or "unknown" for track in tracks]
        artists = [track.artist for track in tracks]
        preferences = [track.preference_score for track in tracks if track.preference_score is not None]

        if request.target_type == "genre":
            aligned_count = sum(
                1
                for track in tracks
                if track.cnn_genre_prediction == request.target_value
                or track.genre_label == request.target_value
            )
            cnn_alignment = aligned_count / len(tracks) if tracks else 0.0
        else:
            cnn_alignment = 0.0

        satisfied = 0
        checks = 4

        if not (request.constraints.explicit_filter and any(track.explicit for track in tracks)):
            satisfied += 1
        if all(count <= request.constraints.artist_repeat_limit for count in Counter(artists).values()):
            satisfied += 1
        if request.max_total_duration_sec is None or sum(track.duration_sec for track in tracks) <= request.max_total_duration_sec:
            satisfied += 1
        if outcome.target_hit:
            satisfied += 1

        pre = outcome.pre_refinement_cost if outcome.pre_refinement_cost is not None else outcome.cost
        improvement = max(0.0, pre - outcome.cost)

        return PlaylistQualityMetrics(
            average_transition_cost=round(sum(transition_costs) / len(transition_costs), 4) if transition_costs else 0.0,
            tempo_variance=round(pvariance(tempos), 4) if len(tempos) > 1 else 0.0,
            energy_variance=round(pvariance(energies), 4) if len(energies) > 1 else 0.0,
            genre_diversity=round(len(set(genres)) / len(genres), 4) if genres else 0.0,
            artist_diversity=round(len(set(artists)) / len(artists), 4) if artists else 0.0,
            preference_mean=round(sum(preferences) / len(preferences), 4) if preferences else 0.0,
            cnn_target_alignment=round(cnn_alignment, 4),
            constraint_satisfaction_rate=round(satisfied / checks, 4),
            hill_climbing_improvement=round(improvement, 4),
            refinement_applied=outcome.refinement_applied,
        )

    def _describe_cluster(self, energy: float, valence: float) -> str:
        if energy < 0.4 and valence < 0.5:
            return "reflective and low-lit"
        if energy < 0.5:
            return "steady and spacious"
        if valence > 0.6:
            return "bright and forward-moving"
        return "driving with a little tension"
