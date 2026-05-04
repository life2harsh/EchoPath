from __future__ import annotations

import argparse

from .commands.benchmark_search import run_benchmark_search
from .commands.ingest import run_ingest
from .commands.train_classical import run_train_classical
from .commands.train_cnn import run_train_cnn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echopath", description="EchoPath training command surface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Prepare the dataset manifest and extracted features.")
    ingest.add_argument("--dataset-root", dest="dataset_root", default=None)
    ingest.add_argument("--output-manifest", dest="output_manifest", default=None)

    train_classical = subparsers.add_parser("train-classical", help="Train the classical ML baselines.")
    train_classical.add_argument("--features", default=None)
    train_classical.add_argument("--label-column", default="preference_proxy")

    train_cnn = subparsers.add_parser("train-cnn", help="Train spectrogram CNNs on GPU or Hugging Face runners.")
    train_cnn.add_argument("--dataset-root", dest="dataset_root", default=None)
    train_cnn.add_argument("--hf-repo", dest="hf_repo", default=None)
    train_cnn.add_argument("--epochs", type=int, default=20)
    train_cnn.add_argument("--mixed-precision", action="store_true")

    benchmark = subparsers.add_parser("benchmark-search", help="Benchmark graph search algorithms on a fixed request set.")
    benchmark.add_argument("--manifest", default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args)
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
