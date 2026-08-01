from __future__ import annotations

import argparse

from .commands.benchmark_search import ABLATIONS, ALGORITHMS, run_benchmark_search
from .commands.enrich_manifest import run_enrich_manifest
from .commands.ingest import run_ingest
from .commands.summarize_research import run_summarize_research
from .commands.train_classical import run_train_classical
from .commands.train_cnn import run_train_cnn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echopath", description="EchoPath training command surface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Prepare the dataset manifest and extracted features.")
    ingest.add_argument("--dataset-root", dest="dataset_root", default=None)
    ingest.add_argument("--metadata-csv", dest="metadata_csv", default=None)
    ingest.add_argument("--output-manifest", dest="output_manifest", default=None)
    ingest.add_argument("--features-csv", dest="features_csv", default=None)
    ingest.add_argument("--audio-duration", dest="audio_duration", type=float, default=30.0)
    ingest.add_argument("--clusters", type=int, default=8)
    ingest.add_argument("--limit", type=int, default=None)

    enrich = subparsers.add_parser("enrich-manifest", help="Add ML/CNN integration signals to the backend manifest.")
    enrich.add_argument("--manifest", required=True)
    enrich.add_argument("--features", default=None)
    enrich.add_argument("--output", default=None)
    enrich.add_argument("--cnn-predictions", dest="cnn_predictions", default=None)

    train_classical = subparsers.add_parser("train-classical", help="Train the classical ML baselines.")
    train_classical.add_argument("--features", default=None)
    train_classical.add_argument("--manifest", default=None)
    train_classical.add_argument("--label-column", default="genre_label")
    train_classical.add_argument("--output-dir", default="artifacts/models/classical")
    train_classical.add_argument("--test-size", type=float, default=0.15)
    train_classical.add_argument("--validation-size", type=float, default=0.15)
    train_classical.add_argument("--splits", default=None)
    train_classical.add_argument("--group-column", default="artist")
    train_classical.add_argument("--seed", type=int, default=42)
    train_classical.add_argument("--regenerate-splits", action="store_true")
    train_classical.add_argument("--formal-evaluation", action="store_true")
    train_classical.add_argument("--min-per-class", type=int, default=20)
    train_classical.add_argument("--top-classes", type=int, default=None)
    train_classical.add_argument("--classes", nargs="+", default=None)
    train_classical.add_argument("--balance-classes", action="store_true")
    train_classical.add_argument("--max-per-class", type=int, default=None)
    train_classical.add_argument("--tune", action="store_true")

    train_cnn = subparsers.add_parser("train-cnn", help="Train and compare spectrogram CNN architectures.")
    train_cnn.add_argument("--dataset-root", dest="dataset_root", default=None)
    train_cnn.add_argument("--manifest", default=None)
    train_cnn.add_argument("--label-column", default="genre_label")
    train_cnn.add_argument("--architecture", choices=["lenet", "vgg", "resnet", "all"], default="lenet")
    train_cnn.add_argument("--top-classes", type=int, default=None)
    train_cnn.add_argument("--classes", nargs="+", default=None)
    train_cnn.add_argument("--balance-classes", action="store_true")
    train_cnn.add_argument("--max-per-class", type=int, default=None)
    train_cnn.add_argument("--epochs", type=int, default=20)
    train_cnn.add_argument("--batch-size", type=int, default=16)
    train_cnn.add_argument("--learning-rate", type=float, default=1e-3)
    train_cnn.add_argument("--test-size", type=float, default=0.15)
    train_cnn.add_argument("--validation-size", type=float, default=0.15)
    train_cnn.add_argument("--splits", default=None)
    train_cnn.add_argument("--group-column", default="artist")
    train_cnn.add_argument("--seed", type=int, default=42)
    train_cnn.add_argument("--regenerate-splits", action="store_true")
    train_cnn.add_argument("--formal-evaluation", action="store_true")
    train_cnn.add_argument("--audio-duration", type=float, default=30.0)
    train_cnn.add_argument("--sample-rate", type=int, default=22_050)
    train_cnn.add_argument("--n-mels", type=int, default=64)
    train_cnn.add_argument("--frames", type=int, default=128)
    train_cnn.add_argument("--min-per-class", type=int, default=5)
    train_cnn.add_argument("--mixed-precision", action="store_true")
    train_cnn.add_argument("--cache-dir", default=None)
    train_cnn.add_argument("--resume", action="store_true")
    train_cnn.add_argument("--num-workers", type=int, default=0)
    train_cnn.add_argument("--output-dir", default="artifacts/models/cnn")

    benchmark = subparsers.add_parser("benchmark-search", help="Run reproducible search experiments and baselines.")
    benchmark.add_argument("--manifest", default=None)
    benchmark.add_argument("--output", default="artifacts/benchmarks/search_benchmark.csv")
    benchmark.add_argument("--summary-output", default=None)
    benchmark.add_argument("--metadata-output", default=None)
    benchmark.add_argument("--playlist-length", type=int, default=5)
    benchmark.add_argument("--max-cases", type=int, default=3)
    benchmark.add_argument("--repetitions", type=int, default=3)
    benchmark.add_argument("--random-seed", type=int, default=2025)
    benchmark.add_argument("--case-track-limit", type=int, default=10_000)
    benchmark.add_argument("--evaluation-split", choices=["all", "train", "validation", "test"], default="all")
    benchmark.add_argument("--algorithms", nargs="+", choices=ALGORITHMS, default=ALGORITHMS)
    benchmark.add_argument("--cache-modes", nargs="+", choices=["cold", "warm"], default=["cold"])
    benchmark.add_argument("--ablations", nargs="*", choices=ABLATIONS, default=[])
    benchmark.add_argument("--neighbor-limits", nargs="*", type=int, default=[])
    benchmark.add_argument("--tempo-policy", choices=["any", "steady", "lift", "cooldown"], default="lift")
    benchmark.add_argument("--artist-repeat-limit", type=int, choices=[1, 2, 3], default=1)
    benchmark.add_argument("--max-total-duration-sec", type=int, default=None)
    benchmark.add_argument("--allow-explicit", dest="explicit_filter", action="store_false")
    benchmark.add_argument("--allow-incomplete", action="store_true")
    benchmark.set_defaults(explicit_filter=True)

    summarize = subparsers.add_parser("summarize-research", help="Generate manuscript-ready research tables and figures.")
    summarize.add_argument("--results-root", required=True)
    summarize.add_argument("--output-dir", default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args)
        return
    if args.command == "enrich-manifest":
        run_enrich_manifest(args)
        return
    if args.command == "train-classical":
        run_train_classical(args)
        return
    if args.command == "train-cnn":
        run_train_cnn(args)
        return
    if args.command == "benchmark-search":
        run_benchmark_search(args)
        return
    if args.command == "summarize-research":
        run_summarize_research(args)
        return

    parser.error("Unknown command")
