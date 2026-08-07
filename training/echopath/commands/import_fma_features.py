from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..audio_features import find_audio_files, normalize_01, safe_float
from .ingest import _assign_clusters, _write_json_atomic


def _column_name(column: tuple[Any, ...]) -> str:
    parts = [str(part).strip() for part in column if str(part).strip() and not str(part).startswith("Unnamed:")]
    return "fma_" + "_".join(parts).replace(" ", "_").replace("/", "_")


def _first_column(columns: pd.MultiIndex, family: str, statistic: str) -> tuple[Any, ...] | None:
    for column in columns:
        if str(column[0]) == family and str(column[1]) == statistic:
            return column
    return None


def _chroma_mean(frame: pd.DataFrame) -> pd.Series:
    columns = [column for column in frame.columns if str(column[0]) == "chroma_stft" and str(column[1]) == "mean"]
    if not columns:
        return pd.Series(0.0, index=frame.index)
    return frame[columns].apply(pd.to_numeric, errors="coerce").mean(axis=1).fillna(0.0)


def _value(frame: pd.DataFrame, column: tuple[Any, ...] | None) -> pd.Series:
    if column is None:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _audio_paths(dataset_root: Path) -> dict[int, Path]:
    paths: dict[int, Path] = {}
    for path in find_audio_files(dataset_root):
        if path.stem.isdigit():
            paths[int(path.stem)] = path
    return paths


def _metadata_table(tracks_csv: Path) -> pd.DataFrame:
    tracks = pd.read_csv(tracks_csv, header=[0, 1], index_col=0)
    tracks.index = pd.to_numeric(tracks.index, errors="coerce")
    tracks = tracks.loc[tracks.index.notna()].copy()
    tracks.index = tracks.index.astype(int)
    subset = tracks[("set", "subset")].astype(str).str.strip().str.lower()
    return tracks.loc[subset.isin({"small", "medium"})]


def _records(features: pd.DataFrame, metadata: pd.DataFrame, audio_paths: dict[int, Path]) -> tuple[list[dict[str, Any]], list[str]]:
    available = metadata.index.intersection(features.index).intersection(pd.Index(audio_paths))
    missing = []
    for track_id in metadata.index:
        if track_id not in audio_paths:
            missing.append(f"{track_id:06d}: audio file missing")
        elif track_id not in features.index:
            missing.append(f"{track_id:06d}: official FMA feature row missing")

    selected_features = features.loc[available].sort_index()
    selected_metadata = metadata.loc[available]
    tempo = _value(selected_features, _first_column(selected_features.columns, "rhythm", "tempo"))
    rms = _value(selected_features, _first_column(selected_features.columns, "rmse", "mean"))
    centroid = _value(selected_features, _first_column(selected_features.columns, "spectral_centroid", "mean"))
    chroma = _chroma_mean(selected_features)

    records: list[dict[str, Any]] = []
    for position, track_id in enumerate(selected_features.index):
        row = selected_features.iloc[position]
        meta = selected_metadata.iloc[position]
        energy_raw = safe_float(rms.iloc[position])
        brightness = normalize_01(safe_float(centroid.iloc[position]), 500.0, 5_000.0)
        valence = float(np.clip(0.7 * brightness + 0.3 * safe_float(chroma.iloc[position]), 0.0, 1.0))
        flat_features = {
            _column_name(column): safe_float(value)
            for column, value in row.items()
        }
        records.append(
            {
                "track_id": f"{int(track_id):06d}",
                "title": str(meta[("track", "title")] if pd.notna(meta[("track", "title")]) else f"Track {track_id:06d}"),
                "artist": str(meta[("artist", "name")] if pd.notna(meta[("artist", "name")]) else "Unknown Artist"),
                "duration_sec": int(safe_float(meta[("track", "duration")], 180.0)),
                "genre_label": str(meta[("track", "genre_top")] if pd.notna(meta[("track", "genre_top")]) else "unknown"),
                "cluster_id": 0,
                "energy": normalize_01(energy_raw, 0.0, 0.25),
                "tempo": safe_float(tempo.iloc[position]),
                "valence": valence,
                "explicit": False,
                "audio_path": str(audio_paths[int(track_id)].resolve()),
                "summary": None,
                **flat_features,
            }
        )
    return records, missing


def run_import_fma_features(args) -> None:
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    tracks_csv = Path(args.metadata_csv).expanduser().resolve()
    fma_features_csv = Path(args.fma_features_csv).expanduser().resolve()
    manifest_path = Path(args.output_manifest).expanduser()
    features_csv = Path(args.features_csv).expanduser()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    features_csv.parent.mkdir(parents=True, exist_ok=True)

    print("Loading FMA metadata...")
    metadata = _metadata_table(tracks_csv)
    print("Scanning audio files...")
    audio_paths = _audio_paths(dataset_root)
    print("Loading official FMA audio features...")
    features = pd.read_csv(fma_features_csv, header=[0, 1, 2], index_col=0)
    features.index = pd.to_numeric(features.index, errors="coerce")
    features = features.loc[features.index.notna()].copy()
    features.index = features.index.astype(int)

    records, missing = _records(features, metadata, audio_paths)
    if not records:
        raise SystemExit("No FMA Small/Medium tracks had matching metadata, audio, and official features.")
    print(f"Matched tracks: {len(records)}")
    # FMA supplies hundreds of descriptors; mood clusters intentionally use the
    # same interpretable tempo-energy-valence space used by playlist search.
    cluster_inputs = [{key: record[key] for key in ("tempo", "energy", "valence")} for record in records]
    _assign_clusters(cluster_inputs, args.clusters)
    for record, cluster_input in zip(records, cluster_inputs):
        record["cluster_id"] = cluster_input["cluster_id"]
    _write_json_atomic(records, manifest_path)
    pd.DataFrame(records).to_csv(features_csv, index=False)
    provenance = {
        "source": "FMA official precomputed features.csv",
        "source_path": str(fma_features_csv),
        "feature_count": int(features.shape[1]),
        "subset_policy": "FMA Small plus FMA Medium additions (set.subset in {'small', 'medium'})",
        "matched_tracks": len(records),
        "missing_tracks": len(missing),
    }
    (manifest_path.parent / "fma_feature_import_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    if missing:
        (manifest_path.parent / "fma_feature_import_failures.txt").write_text("\n".join(missing), encoding="utf-8")

    print("FMA feature import complete")
    print(f"Manifest: {manifest_path}")
    print(f"Features CSV: {features_csv}")
    print(f"Missing tracks: {len(missing)}")
