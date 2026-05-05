from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import math
import re

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

from .models import TrackAnalysisResponse, TrackRecord


SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}


@dataclass(frozen=True)
class AudioFeatureSummary:
    tempo: float
    energy: float
    valence: float
    duration_sec: int
    mfcc_mean: float
    chroma_mean: float
    spectral_contrast_mean: float
    zero_crossing_rate: float


def safe_track_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return cleaned[:48] or "uploaded-track"


def validate_audio_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_SUFFIXES))
        raise ValueError(f"Unsupported audio type '{suffix}'. Supported: {supported}")


def extract_audio_features(audio_path: Path, duration: float = 30.0, sample_rate: int = 22_050) -> AudioFeatureSummary:
    y, sr = librosa.load(audio_path, sr=sample_rate, mono=True, duration=duration)

    if y is None or len(y) == 0:
        raise ValueError(f"Empty or unreadable audio file: {audio_path}")

    y = np.asarray(y, dtype=np.float32).flatten()
    actual_duration = librosa.get_duration(y=y, sr=sr)

    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.asarray(tempo_arr).flatten()[0]) if np.asarray(tempo_arr).size else 0.0

    rms = librosa.feature.rms(y=y)
    raw_energy = float(np.mean(rms)) if rms is not None else 0.0
    # FMA RMS values are small, so scale into a useful 0-1 dashboard range.
    energy = max(0.0, min(1.0, raw_energy * 12.0))

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    raw_valence = float(np.mean(centroid) / 5000.0) if centroid is not None else 0.0
    valence = max(0.0, min(1.0, raw_valence))

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)

    return AudioFeatureSummary(
        tempo=round(tempo, 2),
        energy=round(energy, 4),
        valence=round(valence, 4),
        duration_sec=max(1, int(round(actual_duration))),
        mfcc_mean=round(float(np.mean(mfcc)), 4),
        chroma_mean=round(float(np.mean(chroma)), 4),
        spectral_contrast_mean=round(float(np.mean(contrast)), 4),
        zero_crossing_rate=round(float(np.mean(zcr)), 6),
    )


def save_mel_spectrogram_png(audio_path: Path, output_path: Path, duration: float = 30.0, sample_rate: int = 22_050) -> None:
    y, sr = librosa.load(audio_path, sr=sample_rate, mono=True, duration=duration)
    if y is None or len(y) == 0:
        raise ValueError(f"Empty or unreadable audio file: {audio_path}")

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=128)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mel_db, sr=sr, hop_length=512, x_axis="time", y_axis="mel")
    plt.colorbar(format="%+2.0f dB")
    plt.title(audio_path.name)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def _distance(a: TrackRecord, tempo: float, energy: float, valence: float) -> float:
    tempo_delta = abs((a.tempo or 0.0) - tempo) / 160.0
    energy_delta = abs((a.energy or 0.0) - energy)
    valence_delta = abs((a.valence or 0.0) - valence)
    return math.sqrt(tempo_delta**2 + energy_delta**2 + valence_delta**2)


def _cluster_centroids(tracks: list[TrackRecord]) -> dict[int, tuple[float, float, float]]:
    grouped: dict[int, list[TrackRecord]] = {}
    for track in tracks:
        if track.cluster_id is not None:
            grouped.setdefault(track.cluster_id, []).append(track)

    centroids: dict[int, tuple[float, float, float]] = {}
    for cluster_id, members in grouped.items():
        centroids[cluster_id] = (
            sum((track.tempo or 0.0) for track in members) / len(members),
            sum((track.energy or 0.0) for track in members) / len(members),
            sum((track.valence or 0.0) for track in members) / len(members),
        )
    return centroids


def assign_cluster(tracks: list[TrackRecord], features: AudioFeatureSummary) -> tuple[int | None, float]:
    centroids = _cluster_centroids(tracks)
    if not centroids:
        return None, 0.0

    best_cluster = None
    best_distance = float("inf")

    for cluster_id, (tempo, energy, valence) in centroids.items():
        distance = math.sqrt(
            ((features.tempo - tempo) / 160.0) ** 2
            + (features.energy - energy) ** 2
            + (features.valence - valence) ** 2
        )
        if distance < best_distance:
            best_cluster = cluster_id
            best_distance = distance

    # Convert distance into an interpretable fit score.
    mood_fit = 1.0 / (1.0 + best_distance)
    return best_cluster, round(max(0.0, min(1.0, mood_fit)), 4)


