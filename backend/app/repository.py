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
