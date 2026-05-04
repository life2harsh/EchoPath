from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

from ..config import load_config

ALGORITHMS = ["bfs", "dfs", "ucs", "ids", "astar", "idastar"]


def _load_backend(repo_root: Path, manifest: Path | None):
    backend_path = repo_root / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    if manifest is not None:
        os.environ["ECHOPATH_LIBRARY_PATH"] = str(manifest.expanduser().resolve())

    from app.dependencies import get_repository
    from app.config import get_settings

    get_settings.cache_clear()
    get_repository.cache_clear()
    return get_repository()


def run_benchmark_search(args) -> None:
    config = load_config(None)
    manifest = Path(args.manifest).expanduser() if args.manifest else config.manifest_path
    repository = _load_backend(config.repo_root, manifest)

    tracks = repository.list_tracks(limit=10_000)
    if len(tracks) < args.playlist_length:
        raise SystemExit(f"Need at least {args.playlist_length} tracks for this benchmark.")

    genres = repository.list_genres()
    clusters = sorted({track.cluster_id for track in tracks if track.cluster_id is not None})
    seeds = tracks[: args.max_cases]

    cases = []
    for seed in seeds:
        if genres:
            cases.append((seed.track_id, "genre", genres[-1]))
        if clusters:
            cases.append((seed.track_id, "cluster", str(clusters[-1])))

    rows = []
    for seed_track_id, target_type, target_value in cases:
        for algorithm in ALGORITHMS:
            request = {
                "seed_track_id": seed_track_id,
                "target_type": target_type,
                "target_value": target_value,
                "algorithm": algorithm,
                "playlist_length": args.playlist_length,
                "constraints": {
                    "artist_repeat_limit": 1,
                    "explicit_filter": True,
                    "tempo_policy": args.tempo_policy,
                },
            }
            try:
                from app.models import PlaylistRequest

                result = repository.generate_playlist(PlaylistRequest.model_validate(request))
                rows.append(
                    {
                        "algorithm": algorithm,
                        "seed_track_id": seed_track_id,
                        "target_type": target_type,
                        "target_value": target_value,
                        "playlist_length": len(result.steps),
                        "runtime_ms": result.runtime_ms,
                        "nodes_expanded": result.nodes_expanded,
                        "total_cost": result.total_cost,
                        "target_hit": result.target_hit,
                    }
                )
                print(f"ok {algorithm} seed={seed_track_id} target={target_type}:{target_value}")
            except Exception as exc:
                rows.append(
                    {
                        "algorithm": algorithm,
                        "seed_track_id": seed_track_id,
                        "target_type": target_type,
                        "target_value": target_value,
                        "error": str(exc),
                    }
                )
                print(f"failed {algorithm} seed={seed_track_id}: {exc}")

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"Benchmark written to {output}")
