from __future__ import annotations

import hashlib
import os
from pathlib import Path

import librosa
import numpy as np

CACHE_SCHEMA = "mel-v2-full-clip"
HOP_LENGTH = 512
N_FFT = 2048


def frames_for_duration(audio_duration: float, sample_rate: int) -> int:
    return 1 + int(round(audio_duration * sample_rate)) // HOP_LENGTH


def mel_array(audio_path: str | Path, sample_rate: int, audio_duration: float, n_mels: int, frames: int) -> np.ndarray:
    y, sr = librosa.load(str(audio_path), sr=sample_rate, mono=True, duration=audio_duration)
    if y is None or len(y) == 0:
        raise ValueError(f"Empty audio: {audio_path}")

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=n_mels)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    if mel_db.shape[1] < frames:
        mel_db = np.pad(mel_db, ((0, 0), (0, frames - mel_db.shape[1])), mode="constant", constant_values=float(mel_db.min()))
    else:
        mel_db = mel_db[:, :frames]

    mean = float(mel_db.mean())
    std = float(mel_db.std()) or 1.0
    return ((mel_db - mean) / std).astype(np.float32)[None, :, :]


def cache_path(cache_dir: Path, audio_path: Path, sample_rate: int, audio_duration: float, n_mels: int, frames: int) -> Path:
    stat = audio_path.stat()
    payload = (
        f"{CACHE_SCHEMA}:{audio_path}:{stat.st_size}:{stat.st_mtime_ns}:{sample_rate}:"
        f"{audio_duration}:{n_mels}:{frames}"
    )
    return cache_dir / f"{hashlib.sha256(payload.encode('utf-8')).hexdigest()}.npy"


def load_or_compute(cache_dir: Path, audio_path: Path, sample_rate: int, audio_duration: float, n_mels: int, frames: int) -> np.ndarray:
    path = cache_path(cache_dir, audio_path, sample_rate, audio_duration, n_mels, frames)
    if path.exists():
        try:
            array = np.load(path)
            if array.shape == (1, n_mels, frames):
                return array
        except (OSError, ValueError):
            pass
    array = mel_array(audio_path, sample_rate, audio_duration, n_mels, frames)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.stem}.{os.getpid()}.tmp.npy")
    np.save(temporary, array)
    temporary.replace(path)
    return array


def warm_cache_entry(job: tuple[str, str, int, float, int, int]) -> tuple[str, str | None]:
    audio_path, cache_dir, sample_rate, audio_duration, n_mels, frames = job
    try:
        load_or_compute(Path(cache_dir), Path(audio_path), sample_rate, audio_duration, n_mels, frames)
        return audio_path, None
    except Exception as exc:
        return audio_path, f"{type(exc).__name__}: {exc}"


def default_workers() -> int:
    return max(1, min((os.cpu_count() or 2) - 1, 8))
