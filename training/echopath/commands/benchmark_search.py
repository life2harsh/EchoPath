from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import traceback
from pathlib import Path
from statistics import stdev
from time import perf_counter
from typing import Any, Iterator

import pandas as pd

from ..config import load_config

SEARCH_ALGORITHMS = ["bfs", "dfs", "ucs", "ids", "astar", "idastar"]
BASELINES = ["random-valid", "greedy", "nearest-neighbor"]
ALGORITHMS = SEARCH_ALGORITHMS + BASELINES
ABLATIONS = [
    "no-ml-signals",
    "no-target-ranking",
    "no-hill-climbing",
    "no-heuristic-target",
    "no-heuristic-signals",
    "no-heuristic-depth",
]
QUALITY_METRICS = [
    "average_transition_cost",
    "tempo_variance",
    "energy_variance",
    "genre_diversity",
    "artist_diversity",
    "preference_mean",
    "cnn_target_alignment",
    "constraint_satisfaction_rate",
    "hill_climbing_improvement",
    "refinement_applied",
]
SUMMARY_METRICS = [
    "runtime_ms",
    "wall_runtime_ms",
    "search_runtime_ms",
    "nodes_expanded",
    "search_nodes_expanded",
    "candidate_evaluations",
    "total_cost",
    "target_hit",
    "assisted_target_hit",
    "raw_search_success",
    "fallback_used",
    "playlist_length",
    *QUALITY_METRICS,
]


def _load_backend(repo_root: Path, manifest: Path | None):
    backend_path = repo_root / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    if manifest is not None:
        os.environ["ECHOPATH_LIBRARY_PATH"] = str(manifest.expanduser().resolve())

    from app.config import get_settings
    from app.dependencies import get_repository

    get_settings.cache_clear()
    get_repository.cache_clear()
    return get_repository()


