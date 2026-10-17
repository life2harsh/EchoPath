from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path, required: set[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = required - set(frame.columns)
    if frame.empty or missing:
        raise ValueError(f"Incomplete research artifact {path}: missing columns {sorted(missing)}")
    return frame


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_bar(frame: pd.DataFrame, x: str, y: str, title: str, ylabel: str, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(frame[x].astype(str), frame[y].astype(float), color="#4b7bec")
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", rotation=35)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=200)
    plt.close(figure)


def _artifact_paths(results_root: Path) -> list[Path]:
    fixed = [
        "data/splits.csv",
        "data/splits.csv.metadata.json",
        "data/features.csv",
        "data/tracks_enriched.json",
        "data/ingest_failures.txt",
        "classical/validation_metrics.csv",
        "classical/validation_predictions.csv",
        "classical/class_distribution.csv",
        "classical/final_test_metrics.json",
        "classical/final_test_classification_report.txt",
        "classical/final_test_confusion_matrix.csv",
        "classical/test_predictions.csv",
        "classical/training_config.json",
        "classical/best_classical_model.joblib",
        "cnn/cnn_architecture_comparison.csv",
        "cnn/cnn_predictions.csv",
        "cnn/test_predictions.csv",
        "cnn/final_test_metrics.json",
        "cnn/final_test_classification_report.txt",
        "cnn/final_test_confusion_matrix.csv",
        "cnn/training_config.json",
        "search/search_benchmark.csv",
        "search/search_benchmark_summary.csv",
        "search/search_benchmark_metadata.json",
        "search/search_ablations.csv",
        "search/search_ablations_summary.csv",
        "search/search_ablations_metadata.json",
    ]
    paths = [results_root / relative for relative in fixed]
    paths.extend((results_root / "classical").glob("*_validation_classification_report.txt"))
    for architecture in ("lenet", "vgg", "resnet"):
        architecture_dir = results_root / "cnn" / architecture
        paths.extend(
            architecture_dir / name
            for name in (
                "history.csv",
                "validation_classification_report.txt",
                "validation_predictions.csv",
                "model.pt",
                "best_checkpoint.pt",
            )
        )
    return sorted({path for path in paths if path.is_file()})


def run_summarize_research(args: Any) -> None:
    results_root = Path(args.results_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else results_root / "report"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    classical_validation_path = results_root / "classical" / "validation_metrics.csv"
    classical_test_path = results_root / "classical" / "final_test_metrics.json"
    cnn_validation_path = results_root / "cnn" / "cnn_architecture_comparison.csv"
    cnn_test_path = results_root / "cnn" / "final_test_metrics.json"
    search_summary_path = results_root / "search" / "search_benchmark_summary.csv"
    ablation_summary_path = results_root / "search" / "search_ablations_summary.csv"

    sections = ["# EchoPath Research Results", ""]
    if classical_validation_path.exists():
        classical = _read_csv(classical_validation_path, {"model", "macro_f1"}).sort_values("macro_f1", ascending=False)
        classical.to_csv(tables_dir / "classical_validation.csv", index=False)
        _save_bar(classical, "model", "macro_f1", "Classical model validation", "Macro F1", figures_dir / "classical_macro_f1.png")
        best = classical.iloc[0]
        sections.extend(["## Classical models", "", f"Best validation model: **{best['model']}** with macro F1 **{best['macro_f1']:.4f}**.", ""])

    classical_test = _read_json(classical_test_path)
    if classical_test:
        sections.extend([f"Final held-out test macro F1: **{classical_test['macro_f1']:.4f}**.", ""])

    if cnn_validation_path.exists():
        cnn = _read_csv(cnn_validation_path, {"architecture", "validation_macro_f1"}).sort_values("validation_macro_f1", ascending=False)
        cnn.to_csv(tables_dir / "cnn_validation.csv", index=False)
        _save_bar(cnn, "architecture", "validation_macro_f1", "CNN architecture validation", "Macro F1", figures_dir / "cnn_macro_f1.png")
        best = cnn.iloc[0]
        sections.extend(["## CNN models", "", f"Best validation architecture: **{best['architecture']}** with macro F1 **{best['validation_macro_f1']:.4f}**.", ""])

    cnn_test = _read_json(cnn_test_path)
    if cnn_test:
        sections.extend([f"Final held-out test macro F1: **{cnn_test['macro_f1']:.4f}**.", ""])

    if search_summary_path.exists():
        search = _read_csv(
            search_summary_path,
            {"algorithm", "variant", "cache_mode", "success_rate", "target_hit_mean", "wall_runtime_ms_mean", "total_cost_mean", "nodes_expanded_mean"},
        )
        if bool((search["success_rate"] < 1.0).any()):
            raise ValueError(f"Search artifact contains incomplete groups: {search_summary_path}")
        full = search[(search["variant"] == "full") & (search["cache_mode"] == "cold")].copy()
        if not full.empty:
            grouped = full.groupby("algorithm", as_index=False).agg(
                target_hit_rate=("target_hit_mean", "mean"),
                runtime_ms=("wall_runtime_ms_mean", "mean"),
                total_cost=("total_cost_mean", "mean"),
                nodes_expanded=("nodes_expanded_mean", "mean"),
                success_rate=("success_rate", "min"),
            )
            grouped.to_csv(tables_dir / "search_primary.csv", index=False)
            _save_bar(grouped, "algorithm", "target_hit_rate", "Search target success", "Target success rate", figures_dir / "search_target_success.png")
            _save_bar(grouped, "algorithm", "runtime_ms", "Search runtime", "Wall runtime (ms)", figures_dir / "search_runtime.png")
            sections.extend(["## Playlist search", "", "Primary cold-cache search results are available in `tables/search_primary.csv`.", ""])

    if ablation_summary_path.exists():
        ablations = _read_csv(ablation_summary_path, {"algorithm", "variant", "success_rate"})
        if bool((ablations["success_rate"] < 1.0).any()):
            raise ValueError(f"Ablation artifact contains incomplete groups: {ablation_summary_path}")
        ablations.to_csv(tables_dir / "search_ablations.csv", index=False)
        sections.extend(["A* ablation results are available in `tables/search_ablations.csv`.", ""])

    artifacts = []
    for path in _artifact_paths(results_root):
        artifacts.append(
            {
                "path": path.relative_to(results_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {"schema_version": 1, "results_root": ".", "artifacts": artifacts}
    (output_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sections.extend(["## Reproducibility", "", f"The artifact manifest contains checksums for **{len(artifacts)}** files.", ""])
    (output_dir / "research_summary.md").write_text("\n".join(sections), encoding="utf-8")
    print(f"Research summary written to {output_dir}")
