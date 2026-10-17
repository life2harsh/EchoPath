from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import json
import os
import platform
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from ..mel import CACHE_SCHEMA, cache_path, default_workers, frames_for_duration, load_or_compute, warm_cache_entry
from ..splits import load_or_create_splits, track_identity

def _arg(args: Any, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _frames(args: Any) -> int:
    configured = _arg(args, "frames", None)
    if configured:
        return int(configured)
    return frames_for_duration(float(_arg(args, "audio_duration", 30.0)), int(_arg(args, "sample_rate", 22_050)))


def _set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)


def _atomic_torch_save(payload: Any, path: Path) -> None:
    temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def _valid_track(track: dict[str, Any], label_column: str) -> bool:
    label = track.get(label_column)
    audio_path = track.get("audio_path")
    if label is None or str(label).strip().lower() in {"", "nan", "none", "unknown"}:
        return False
    if not audio_path:
        return False
    return Path(audio_path).expanduser().exists()


def _filter_tracks(
    tracks: list[dict[str, Any]],
    label_column: str,
    min_per_class: int,
    top_classes: int | None,
    classes: list[str] | None,
    balance_classes: bool,
    max_per_class: int | None,
    seed: int = 42,
) -> list[dict[str, Any]]:
    usable = [track for track in tracks if _valid_track(track, label_column)]
    counts = Counter(str(track[label_column]) for track in usable)

    keep = {label for label, count in counts.items() if count >= min_per_class}
    usable = [track for track in usable if str(track[label_column]) in keep]

    if classes:
        allowed = {str(label) for label in classes}
        usable = [track for track in usable if str(track[label_column]) in allowed]

    if top_classes and top_classes > 0:
        top = {label for label, _ in Counter(str(track[label_column]) for track in usable).most_common(top_classes)}
        usable = [track for track in usable if str(track[label_column]) in top]

    if balance_classes:
        rng = np.random.default_rng(seed)
        groups: dict[str, list[dict[str, Any]]] = {}
        for track in usable:
            groups.setdefault(str(track[label_column]), []).append(track)

        if not groups:
            return []

        target_count = min(len(group) for group in groups.values())
        if max_per_class:
            target_count = min(target_count, max_per_class)

        balanced: list[dict[str, Any]] = []
        for group in groups.values():
            indices = rng.choice(len(group), size=target_count, replace=False)
            balanced.extend(group[int(index)] for index in indices)

        rng.shuffle(balanced)
        usable = balanced

    return usable


def _training_indices(
    labels: np.ndarray,
    indices: np.ndarray,
    balance: bool,
    max_per_class: int | None,
    seed: int,
) -> np.ndarray:
    if not balance:
        return indices
    target_count = min(int(np.sum(labels[indices] == label)) for label in np.unique(labels[indices]))
    if max_per_class:
        target_count = min(target_count, int(max_per_class))
    rng = np.random.default_rng(seed)
    selected = [
        int(index)
        for label in np.unique(labels[indices])
        for index in rng.choice(indices[labels[indices] == label], size=target_count, replace=False)
    ]
    return np.array(sorted(selected), dtype=int)


class SpectrogramDataset(Dataset):
    def __init__(
        self,
        tracks: list[dict[str, Any]],
        labels: np.ndarray,
        sample_rate: int,
        audio_duration: float,
        n_mels: int,
        frames: int,
        cache_dir: Path,
    ) -> None:
        self.tracks = tracks
        self.labels = labels
        self.sample_rate = sample_rate
        self.audio_duration = audio_duration
        self.n_mels = n_mels
        self.frames = frames
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        track = self.tracks[index]
        audio_path = Path(str(track["audio_path"])).expanduser().resolve()
        array = load_or_compute(self.cache_dir, audio_path, self.sample_rate, self.audio_duration, self.n_mels, self.frames)
        x = torch.from_numpy(array)
        y = torch.tensor(int(self.labels[index]), dtype=torch.long)
        return x, y