def _stable_seed(seed: int, *parts: object) -> int:
    payload = "\x1f".join([str(seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], "big")


def _track_value(track: Any, target_type: str) -> str | None:
    value = track.genre_label if target_type == "genre" else track.cluster_id
    return None if value is None else str(value)


def _build_cases(tracks: list[Any], max_cases: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    cases: list[dict[str, str]] = []
    for target_type in ("genre", "cluster"):
        by_source: dict[str, list[Any]] = {}
        target_values: set[str] = set()
        for track in tracks:
            value = _track_value(track, target_type)
            if value is not None:
                by_source.setdefault(value, []).append(track)
                target_values.add(value)
        if not target_values:
            continue

        strata = [
            (source, target)
            for source in sorted(by_source)
            for target in sorted(target_values)
            if source != target
        ]
        if not strata:
            strata = [(source, target) for source in sorted(by_source) for target in sorted(target_values)]
        rng.shuffle(strata)
        selected = 0
        cycle = 0
        while selected < max_cases and strata:
            source, target = strata[cycle % len(strata)]
            candidates = by_source[source]
            track = candidates[rng.randrange(len(candidates))]
            cases.append(
                {
                    "case_id": f"{target_type}-{selected + 1:04d}",
                    "seed_track_id": track.track_id,
                    "seed_stratum": source,
                    "target_type": target_type,
                    "target_value": target,
                }
            )
            selected += 1
            cycle += 1
    return cases


def _variants(ablations: list[str], neighbor_limits: list[int], default_neighbor_limit: int) -> list[dict[str, Any]]:
    variants = [{"name": "full", "ablation": None, "neighbor_limit": default_neighbor_limit}]
    variants.extend(
        {"name": ablation, "ablation": ablation, "neighbor_limit": default_neighbor_limit}
        for ablation in ablations
    )
    variants.extend(
        {"name": f"neighbor-limit-{limit}", "ablation": None, "neighbor_limit": limit}
        for limit in neighbor_limits
        if limit != default_neighbor_limit
    )
    return variants


@contextmanager
def _benchmark_variant(repository: Any, variant: dict[str, Any]) -> Iterator[None]:
    names = ["_signal_penalty", "_neighbors", "_hill_climb_refine", "_heuristic", "_matches_target", "_target_penalty"]
    originals = {name: getattr(repository, name) for name in names}
    ablation = variant["ablation"]
    neighbor_limit = variant["neighbor_limit"]

    if ablation == "no-ml-signals":
        repository._signal_penalty = lambda track, request: 0.0

        def label_only_match(track, request):
            if request.target_type == "genre":
                return track.genre_label == request.target_value
            try:
                return track.cluster_id == int(request.target_value)
            except ValueError:
                return False

        def label_only_penalty(track, request):
            if request.target_type == "genre":
                return 0.0 if track.genre_label == request.target_value else 0.75
            return originals["_target_penalty"](track, request)

        repository._matches_target = label_only_match
        repository._target_penalty = label_only_penalty

    if ablation == "no-target-ranking":
        ranking_cache: dict[tuple[str, str, str, str], list[str]] = {}

        def untargeted_neighbors(current, path, request, limit=None):
            effective_limit = neighbor_limit if limit is None else limit
            key = (
                current.track_id,
                request.constraints.tempo_policy,
                request.target_type,
                request.target_value,
            )
            ranked_ids = ranking_cache.get(key)
            if ranked_ids is None:
                ranked = sorted(
                    (track for track in repository._tracks if track.track_id != current.track_id),
                    key=lambda track: repository._composite_edge_cost(current, track, request),
                )
                ranked_ids = [track.track_id for track in ranked]
                ranking_cache[key] = ranked_ids
            candidates = []
            for track_id in ranked_ids:
                track = repository.get_track(track_id)
                if repository._can_add_to_path(track, path, request):
                    candidates.append(track)
                if len(candidates) >= effective_limit:
                    break
            return candidates

        repository._neighbors = untargeted_neighbors
    elif neighbor_limit != 8:
        repository._neighbors = lambda current, path, request, limit=None: originals["_neighbors"](
            current, path, request, neighbor_limit if limit is None else limit
        )

    if ablation == "no-hill-climbing":
        repository._hill_climb_refine = lambda outcome, request: outcome

    if ablation in {"no-heuristic-target", "no-heuristic-signals", "no-heuristic-depth"}:
        def ablated_heuristic(track, path, request):
            remaining = max(request.playlist_length - len(path), 0)
            target = 0.0 if ablation == "no-heuristic-target" else repository._target_penalty(track, request)
            signals = 0.0 if ablation == "no-heuristic-signals" else repository._signal_penalty(track, request) * 0.5
            depth = 0.0 if ablation == "no-heuristic-depth" else remaining * 0.08
            return target + signals + depth

        repository._heuristic = ablated_heuristic

    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(repository, name, original)
        repository._neighbor_cache.clear()


def _baseline_outcome(repository: Any, request: Any, algorithm: str, rng: random.Random):
    from app.repository import SearchOutcome

    if algorithm == "greedy":
        return repository._greedy_fallback(request.seed_track_id, request), math.nan

    path = [request.seed_track_id]
    total_cost = 0.0
    expansions = 0
    candidate_evaluations = 0
    while len(path) < request.playlist_length:
        current = repository.get_track(path[-1])
        candidates = [
            track
            for track in repository._tracks
            if repository._can_add_to_path(track, path, request)
        ]
        if not candidates:
            break
        candidate_evaluations += len(candidates)
        if algorithm == "random-valid":
            chosen = rng.choice(candidates)
        else:
            chosen = min(
                candidates,
                key=lambda track: (repository._edge_cost(current, track, request.constraints.tempo_policy), track.track_id),
            )
        total_cost += repository._composite_edge_cost(current, chosen, request)
        path.append(chosen.track_id)
        expansions += 1
    outcome = SearchOutcome(
        path=path,
        cost=total_cost,
        nodes_expanded=expansions,
        target_hit=repository._matches_target(repository.get_track(path[-1]), request),
    )
    return outcome, candidate_evaluations


def _ground_truth_hit(repository: Any, path: list[str], request: Any) -> bool:
    final_track = repository.get_track(path[-1])
    if request.target_type == "genre":
        return final_track.genre_label == request.target_value
    try:
        return final_track.cluster_id == int(request.target_value)
    except ValueError:
        return False


def _execute(repository: Any, request: Any, algorithm: str, rng: random.Random) -> dict[str, Any]:
    started = perf_counter()
    if algorithm in SEARCH_ALGORITHMS:
        strategy = {
            "bfs": repository._search_bfs,
            "dfs": repository._search_dfs,
            "ucs": repository._search_ucs,
            "ids": repository._search_ids,
            "astar": repository._search_astar,
            "idastar": repository._search_idastar,
        }[algorithm]
        neighbor_calls = 0
        current_neighbors = repository._neighbors

        def counted_neighbors(*args, **kwargs):
            nonlocal neighbor_calls
            neighbor_calls += 1
            return current_neighbors(*args, **kwargs)

        repository._neighbors = counted_neighbors
        search_started = perf_counter()
        try:
            outcome = strategy(request.seed_track_id, request)
        finally:
            repository._neighbors = current_neighbors
        search_runtime_ms = (perf_counter() - search_started) * 1000
        raw_search_success = outcome is not None
        search_nodes_expanded = outcome.nodes_expanded if outcome is not None else neighbor_calls
        fallback_used = outcome is None
        if outcome is None:
            outcome = repository._greedy_fallback(request.seed_track_id, request)
        candidate_evaluations = math.nan
    else:
        outcome, candidate_evaluations = _baseline_outcome(repository, request, algorithm, rng)
        search_runtime_ms = (perf_counter() - started) * 1000
        raw_search_success = math.nan
        search_nodes_expanded = math.nan
        fallback_used = False

    refined = repository._hill_climb_refine(outcome, request)
    runtime_ms = (perf_counter() - started) * 1000
    metrics = repository._playlist_quality_metrics(refined, request).model_dump()
    ground_truth_hit = _ground_truth_hit(repository, refined.path, request)
    metrics["constraint_satisfaction_rate"] = max(
        0.0,
        min(
            1.0,
            metrics["constraint_satisfaction_rate"]
            + (float(ground_truth_hit) - float(refined.target_hit)) / 4.0,
        ),
    )
    return {
        "playlist_length": len(refined.path),
        "playlist_track_ids": "|".join(refined.path),
        "runtime_ms": runtime_ms,
        "wall_runtime_ms": runtime_ms,
        "search_runtime_ms": search_runtime_ms,
        "nodes_expanded": refined.nodes_expanded,
        "search_nodes_expanded": search_nodes_expanded,
        "candidate_evaluations": candidate_evaluations,
        "total_cost": refined.cost,
        "target_hit": ground_truth_hit,
        "assisted_target_hit": refined.target_hit,
        "raw_search_success": raw_search_success,
        "fallback_used": fallback_used,
        **metrics,
    }


def _aggregate(rows: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["algorithm", "target_type", "cache_mode", "variant", "neighbor_limit"]
    output: list[dict[str, Any]] = []
    for keys, group in rows.groupby(group_columns, dropna=False, sort=True):
        row = dict(zip(group_columns, keys))
        row["runs"] = len(group)
        row["cases"] = int(group["case_id"].nunique())
        row["successful_runs"] = int(group["success"].sum())
        row["error_runs"] = int((~group["success"]).sum())
        row["success_rate"] = float(group["success"].mean())
        for metric in SUMMARY_METRICS:
            case_values = group.assign(_value=pd.to_numeric(group[metric], errors="coerce")).groupby("case_id")["_value"].mean()
            values = case_values.dropna().tolist()
            row[f"{metric}_n"] = len(values)
            row[f"{metric}_mean"] = sum(values) / len(values) if values else math.nan
            half_width = 1.96 * stdev(values) / math.sqrt(len(values)) if len(values) > 1 else math.nan
            row[f"{metric}_ci95"] = half_width
            row[f"{metric}_ci95_low"] = row[f"{metric}_mean"] - half_width if len(values) > 1 else math.nan
            row[f"{metric}_ci95_high"] = row[f"{metric}_mean"] + half_width if len(values) > 1 else math.nan
        output.append(row)
    return pd.DataFrame(output)


def _git_revision(repo_root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_benchmark_search(args) -> None:
    config = load_config(None)
    manifest = Path(args.manifest).expanduser() if args.manifest else config.manifest_path
    repository = _load_backend(config.repo_root, manifest)
    from app.models import PlaylistRequest

    if args.evaluation_split != "all":
        repository._tracks = [
            track for track in repository._tracks if track.evaluation_split == args.evaluation_split
        ]
        repository._track_index = {track.track_id: track for track in repository._tracks}
        cluster_points: dict[int, list[tuple[float, float, float]]] = {}
        for track in repository._tracks:
            if track.cluster_id is not None:
                cluster_points.setdefault(track.cluster_id, []).append(repository._feature_point(track))
        repository._cluster_centroids = {
            cluster_id: tuple(sum(point[index] for point in points) / len(points) for index in range(3))
            for cluster_id, points in cluster_points.items()
        }
        repository._neighbor_cache.clear()
        if not repository._tracks:
            raise SystemExit(f"No tracks belong to evaluation split '{args.evaluation_split}'.")

    if args.max_cases < 1 or args.repetitions < 1 or args.case_track_limit < 1:
        raise SystemExit("max-cases, repetitions, and case-track-limit must be positive.")
    if any(limit < 1 for limit in args.neighbor_limits):
        raise SystemExit("neighbor limits must be positive.")
    tracks = repository.list_tracks(limit=args.case_track_limit)
    if len(tracks) < args.playlist_length:
        raise SystemExit(f"Need at least {args.playlist_length} tracks for this benchmark.")

    cases = _build_cases(tracks, args.max_cases, args.random_seed)
    if not cases:
        raise SystemExit("No genre or cluster benchmark cases can be built from this library.")

    variants = _variants(args.ablations, args.neighbor_limits, 8)
    jobs = [
        (case, algorithm, variant, cache_mode, repetition)
        for case in cases
        for algorithm in args.algorithms
        for variant in variants
        for cache_mode in args.cache_modes
        for repetition in range(1, args.repetitions + 1)
    ]
    random.Random(args.random_seed).shuffle(jobs)
    rows: list[dict[str, Any]] = []

    for run_index, (case, algorithm, variant, cache_mode, repetition) in enumerate(jobs, start=1):
        run_seed = _stable_seed(
            args.random_seed,
            case["case_id"],
            algorithm,
            variant["name"],
            cache_mode,
            repetition,
        )
        request_data = {
            "seed_track_id": case["seed_track_id"],
            "target_type": case["target_type"],
            "target_value": case["target_value"],
            "algorithm": algorithm if algorithm in SEARCH_ALGORITHMS else "astar",
            "playlist_length": args.playlist_length,
            "max_total_duration_sec": args.max_total_duration_sec,
            "constraints": {
                "artist_repeat_limit": args.artist_repeat_limit,
                "explicit_filter": args.explicit_filter,
                "tempo_policy": args.tempo_policy,
            },
        }
        request = PlaylistRequest.model_validate(request_data)
        row = {
            "run_index": run_index,
            "repetition": repetition,
            "run_seed": run_seed,
            **case,
            "algorithm": algorithm,
            "variant": variant["name"],
            "ablation": variant["ablation"],
            "neighbor_limit": variant["neighbor_limit"],
            "cache_mode": cache_mode,
            "requested_playlist_length": args.playlist_length,
            "tempo_policy": args.tempo_policy,
            "artist_repeat_limit": args.artist_repeat_limit,
            "explicit_filter": args.explicit_filter,
            "max_total_duration_sec": args.max_total_duration_sec,
        }
        row.update({metric: math.nan for metric in SUMMARY_METRICS})
        row["playlist_track_ids"] = None
        row["success"] = False
        row["error_type"] = None
        row["error_message"] = None
        row["error_traceback"] = None
        try:
            with _benchmark_variant(repository, variant):
                repository._neighbor_cache.clear()
                if cache_mode == "warm":
                    _execute(repository, request, algorithm, random.Random(run_seed))
                row.update(_execute(repository, request, algorithm, random.Random(run_seed)))
            row["success"] = True
            print(f"[{run_index}/{len(jobs)}] ok {algorithm} {case['case_id']} {variant['name']} {cache_mode}")
        except Exception as exc:
            row["error_type"] = type(exc).__name__
            row["error_message"] = str(exc)
            row["error_traceback"] = traceback.format_exc()
            print(f"[{run_index}/{len(jobs)}] failed {algorithm} {case['case_id']}: {exc}")
        rows.append(row)

    output = Path(args.output).expanduser()
    summary_output = Path(args.summary_output).expanduser() if args.summary_output else output.with_name(f"{output.stem}_summary.csv")
    metadata_output = Path(args.metadata_output).expanduser() if args.metadata_output else output.with_name(f"{output.stem}_metadata.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    raw = pd.DataFrame(rows)
    raw.to_csv(output, index=False)
    summary = _aggregate(raw)
    summary.to_csv(summary_output, index=False)
    resolved_manifest = Path(repository.dataset_status.source).resolve()
    metadata = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": _git_revision(config.repo_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "manifest_path": os.path.relpath(resolved_manifest, metadata_output.parent),
        "manifest_sha256": _file_sha256(resolved_manifest),
        "using_sample_data": repository.dataset_status.using_sample_data,
        "library_track_count": repository.dataset_status.track_count,
        "benchmark_track_count": len(tracks),
        "search_graph_track_count": len(repository._tracks),
        "evaluation_split": args.evaluation_split,
        "case_count": len(cases),
        "run_count": len(rows),
        "confidence_interval": {
            "level": 0.95,
            "method": "normal approximation over case-level repetition means",
        },
        "cases": cases,
        "configuration": {
            key: value
            for key, value in vars(args).items()
            if isinstance(value, (str, int, float, bool, list, type(None)))
        },
        "outputs": {
            "raw_csv": os.path.relpath(output.resolve(), metadata_output.parent),
            "summary_csv": os.path.relpath(summary_output.resolve(), metadata_output.parent),
            "metadata_json": os.path.relpath(metadata_output.resolve(), metadata_output.parent),
        },
    }
    metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Raw benchmark written to {output}")
    print(f"Aggregate summary written to {summary_output}")
    print(f"Run metadata written to {metadata_output}")
    if not args.allow_incomplete and (not bool(raw["success"].any()) or bool((summary["success_rate"] < 1.0).any())):
        raise SystemExit("Benchmark contains failed or incomplete groups; inspect the raw CSV and rerun.")
