from __future__ import annotations

from ..config import load_config


def run_train_cnn(args) -> None:
    config = load_config(args.dataset_root)
    print("EchoPath CNN training scaffold")
    print(f"Dataset root: {config.dataset_root}")
    print(f"Epochs: {args.epochs}")
    print(f"Mixed precision: {'enabled' if args.mixed_precision else 'disabled'}")
    print(f"Hugging Face repo: {args.hf_repo or 'not set'}")
    print("")
    print("Planned models: LeNet-style, VGG-style, ResNet-style")
    print("This command will manage Accelerate launch configs, checkpoint saving, and HF uploads.")