def _warm_mel_cache(
    tracks: list[dict[str, Any]],
    cache_dir: Path,
    sample_rate: int,
    audio_duration: float,
    n_mels: int,
    frames: int,
    workers: int,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for track in tracks:
        audio_path = Path(str(track["audio_path"])).expanduser().resolve()
        if not cache_path(cache_dir, audio_path, sample_rate, audio_duration, n_mels, frames).exists():
            jobs.append((str(audio_path), str(cache_dir), sample_rate, audio_duration, n_mels, frames))
    print(f"Mel cache: {len(tracks) - len(jobs)} cached, {len(jobs)} to compute with {workers} worker(s)")
    if not jobs:
        return

    failures: list[str] = []
    executor = ProcessPoolExecutor(max_workers=workers) if workers > 1 else None
    results = executor.map(warm_cache_entry, jobs, chunksize=8) if executor else map(warm_cache_entry, jobs)
    try:
        for done, (audio_path, error) in enumerate(results, start=1):
            if error:
                failures.append(f"{audio_path}: {error}")
            if done % 250 == 0 or done == len(jobs):
                print(f"Mel cache: {done}/{len(jobs)} computed")
    finally:
        if executor is not None:
            executor.shutdown()
    if failures:
        raise SystemExit("Could not compute spectrograms for these files:\n" + "\n".join(failures[:20]))


class LeNetSpectrogramCNN(nn.Module):
    def __init__(self, num_classes: int, n_mels: int, frames: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=5, padding=2),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=5, padding=2),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, 1, n_mels, frames)
            flattened = int(np.prod(self.features(dummy).shape[1:]))

        self.classifier = nn.Sequential(
            nn.Linear(flattened, 128),
            nn.ReLU(),
            nn.Dropout(0.35),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


class VGGStyleSpectrogramCNN(nn.Module):
    def __init__(self, num_classes: int, n_mels: int, frames: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            self._block(1, 32),
            self._block(32, 64),
            self._block(64, 128),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, 1, n_mels, frames)
            flattened = int(np.prod(self.features(dummy).shape[1:]))

        self.classifier = nn.Sequential(
            nn.Linear(flattened, 256),
            nn.ReLU(),
            nn.Dropout(0.45),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.35),
            nn.Linear(128, num_classes),
        )

    @staticmethod
    def _block(in_channels: int, out_channels: int) -> nn.Sequential:
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


class ResidualBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1) -> None:
        super().__init__()
        self.main = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, stride=stride, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        )

        if in_channels != out_channels or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

        self.activation = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.activation(self.main(x) + self.shortcut(x))


class ResNetStyleSpectrogramCNN(nn.Module):
    def __init__(self, num_classes: int, n_mels: int, frames: int) -> None:
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, padding=2, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(),
        )
        self.features = nn.Sequential(
            ResidualBlock(32, 32),
            ResidualBlock(32, 64, stride=2),
            ResidualBlock(64, 64),
            ResidualBlock(64, 128, stride=2),
            ResidualBlock(128, 128),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.35),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.features(x)
        return self.classifier(x)


def _build_model(name: str, num_classes: int, n_mels: int, frames: int) -> nn.Module:
    if name == "lenet":
        return LeNetSpectrogramCNN(num_classes, n_mels, frames)
    if name == "vgg":
        return VGGStyleSpectrogramCNN(num_classes, n_mels, frames)
    if name == "resnet":
        return ResNetStyleSpectrogramCNN(num_classes, n_mels, frames)
    raise ValueError(f"Unknown CNN architecture: {name}")


