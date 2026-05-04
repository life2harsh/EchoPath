from __future__ import annotations

import argparse

from .commands.benchmark_search import run_benchmark_search
from .commands.enrich_manifest import run_enrich_manifest
from .commands.ingest import run_ingest
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
    train_classical.add_argument("--test-size", type=float, default=0.25)
    train_classical.add_argument("--min-per-class", type=int, default=20)
    train_classical.add_argument("--top-classes", type=int, default=None)
    train_classical.add_argument("--balance-classes", action="store_true")
    train_classical.add_argument("--max-per-class", type=int, default=None)
    train_classical.add_argument("--tune", action="store_true")

    train_cnn = subparsers.add_parser("train-cnn", help="Train and compare spectrogram CNN architectures.")
    train_cnn.add_argument("--dataset-root", dest="dataset_root", default=None)
    train_cnn.add_argument("--manifest", default=None)
    train_cnn.add_argument("--label-column", default="genre_label")
    train_cnn.add_argument("--architecture", choices=["lenet", "vgg", "resnet", "all"], default="lenet")
    train_cnn.add_argument("--top-classes", type=int, default=None)
    train_cnn.add_argument("--balance-classes", action="store_true")
    train_cnn.add_argument("--max-per-class", type=int, default=None)
    train_cnn.add_argument("--hf-repo", dest="hf_repo", default=None)
    train_cnn.add_argument("--epochs", type=int, default=20)
    train_cnn.add_argument("--batch-size", type=int, default=16)
    train_cnn.add_argument("--learning-rate", type=float, default=1e-3)
    train_cnn.add_argument("--test-size", type=float, default=0.2)
    train_cnn.add_argument("--audio-duration", type=float, default=30.0)
    train_cnn.add_argument("--sample-rate", type=int, default=22_050)
    train_cnn.add_argument("--n-mels", type=int, default=64)
    train_cnn.add_argument("--frames", type=int, default=128)
    train_cnn.add_argument("--min-per-class", type=int, default=5)
    train_cnn.add_argument("--mixed-precision", action="store_true")
    train_cnn.add_argument("--output-dir", default="artifacts/models/cnn")

    benchmark = subparsers.add_parser("benchmark-search", help="Benchmark graph search algorithms on a fixed request set.")
    benchmark.add_argument("--manifest", default=None)
    benchmark.add_argument("--output", default="artifacts/benchmarks/search_benchmark.csv")
    benchmark.add_argument("--playlist-length", type=int, default=5)
    benchmark.add_argument("--max-cases", type=int, default=10)
    benchmark.add_argument("--tempo-policy", choices=["any", "steady", "lift", "cooldown"], default="lift")

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

    parser.error("Unknown command")
