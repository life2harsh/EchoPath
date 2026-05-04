from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    repo_root: Path
    sample_data_path: Path
    dataset_manifest_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[2]
    default_manifest = repo_root / "data" / "library" / "tracks.json"
    manifest_value = os.getenv("ECHOPATH_LIBRARY_PATH", str(default_manifest))

    return Settings(
        app_name="EchoPath API",
        repo_root=repo_root,
        sample_data_path=repo_root / "artifacts" / "sample-data" / "demo_library.json",
        dataset_manifest_path=Path(manifest_value).expanduser(),
    )
