from __future__ import annotations

from pathlib import Path

from ..config import load_config


def run_ingest(args) -> None:
    config = load_config(args.dataset_root)
    manifest_path = Path(args.output_manifest).expanduser() if args.output_manifest else config.manifest_path

    print("EchoPath ingest scaffold")
    print(f"Dataset root: {config.dataset_root}")
    print(f"Output manifest: {manifest_path}")
    print("")
    print("Next implementation step:")
    print("- scan the dataset root for audio files and metadata")
    print("- extract classical features and mel-spectrogram tensors")
    print("- write a backend-compatible track manifest to the output path")
