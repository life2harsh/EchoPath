from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import librosa
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ..audio_features import extract_audio_features, feature_columns, find_audio_files, safe_float
from ..config import load_config


def _find_metadata_csv(dataset_root: Path, explicit_path: str | None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        return path if path.exists() else None

    candidates = [
        dataset_root / "fma_metadata" / "tracks.csv",
        dataset_root.parent / "fma_metadata" / "tracks.csv",
        dataset_root / "tracks.csv",
        dataset_root.parent / "tracks.csv",
    ]
    return next((path for path in candidates if path.exists()), None)


def _load_fma_metadata(metadata_csv: Path | None) -> dict[str, dict[str, Any]]:
    """
    Load FMA tracks.csv if available. FMA metadata uses two CSV header rows.
    Returns keys as zero-padded six-digit track IDs, matching the mp3 file names.
    """
    if metadata_csv is None:
        return {}

    try:
        frame = pd.read_csv(metadata_csv, header=[0, 1], index_col=0)
    except Exception:
        # Fallback for a simple one-row-header CSV.
        simple = pd.read_csv(metadata_csv)
        result: dict[str, dict[str, Any]] = {}
        for _, row in simple.iterrows():
            raw_id = row.get("track_id") or row.get("id") or row.get("track")
            if pd.isna(raw_id):
                continue
            track_id = str(int(raw_id)).zfill(6)
            result[track_id] = {
                "title": row.get("title"),
                "artist": row.get("artist"),
                "genre_label": row.get("genre") or row.get("genre_label") or row.get("genre_top"),
                "duration_sec": row.get("duration") or row.get("duration_sec"),
            }
        return result

    result = {}
    for raw_id, row in frame.iterrows():
        track_id = str(int(raw_id)).zfill(6)

        def get(section: str, field: str, default: Any = None) -> Any:
            try:
                value = row[(section, field)]
                if pd.isna(value):
                    return default
                return value
            except Exception:
                return default

        result[track_id] = {
            "title": get("track", "title", f"Track {track_id}"),
            "artist": get("artist", "name", "Unknown Artist"),
            "genre_label": get("track", "genre_top", "unknown"),
            "duration_sec": get("track", "duration", None),
        }
    return result


def _duration_seconds(audio_path: Path, metadata_value: Any) -> int:
    metadata_duration = int(safe_float(metadata_value, 0.0))
    if metadata_duration > 0:
        return metadata_duration
    try:
        return max(1, int(round(librosa.get_duration(path=str(audio_path)))))
    except Exception:
        return 180


def _build_track_record(audio_path: Path, dataset_root: Path, metadata: dict[str, Any], features: dict[str, float]) -> dict[str, Any]:
    track_id = audio_path.stem.zfill(6) if audio_path.stem.isdigit() else audio_path.stem
    title = metadata.get("title") or audio_path.stem
    artist = metadata.get("artist") or "Unknown Artist"
    genre_label = metadata.get("genre_label") or "unknown"

    return {
        "track_id": track_id,
        "title": str(title),
        "artist": str(artist),
        "duration_sec": _duration_seconds(audio_path, metadata.get("duration_sec")),
        "genre_label": str(genre_label) if str(genre_label).strip() else "unknown",
        "cluster_id": 0,
        "energy": features["energy"],
        "tempo": features["tempo"],
        "valence": features["valence"],
        "explicit": False,
        "audio_path": str(audio_path.resolve()),
        "summary": None,
        **features,
    }


def _assign_clusters(records: list[dict[str, Any]], cluster_count: int) -> None:
    if not records:
        return
    cols = feature_columns(records[0])
    if not cols:
        return

    frame = pd.DataFrame(records)
    x = frame[cols].fillna(0.0).to_numpy(dtype=float)
    n_clusters = max(1, min(cluster_count, len(records)))
    x_scaled = StandardScaler().fit_transform(x)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto").fit_predict(x_scaled)

    for record, label in zip(records, labels):
        record["cluster_id"] = int(label)


def _write_json_atomic(payload: Any, path: Path) -> None:
    temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_ingest(args) -> None:
    config = load_config(args.dataset_root)
    dataset_root = config.dataset_root.expanduser().resolve()
    manifest_path = Path(args.output_manifest).expanduser() if args.output_manifest else config.manifest_path
    features_csv = Path(args.features_csv).expanduser() if args.features_csv else config.artifacts_dir / "features.csv"
    checkpoint_path = manifest_path.with_suffix(manifest_path.suffix + ".partial.json")

    metadata_csv = _find_metadata_csv(dataset_root, args.metadata_csv)
    metadata_by_id = _load_fma_metadata(metadata_csv)
    audio_files = find_audio_files(dataset_root)
    if args.limit:
        audio_files = audio_files[: args.limit]

    if not audio_files:
        raise SystemExit(f"No audio files found under {dataset_root}")

    print(f"Dataset root: {dataset_root}")
    print(f"Audio files: {len(audio_files)}")
    print(f"Metadata CSV: {metadata_csv or 'not found, using file names'}")

    records: list[dict[str, Any]] = []
    failures: list[str] = []
    completed_ids: set[str] = set()
    if bool(getattr(args, "resume", False)) and checkpoint_path.exists():
        saved = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if isinstance(saved, list):
            records = saved
            completed_ids = {str(record.get("track_id")) for record in records}
            print(f"Resuming from checkpoint: {len(records)} tracks")

    for index, audio_path in enumerate(audio_files, start=1):
        track_id = audio_path.stem.zfill(6) if audio_path.stem.isdigit() else audio_path.stem
        if track_id in completed_ids:
            continue
        try:
            features = extract_audio_features(audio_path, duration=args.audio_duration)
            record = _build_track_record(audio_path, dataset_root, metadata_by_id.get(track_id, {}), features)
            records.append(record)
            completed_ids.add(track_id)
            checkpoint_every = max(1, int(getattr(args, "checkpoint_every", 100)))
            if len(records) % checkpoint_every == 0:
                _write_json_atomic(records, checkpoint_path)
            print(f"[{index}/{len(audio_files)}] ok {track_id} {record['title']}")
        except Exception as exc:
            failures.append(f"{audio_path}: {exc}")
            print(f"[{index}/{len(audio_files)}] failed {audio_path}: {exc}")

    if not records:
        raise SystemExit("Feature extraction failed for every audio file.")

    _assign_clusters(records, args.clusters)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    features_csv.parent.mkdir(parents=True, exist_ok=True)

    _write_json_atomic(records, manifest_path)
    pd.DataFrame(records).to_csv(features_csv, index=False)
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    print("")
    print("Ingest complete")
    print(f"Tracks written: {len(records)}")
    print(f"Manifest: {manifest_path}")
    print(f"Features CSV: {features_csv}")
    if failures:
        failure_log = config.artifacts_dir / "ingest_failures.txt"
        failure_log.parent.mkdir(parents=True, exist_ok=True)
        failure_log.write_text("\n".join(failures), encoding="utf-8")
        print(f"Failures: {len(failures)} written to {failure_log}")