def _evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    amp_enabled: bool,
) -> tuple[float, float, float, np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    losses: list[float] = []
    predictions: list[int] = []
    labels: list[int] = []
    confidences: list[float] = []

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            with torch.amp.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                logits = model(x)
                loss = criterion(logits, y)
            probabilities = torch.softmax(logits.float(), dim=1)
            losses.append(float(loss.item()))
            confidence, prediction = torch.max(probabilities, dim=1)
            predictions.extend(prediction.cpu().numpy().tolist())
            confidences.extend(confidence.cpu().numpy().tolist())
            labels.extend(y.cpu().numpy().tolist())

    avg_loss = float(np.mean(losses)) if losses else 0.0
    accuracy = accuracy_score(labels, predictions) if labels else 0.0
    macro_f1 = f1_score(labels, predictions, average="macro", zero_division=0) if labels else 0.0
    return avg_loss, accuracy, macro_f1, np.array(labels), np.array(predictions), np.array(confidences)


def _train_one_architecture(
    architecture: str,
    train_tracks: list[dict[str, Any]],
    validation_tracks: list[dict[str, Any]],
    y_train: np.ndarray,
    y_validation: np.ndarray,
    class_names: list[str],
    args: Any,
    output_dir: Path,
    device: torch.device,
) -> dict[str, Any]:
    n_mels = int(_arg(args, "n_mels", 64))
    frames = _frames(args)
    sample_rate = int(_arg(args, "sample_rate", 22_050))
    audio_duration = float(_arg(args, "audio_duration", 30.0))
    batch_size = int(_arg(args, "batch_size", 16))
    epochs = int(_arg(args, "epochs", 20))
    learning_rate = float(_arg(args, "learning_rate", 1e-3))
    seed = int(_arg(args, "seed", 42))
    num_workers = int(_arg(args, "num_workers", 0))
    amp_enabled = bool(_arg(args, "mixed_precision", False)) and device.type == "cuda"
    cache_dir = Path(_arg(args, "cache_dir", None) or output_dir / "mel_cache").expanduser().resolve()

    train_dataset = SpectrogramDataset(train_tracks, y_train, sample_rate, audio_duration, n_mels, frames, cache_dir)
    validation_dataset = SpectrogramDataset(
        validation_tracks, y_validation, sample_rate, audio_duration, n_mels, frames, cache_dir
    )

    generator = torch.Generator().manual_seed(seed)
    loader_options = {
        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": num_workers > 0,
    }
    train_loader = DataLoader(train_dataset, shuffle=True, generator=generator, **loader_options)
    validation_loader = DataLoader(validation_dataset, shuffle=False, **loader_options)

    model = _build_model(architecture, len(class_names), n_mels, frames).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)

    best_macro_f1 = -1.0
    best_state = None
    history: list[dict[str, float]] = []
    start_epoch = 1
    best_epoch = 0
    arch_dir = output_dir / architecture
    arch_dir.mkdir(parents=True, exist_ok=True)
    resume_path = arch_dir / "last_checkpoint.pt"
    run_signature = {
        "architecture": architecture,
        "class_names": class_names,
        "n_mels": n_mels,
        "frames": frames,
        "sample_rate": sample_rate,
        "audio_duration": audio_duration,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "epochs": epochs,
        "mixed_precision": amp_enabled,
        "train_track_ids": [track_identity(track, index) for index, track in enumerate(train_tracks)],
        "validation_track_ids": [track_identity(track, index) for index, track in enumerate(validation_tracks)],
        "train_labels": y_train.tolist(),
        "validation_labels": y_validation.tolist(),
        "seed": seed,
        "cache_schema": CACHE_SCHEMA,
    }
    if bool(_arg(args, "resume", False)) and resume_path.exists():
        try:
            checkpoint = torch.load(resume_path, map_location=device, weights_only=False)
        except Exception as exc:
            print(f"Ignoring unreadable resume checkpoint {resume_path}: {exc}")
            checkpoint = {}
        if checkpoint.get("run_signature") == run_signature:
            model.load_state_dict(checkpoint["state_dict"])
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            scaler.load_state_dict(checkpoint["scaler_state_dict"])
            generator.set_state(checkpoint["generator_state"].cpu())
            torch.set_rng_state(checkpoint["torch_rng_state"].cpu())
            if torch.cuda.is_available() and checkpoint["cuda_rng_state_all"]:
                torch.cuda.set_rng_state_all([state.cpu() for state in checkpoint["cuda_rng_state_all"]])
            np.random.set_state(checkpoint["numpy_rng_state"])
            random.setstate(checkpoint["python_rng_state"])
            best_state = checkpoint["best_state_dict"]
            best_macro_f1 = float(checkpoint["best_validation_macro_f1"])
            best_epoch = int(checkpoint["best_epoch"])
            history = checkpoint["history"]
            start_epoch = int(checkpoint["epoch"]) + 1
        else:
            print(f"Ignoring incompatible resume checkpoint: {resume_path}")

    for epoch in range(start_epoch, epochs + 1):
        model.train()
        train_losses: list[float] = []

        for x, y in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                logits = model(x)
                loss = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_losses.append(float(loss.item()))

        validation_loss, accuracy, macro_f1, _, _, _ = _evaluate(
            model, validation_loader, criterion, device, amp_enabled
        )
        train_loss = float(np.mean(train_losses)) if train_losses else 0.0

        history.append(
            {
                "epoch": float(epoch),
                "train_loss": train_loss,
                "validation_loss": validation_loss,
                "validation_accuracy": accuracy,
                "validation_macro_f1": macro_f1,
            }
        )

        print(
            f"[{architecture}] epoch={epoch} "
            f"train_loss={train_loss:.4f} validation_loss={validation_loss:.4f} "
            f"validation_acc={accuracy:.4f} validation_macro_f1={macro_f1:.4f}"
        )

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_epoch = epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            _atomic_torch_save(
                {
                    "run_signature": run_signature,
                    "epoch": epoch,
                    "state_dict": best_state,
                    "validation_macro_f1": best_macro_f1,
                },
                arch_dir / "best_checkpoint.pt",
            )

        _atomic_torch_save(
            {
                "run_signature": run_signature,
                "epoch": epoch,
                "state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scaler_state_dict": scaler.state_dict(),
                "best_state_dict": best_state,
                "best_validation_macro_f1": best_macro_f1,
                "best_epoch": best_epoch,
                "history": history,
                "generator_state": generator.get_state(),
                "torch_rng_state": torch.get_rng_state(),
                "cuda_rng_state_all": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
                "numpy_rng_state": np.random.get_state(),
                "python_rng_state": random.getstate(),
            },
            resume_path,
        )

    if best_state is not None:
        model.load_state_dict(best_state)
    else:
        raise RuntimeError(f"No checkpoint available for {architecture}")

    validation_loss, validation_accuracy, validation_macro_f1, true_labels, predicted_labels, confidence = _evaluate(
        model, validation_loader, criterion, device, amp_enabled
    )

    report = classification_report(
        true_labels,
        predicted_labels,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
    )
    (arch_dir / "validation_classification_report.txt").write_text(report, encoding="utf-8")
    pd.DataFrame(history).to_csv(arch_dir / "history.csv", index=False)
    pd.DataFrame(
        {
            "track_id": [track_identity(track, index) for index, track in enumerate(validation_tracks)],
            "split": "validation",
            "true_label": np.asarray(class_names)[true_labels],
            "prediction": np.asarray(class_names)[predicted_labels],
            "confidence": confidence,
        }
    ).to_csv(arch_dir / "validation_predictions.csv", index=False)

    _atomic_torch_save(
        {
            "architecture": architecture,
            "state_dict": model.state_dict(),
            "class_names": class_names,
            "n_mels": n_mels,
            "frames": frames,
            "sample_rate": sample_rate,
            "audio_duration": audio_duration,
            "best_epoch": best_epoch,
            "validation_accuracy": validation_accuracy,
            "validation_macro_f1": validation_macro_f1,
        },
        arch_dir / "model.pt",
    )

    return {
        "architecture": architecture,
        "validation_accuracy": validation_accuracy,
        "validation_macro_f1": validation_macro_f1,
        "validation_loss": validation_loss,
        "best_epoch": best_epoch,
        "amp_enabled": amp_enabled,
    }


