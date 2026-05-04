from __future__ import annotations

from pathlib import Path
from typing import Any

import librosa
import numpy as np

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}


def find_audio_files(dataset_root: Path) -> list[Path]:
    """Return audio files below dataset_root, sorted for reproducible manifests."""
    return sorted(
        path
        for path in dataset_root.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if np.isnan(result) or np.isinf(result):
            return default
        return result
    except Exception:
        return default


def normalize_01(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return float(np.clip((value - low) / (high - low), 0.0, 1.0))


def extract_audio_features(
    audio_path: str | Path,
    *,
    sr: int = 22_050,
    duration: float = 30.0,
    n_mfcc: int = 13,
) -> dict[str, float]:
    """
    Extract backend-friendly and ML-friendly audio features.

    Backend fields:
    - tempo
    - energy
    - valence

    Extra fields are used by clustering/classical ML and are ignored by the backend model.
    """
    path = Path(audio_path)
    y, actual_sr = librosa.load(path, sr=sr, mono=True, duration=duration)
    y = np.asarray(y, dtype=np.float32).flatten()
    if y.size == 0:
        raise ValueError(f"Audio file is empty: {path}")

    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=actual_sr)
    tempo = safe_float(np.ravel(tempo_arr)[0] if np.size(tempo_arr) else tempo_arr)

    rms = librosa.feature.rms(y=y)[0]
    energy_raw = safe_float(np.mean(rms))
    energy = normalize_01(energy_raw, 0.0, 0.25)

    centroid = librosa.feature.spectral_centroid(y=y, sr=actual_sr)[0]
    centroid_mean = safe_float(np.mean(centroid))
    brightness = normalize_01(centroid_mean, 500.0, 5_000.0)

    chroma = librosa.feature.chroma_stft(y=y, sr=actual_sr)
    chroma_mean = np.mean(chroma, axis=1)

    # This is not emotional valence ground truth. It is a transparent audio-brightness proxy.
    valence = float(np.clip(0.7 * brightness + 0.3 * safe_float(np.mean(chroma_mean)), 0.0, 1.0))

    zcr = librosa.feature.zero_crossing_rate(y)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=actual_sr)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=actual_sr)
    mfcc = librosa.feature.mfcc(y=y, sr=actual_sr, n_mfcc=n_mfcc)

    features: dict[str, float] = {
        "tempo": round(tempo, 4),
        "energy": round(energy, 6),
        "valence": round(valence, 6),
        "rms_mean": round(energy_raw, 8),
        "rms_std": round(safe_float(np.std(rms)), 8),
        "spectral_centroid_mean": round(centroid_mean, 6),
        "spectral_centroid_std": round(safe_float(np.std(centroid)), 6),
        "zero_crossing_rate_mean": round(safe_float(np.mean(zcr)), 8),
        "spectral_rolloff_mean": round(safe_float(np.mean(rolloff)), 6),
    }

    for i, value in enumerate(np.mean(mfcc, axis=1), start=1):
        features[f"mfcc_{i:02d}_mean"] = round(safe_float(value), 6)
    for i, value in enumerate(np.std(mfcc, axis=1), start=1):
        features[f"mfcc_{i:02d}_std"] = round(safe_float(value), 6)
    for i, value in enumerate(chroma_mean, start=1):
        features[f"chroma_{i:02d}_mean"] = round(safe_float(value), 6)
    for i, value in enumerate(np.mean(contrast, axis=1), start=1):
        features[f"spectral_contrast_{i:02d}_mean"] = round(safe_float(value), 6)

    return features


def feature_columns(row: dict[str, Any]) -> list[str]:
    """Return numeric feature columns suitable for clustering/training."""
    blocked = {
        "track_id",
        "title",
        "artist",
        "genre_label",
        "audio_path",
        "stream_url",
        "spectrogram_url",
        "summary",
        "explicit",
        "cluster_id",
        "duration_sec",
    }
    return sorted(
        key
        for key, value in row.items()
        if key not in blocked and isinstance(value, (int, float)) and not isinstance(value, bool)
    )
