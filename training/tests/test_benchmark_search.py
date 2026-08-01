from types import SimpleNamespace

import pandas as pd

from echopath.commands.benchmark_search import _aggregate, _build_cases, _stable_seed


def _tracks():
    return [
        SimpleNamespace(track_id=f"t{index}", genre_label=genre, cluster_id=cluster)
        for index, (genre, cluster) in enumerate(
            [("jazz", 0), ("jazz", 0), ("rock", 1), ("rock", 1), ("folk", 2), ("folk", 2)]
        )
    ]


def test_cases_are_reproducible_stratified_and_nontrivial() -> None:
    first = _build_cases(_tracks(), max_cases=5, seed=17)
    second = _build_cases(_tracks(), max_cases=5, seed=17)

    assert first == second
    assert len(first) == 10
    assert {case["target_type"] for case in first} == {"genre", "cluster"}
    assert all(case["seed_stratum"] != case["target_value"] for case in first)
    assert first != _build_cases(_tracks(), max_cases=5, seed=18)


def test_stable_seed_does_not_depend_on_process_hashing() -> None:
    assert _stable_seed(2025, "case", "astar", 1) == _stable_seed(2025, "case", "astar", 1)
    assert _stable_seed(2025, "case", "astar", 1) != _stable_seed(2025, "case", "astar", 2)


def test_aggregate_preserves_errors_and_computes_confidence_intervals() -> None:
    base = {
        "algorithm": "astar",
        "target_type": "genre",
        "cache_mode": "cold",
        "variant": "full",
        "neighbor_limit": 8,
    }
    rows = []
    for success, runtime in [(True, 10.0), (True, 14.0), (False, float("nan"))]:
        row = {**base, "success": success, "case_id": f"case-{len(rows)}"}
        from echopath.commands.benchmark_search import SUMMARY_METRICS

        for metric in SUMMARY_METRICS:
            row[metric] = runtime
        rows.append(row)

    summary = _aggregate(pd.DataFrame(rows)).iloc[0]

    assert summary["runs"] == 3
    assert summary["successful_runs"] == 2
    assert summary["error_runs"] == 1
    assert summary["cases"] == 3
    assert summary["runtime_ms_mean"] == 12.0
    assert summary["runtime_ms_ci95"] > 0