def run_train_cnn(args) -> None:
    formal_evaluation = bool(_arg(args, "formal_evaluation", False))
    requested_classes = _arg(args, "classes", None)
    if formal_evaluation and not requested_classes:
        raise SystemExit("Formal evaluation requires an explicit --classes cohort.")
    manifest_path = Path(_arg(args, "manifest", None) or "data/library/tracks.json").expanduser().resolve()
    tracks = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_root_value = _arg(args, "dataset_root", None)
    dataset_root = Path(dataset_root_value).expanduser().resolve() if dataset_root_value else manifest_path.parent
    for track in tracks:
        audio_path = Path(str(track.get("audio_path", ""))).expanduser()
        if not audio_path.is_absolute():
            dataset_candidate = dataset_root / audio_path
            manifest_candidate = manifest_path.parent / audio_path
            track["audio_path"] = str(dataset_candidate if dataset_candidate.exists() else manifest_candidate)

    label_column = _arg(args, "label_column", "genre_label")
    seed = int(_arg(args, "seed", 42))
    balance_classes = bool(_arg(args, "balance_classes", False))
    tracks = _filter_tracks(
        tracks=tracks,
        label_column=label_column,
        min_per_class=int(_arg(args, "min_per_class", 5)),
        top_classes=_arg(args, "top_classes", None),
        classes=_arg(args, "classes", None),
        balance_classes=False,
        max_per_class=_arg(args, "max_per_class", None),
        seed=seed,
    )
    if formal_evaluation and {str(track[label_column]) for track in tracks} != {str(label) for label in requested_classes}:
        missing = sorted({str(label) for label in requested_classes} - {str(track[label_column]) for track in tracks})
        raise SystemExit(f"Formal evaluation cohort is incomplete after filtering: {missing}")

    if len(tracks) < 10:
        raise SystemExit("Not enough usable tracks for CNN training.")

    labels_raw = [str(track[label_column]) for track in tracks]
    encoder = LabelEncoder()
    labels = encoder.fit_transform(labels_raw)
    class_names = encoder.classes_.tolist()

    if len(class_names) < 2:
        raise SystemExit("Need at least two classes for CNN training.")

    counts = Counter(labels_raw)
    print("CNN training rows:", len(tracks))
    print("Classes:", len(class_names))
    print("Class distribution:")
    for label, count in counts.most_common():
        print(f"{label}: {count}")
    print("")

    _set_determinism(seed)
    output_dir = Path(_arg(args, "output_dir", "artifacts/models/cnn")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    split_path = Path(_arg(args, "splits", None) or output_dir / "splits.csv")
    splits = load_or_create_splits(
        tracks,
        labels_raw,
        split_path,
        validation_size=float(_arg(args, "validation_size", 0.15)),
        test_size=float(_arg(args, "test_size", 0.15)),
        seed=seed,
        group_column=_arg(args, "group_column", "artist"),
        regenerate=bool(_arg(args, "regenerate_splits", False)),
    )
    all_train_indices = np.flatnonzero(splits == "train")
    train_indices = _training_indices(
        labels,
        all_train_indices,
        balance_classes,
        _arg(args, "max_per_class", None),
        seed,
    )
    validation_indices = np.flatnonzero(splits == "validation")
    test_indices = np.flatnonzero(splits == "test")
    train_tracks = [tracks[int(index)] for index in train_indices]
    all_train_tracks = [tracks[int(index)] for index in all_train_indices]
    validation_tracks = [tracks[int(index)] for index in validation_indices]
    test_tracks = [tracks[int(index)] for index in test_indices]
    y_train = labels[train_indices]
    all_y_train = labels[all_train_indices]
    y_validation = labels[validation_indices]
    y_test = labels[test_indices]
    if set(np.unique(y_train)) != set(np.unique(labels)):
        raise SystemExit("Training split must contain every class; adjust split sizes or grouping.")

    requested_architecture = _arg(args, "architecture", "lenet")
    if requested_architecture == "all":
        architectures = ["lenet", "vgg", "resnet"]
    else:
        architectures = [requested_architecture]

    _warm_mel_cache(
        tracks,
        Path(_arg(args, "cache_dir", None) or output_dir / "mel_cache").expanduser().resolve(),
        int(_arg(args, "sample_rate", 22_050)),
        float(_arg(args, "audio_duration", 30.0)),
        int(_arg(args, "n_mels", 64)),
        _frames(args),
        int(_arg(args, "preprocess_workers", 0) or default_workers()),
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print("")

    rows = []
    for architecture in architectures:
        print(f"Training architecture: {architecture}")
        row = _train_one_architecture(
            architecture=architecture,
            train_tracks=train_tracks,
            validation_tracks=validation_tracks,
            y_train=y_train,
            y_validation=y_validation,
            class_names=class_names,
            args=args,
            output_dir=output_dir,
            device=device,
        )
        rows.append(row)
        if device.type == "cuda":
            torch.cuda.empty_cache()

    best = max(rows, key=lambda item: item["validation_macro_f1"])
    n_mels = int(_arg(args, "n_mels", 64))
    frames = _frames(args)
    model = _build_model(best["architecture"], len(class_names), n_mels, frames).to(device)
    selected_checkpoint = torch.load(
        output_dir / best["architecture"] / "model.pt", map_location=device, weights_only=False
    )
    model.load_state_dict(selected_checkpoint["state_dict"])
    sample_rate = int(_arg(args, "sample_rate", 22_050))
    audio_duration = float(_arg(args, "audio_duration", 30.0))
    batch_size = int(_arg(args, "batch_size", 16))
    num_workers = int(_arg(args, "num_workers", 0))
    cache_dir = Path(_arg(args, "cache_dir", None) or output_dir / "mel_cache").expanduser().resolve()
    loader_options = {
        "batch_size": batch_size,
        "shuffle": False,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": num_workers > 0,
    }
    criterion = nn.CrossEntropyLoss()

    def prediction_rows(split_name: str, split_tracks: list[dict[str, Any]], split_labels: np.ndarray):
        dataset = SpectrogramDataset(
            split_tracks, split_labels, sample_rate, audio_duration, n_mels, frames, cache_dir
        )
        loader = DataLoader(dataset, **loader_options)
        result = _evaluate(model, loader, criterion, device, bool(best["amp_enabled"]))
        _, _, _, true_values, predicted_values, confidence_values = result
        prediction_frame = pd.DataFrame(
            {
                "track_id": [track_identity(track, index) for index, track in enumerate(split_tracks)],
                "split": split_name,
                "true_label": np.asarray(class_names)[true_values],
                "prediction": np.asarray(class_names)[predicted_values],
                "confidence": confidence_values,
                "architecture": best["architecture"],
            }
        )
        return result, prediction_frame

    _, train_prediction_frame = prediction_rows("train", all_train_tracks, all_y_train)
    _, validation_prediction_frame = prediction_rows("validation", validation_tracks, y_validation)
    test_result, test_prediction_frame = prediction_rows("test", test_tracks, y_test)
    test_loss, test_accuracy, test_macro_f1, true_labels, predicted_labels, _ = test_result
    test_weighted_f1 = f1_score(true_labels, predicted_labels, average="weighted", zero_division=0)
    test_balanced_accuracy = balanced_accuracy_score(true_labels, predicted_labels)
    predictions = pd.concat(
        [train_prediction_frame, validation_prediction_frame, test_prediction_frame], ignore_index=True
    )
    predictions.to_csv(output_dir / "cnn_predictions.csv", index=False)
    test_prediction_frame.to_csv(output_dir / "test_predictions.csv", index=False)

    test_metrics = {
        "architecture": best["architecture"],
        "best_epoch": int(best["best_epoch"]),
        "selected_validation_macro_f1": float(best["validation_macro_f1"]),
        "test_loss": float(test_loss),
        "accuracy": float(test_accuracy),
        "balanced_accuracy": float(test_balanced_accuracy),
        "macro_f1": float(test_macro_f1),
        "weighted_f1": float(test_weighted_f1),
        "test_rows": int(len(test_tracks)),
    }
    (output_dir / "final_test_metrics.json").write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
    report = classification_report(
        true_labels,
        predicted_labels,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
    )
    (output_dir / "final_test_classification_report.txt").write_text(report, encoding="utf-8")
    pd.DataFrame(
        confusion_matrix(true_labels, predicted_labels, labels=list(range(len(class_names)))),
        index=class_names,
        columns=class_names,
    ).to_csv(output_dir / "final_test_confusion_matrix.csv", index_label="true_label")

    comparison = pd.DataFrame(
        [{key: value for key, value in row.items() if key != "amp_enabled"} for row in rows]
    ).sort_values("validation_macro_f1", ascending=False)
    comparison.to_csv(output_dir / "cnn_architecture_comparison.csv", index=False)
    config_metadata = {
        "command": "train-cnn",
        "manifest": os.path.relpath(manifest_path, output_dir),
        "label_column": label_column,
        "architectures": architectures,
        "selected_architecture": best["architecture"],
        "formal_evaluation": formal_evaluation,
        "seed": seed,
        "validation_size": float(_arg(args, "validation_size", 0.15)),
        "test_size": float(_arg(args, "test_size", 0.15)),
        "group_column": _arg(args, "group_column", "artist"),
        "split_path": os.path.relpath(split_path.expanduser().resolve(), output_dir),
        "cache_dir": os.path.relpath(cache_dir, output_dir),
        "cache_schema": CACHE_SCHEMA,
        "epochs": int(_arg(args, "epochs", 20)),
        "batch_size": batch_size,
        "learning_rate": float(_arg(args, "learning_rate", 1e-3)),
        "sample_rate": sample_rate,
        "audio_duration": audio_duration,
        "n_mels": n_mels,
        "frames": frames,
        "mixed_precision_requested": bool(_arg(args, "mixed_precision", False)),
        "mixed_precision_enabled": bool(best["amp_enabled"]),
        "resume": bool(_arg(args, "resume", False)),
        "num_workers": num_workers,
        "min_per_class": int(_arg(args, "min_per_class", 5)),
        "top_classes": _arg(args, "top_classes", None),
        "classes": _arg(args, "classes", None),
        "balance_classes": balance_classes,
        "max_per_class": _arg(args, "max_per_class", None),
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "rows": {name: int((splits == name).sum()) for name in ("train", "validation", "test")},
        "training_rows_after_balance": int(len(train_indices)),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "torch_version": torch.__version__,
        "platform": sys.platform,
    }
    (output_dir / "training_config.json").write_text(json.dumps(config_metadata, indent=2), encoding="utf-8")

    print("\nCNN architecture comparison complete")
    print("architecture validation_accuracy validation_macro_f1 validation_loss best_epoch")
    for row in sorted(rows, key=lambda item: item["validation_macro_f1"], reverse=True):
        print(
            f"{row['architecture']:>12} "
            f"{row['validation_accuracy']:.4f} "
            f"{row['validation_macro_f1']:.4f} "
            f"{row['validation_loss']:.4f} "
            f"{row['best_epoch']}"
        )
    print(f"Best architecture: {best['architecture']} (validation selection)")
    print(f"Final test macro F1: {test_macro_f1:.4f}")
    print(f"Artifacts: {output_dir}")
