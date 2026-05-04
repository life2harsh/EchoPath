from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def _arg(args: Any, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _clip01(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_series(values: list[float]) -> dict[int, float]:
    if not values:
        return {}
    lo = min(values)
    hi = max(values)
    spread = max(hi - lo, 1e-9)
    return {idx: _clip01((value - lo) / spread) for idx, value in enumerate(values)}


def _load_cnn_predictions(path: str | None) -> dict[str, tuple[str, float]]:
    if not path:
        return {}

    frame = pd.read_csv(Path(path).expanduser())
    required = {"track_id", "prediction", "confidence"}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"CNN prediction CSV missing columns: {sorted(missing)}")

    predictions: dict[str, tuple[str, float]] = {}
    for row in frame.to_dict("records"):
        predictions[str(row["track_id"])] = (
            str(row["prediction"]),
            _clip01(_to_float(row["confidence"], 0.5)),
        )
    return predictions


def run_enrich_manifest(args) -> None:
    manifest_path = Path(_arg(args, "manifest", "data/library/tracks.json")).expanduser()
    output_path = Path(_arg(args, "output", str(manifest_path))).expanduser()
    features_path = _arg(args, "features", None)
    cnn_predictions_path = _arg(args, "cnn_predictions", None)

    tracks = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(tracks, list) or not tracks:
        raise SystemExit(f"No tracks found in manifest: {manifest_path}")

    feature_rows: dict[str, dict[str, Any]] = {}
    if features_path:
        features = pd.read_csv(Path(features_path).expanduser())
        if "track_id" not in features.columns:
            raise SystemExit("features CSV must include track_id")
        feature_rows = {str(row["track_id"]): row for row in features.to_dict("records")}

    tempos: list[float] = []
    energies: list[float] = []
    valences: list[float] = []

    for track in tracks:
        row = feature_rows.get(str(track.get("track_id")), {})
        tempos.append(_to_float(track.get("tempo", row.get("tempo")), 0.0))
        energies.append(_to_float(track.get("energy", row.get("energy")), 0.0))
        valences.append(_to_float(track.get("valence", row.get("valence")), 0.0))

    energy_norm = _normalize_series(energies)
    valence_norm = _normalize_series(valences)

    cluster_points: dict[int, list[tuple[float, float, float]]] = {}
    cluster_genres: dict[int, list[str]] = {}

    for idx, track in enumerate(tracks):
        cluster_id = track.get("cluster_id")
        if cluster_id is None:
            continue
        try:
            cid = int(cluster_id)
        except (TypeError, ValueError):
            continue

        tempo = tempos[idx] / 200.0
        energy = energy_norm.get(idx, 0.0)
        valence = valence_norm.get(idx, 0.0)
        cluster_points.setdefault(cid, []).append((tempo, energy, valence))

        genre = track.get("genre_label")
        if genre:
            cluster_genres.setdefault(cid, []).append(str(genre))

    centroids: dict[int, tuple[float, float, float]] = {}
    for cid, points in cluster_points.items():
        n = len(points)
        centroids[cid] = (
            sum(p[0] for p in points) / n,
            sum(p[1] for p in points) / n,
            sum(p[2] for p in points) / n,
        )

    max_cluster_distance: dict[int, float] = {}
    for cid, points in cluster_points.items():
        centroid = centroids[cid]
        distances = [
            math.sqrt(sum((point[i] - centroid[i]) ** 2 for i in range(3)))
            for point in points
        ]
        max_cluster_distance[cid] = max(max(distances), 1e-9)

    cluster_majority_genre: dict[int, tuple[str, float]] = {}
    for cid, genres in cluster_genres.items():
        counts = Counter(genres)
        genre, count = counts.most_common(1)[0]
        cluster_majority_genre[cid] = (genre, _clip01(count / len(genres)))

    cnn_predictions = _load_cnn_predictions(cnn_predictions_path)

    for idx, track in enumerate(tracks):
        tempo = tempos[idx]
        energy = energy_norm.get(idx, 0.0)
        valence = valence_norm.get(idx, 0.0)

        tempo_sweet_spot = 1.0 - min(1.0, abs(tempo - 115.0) / 115.0)
        explicit_bonus = 0.0 if bool(track.get("explicit", False)) else 1.0
        preference_score = (
            0.35 * energy
            + 0.30 * valence
            + 0.25 * tempo_sweet_spot
            + 0.10 * explicit_bonus
        )
        track["preference_score"] = round(_clip01(preference_score), 4)

        cid_raw = track.get("cluster_id")
        mood_fit_score = 0.5
        try:
            cid = int(cid_raw)
            centroid = centroids[cid]
            point = (tempo / 200.0, energy, valence)
            distance = math.sqrt(sum((point[i] - centroid[i]) ** 2 for i in range(3)))
            mood_fit_score = 1.0 - (distance / max_cluster_distance[cid])
        except Exception:
            pass
        track["mood_fit_score"] = round(_clip01(mood_fit_score), 4)

        track_id = str(track.get("track_id"))
        if track_id in cnn_predictions:
            prediction, confidence = cnn_predictions[track_id]
            track["cnn_genre_prediction"] = prediction
            track["cnn_genre_confidence"] = round(confidence, 4)
            track["signal_source"] = "cnn_prediction_csv"
        else:
            prediction = track.get("genre_label") or "unknown"
            confidence = 0.50
            try:
                cid = int(cid_raw)
                prediction, confidence = cluster_majority_genre.get(cid, (prediction, confidence))
            except Exception:
                pass
            track["cnn_genre_prediction"] = str(prediction)
            track["cnn_genre_confidence"] = round(_clip01(confidence), 4)
            track["signal_source"] = "cluster_majority_proxy"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(tracks, indent=2), encoding="utf-8")

    print("Manifest enrichment complete")
    print(f"Input manifest: {manifest_path}")
    print(f"Output manifest: {output_path}")
    print(f"Tracks enriched: {len(tracks)}")
    print("Added fields:")
    print("- preference_score")
    print("- mood_fit_score")
    print("- cnn_genre_prediction")
    print("- cnn_genre_confidence")
    print("- signal_source")