def estimate_preference_score(features: AudioFeatureSummary, explicit: bool = False) -> float:
    tempo_sweet_spot = 1.0 - min(1.0, abs(features.tempo - 115.0) / 115.0)
    explicit_bonus = 0.0 if explicit else 1.0
    score = (
        0.35 * features.energy
        + 0.30 * features.valence
        + 0.25 * tempo_sweet_spot
        + 0.10 * explicit_bonus
    )
    return round(max(0.0, min(1.0, score)), 4)


def estimate_genre_from_neighbors(
    tracks: list[TrackRecord],
    features: AudioFeatureSummary,
    neighbor_count: int = 7,
) -> tuple[str | None, float, list[dict[str, object]]]:
    candidates = [track for track in tracks if track.genre_label]
    if not candidates:
        return None, 0.0, []

    ranked = sorted(
        candidates,
        key=lambda track: _distance(track, features.tempo, features.energy, features.valence),
    )[:neighbor_count]

    genre_counts = Counter(track.genre_label for track in ranked if track.genre_label)
    if not genre_counts:
        return None, 0.0, []

    genre, count = genre_counts.most_common(1)[0]
    confidence = count / len(ranked)

    neighbors = [
        {
            "track_id": track.track_id,
            "title": track.title,
            "artist": track.artist,
            "genre_label": track.genre_label,
            "cluster_id": track.cluster_id,
            "distance": round(_distance(track, features.tempo, features.energy, features.valence), 4),
        }
        for track in ranked
    ]

    return genre, round(confidence, 4), neighbors


def build_uploaded_track_analysis(
    *,
    audio_path: Path,
    original_filename: str,
    title: str | None,
    artist: str | None,
    known_tracks: list[TrackRecord],
    spectrogram_path: Path,
    duration: float = 30.0,
) -> TrackAnalysisResponse:
    features = extract_audio_features(audio_path, duration=duration)
    save_mel_spectrogram_png(audio_path, spectrogram_path, duration=duration)

    cluster_id, mood_fit = assign_cluster(known_tracks, features)
    predicted_genre, genre_confidence, nearest_neighbors = estimate_genre_from_neighbors(known_tracks, features)
    preference_score = estimate_preference_score(features)

    track_id = f"upload-{uuid4().hex[:10]}"
    display_title = title.strip() if title and title.strip() else Path(original_filename).stem
    display_artist = artist.strip() if artist and artist.strip() else "Uploaded Track"

    summary = (
        f"Uploaded audio analyzed from {original_filename}. "
        f"Estimated {features.tempo:.0f} BPM, energy {features.energy:.2f}, "
        f"valence {features.valence:.2f}."
    )

    track = TrackRecord(
        track_id=track_id,
        title=display_title,
        artist=display_artist,
        duration_sec=features.duration_sec,
        genre_label=predicted_genre,
        cluster_id=cluster_id,
        energy=features.energy,
        tempo=features.tempo,
        valence=features.valence,
        explicit=False,
        audio_path=str(audio_path),
        stream_url=f"/tracks/{track_id}/stream",
        spectrogram_url=f"/tracks/{track_id}/spectrogram",
        summary=summary,
        preference_score=preference_score,
        mood_fit_score=mood_fit,
        cnn_genre_prediction=predicted_genre,
        cnn_genre_confidence=genre_confidence,
        signal_source="uploaded_audio_knn_analysis",
    )

    return TrackAnalysisResponse(
        track=track,
        detected_features={
            "tempo": features.tempo,
            "energy": features.energy,
            "valence": features.valence,
            "duration_sec": features.duration_sec,
            "mfcc_mean": features.mfcc_mean,
            "chroma_mean": features.chroma_mean,
            "spectral_contrast_mean": features.spectral_contrast_mean,
            "zero_crossing_rate": features.zero_crossing_rate,
        },
        assigned_cluster_id=cluster_id,
        predicted_genre=predicted_genre,
        predicted_genre_confidence=genre_confidence,
        nearest_neighbors=nearest_neighbors,
        explanation=(
            "The uploaded song was standardized to mono audio, converted into audio features, "
            "assigned to the closest existing mood cluster, and compared with the known library "
            "to estimate genre and nearest transition candidates. It can now be used as a seed track."
        ),
    )
