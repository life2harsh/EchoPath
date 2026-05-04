from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class TrainingConfig:
    repo_root: Path
    dataset_root: Path
    manifest_path: Path
    artifacts_dir: Path


def load_config(dataset_root: str | None = None) -> TrainingConfig:
    repo_root = Path(__file__).resolve().parents[2]
    resolved_dataset_root = Path(dataset_root or os.getenv("ECHOPATH_DATASET_ROOT", repo_root / "data")).expanduser()
    return TrainingConfig(
        repo_root=repo_root,
        dataset_root=resolved_dataset_root,
        manifest_path=repo_root / "data" / "library" / "tracks.json",
        artifacts_dir=repo_root / "artifacts",
    )
