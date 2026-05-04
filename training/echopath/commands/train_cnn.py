from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


def _arg(args: Any, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.exists():
        return path
    return path.resolve()


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
    balance_classes: bool,
    max_per_class: int | None,
) -> list[dict[str, Any]]:
    usable = [track for track in tracks if _valid_track(track, label_column)]
    counts = Counter(str(track[label_column]) for track in usable)

    keep = {label for label, count in counts.items() if count >= min_per_class}
    usable = [track for track in usable if str(track[label_column]) in keep]

    if top_classes and top_classes > 0:
        top = {label for label, _ in Counter(str(track[label_column]) for track in usable).most_common(top_classes)}
        usable = [track for track in usable if str(track[label_column]) in top]

    if balance_classes:
        rng = np.random.default_rng(42)
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


def _mel_tensor(
    audio_path: str,
    sample_rate: int,
    audio_duration: float,
    n_mels: int,
    frames: int,
) -> torch.Tensor:
    y, sr = librosa.load(
        audio_path,
        sr=sample_rate,
        mono=True,
        duration=audio_duration,
    )

    if y is None or len(y) == 0:
        raise ValueError(f"Empty audio: {audio_path}")

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=2048,
        hop_length=512,
        n_mels=n_mels,
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)

    if mel_db.shape[1] < frames:
        pad_width = frames - mel_db.shape[1]
        mel_db = np.pad(mel_db, ((0, 0), (0, pad_width)), mode="constant")
    else:
        mel_db = mel_db[:, :frames]

    mean = float(mel_db.mean())
    std = float(mel_db.std()) or 1.0
    mel_db = (mel_db - mean) / std

    return torch.tensor(mel_db, dtype=torch.float32).unsqueeze(0)


class SpectrogramDataset(Dataset):
    def __init__(
        self,
        tracks: list[dict[str, Any]],
        labels: np.ndarray,
        sample_rate: int,
        audio_duration: float,
        n_mels: int,
        frames: int,
    ) -> None:
        self.tracks = tracks
        self.labels = labels
        self.sample_rate = sample_rate
        self.audio_duration = audio_duration
        self.n_mels = n_mels
        self.frames = frames

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        track = self.tracks[index]
        x = _mel_tensor(
            str(track["audio_path"]),
            sample_rate=self.sample_rate,
            audio_duration=self.audio_duration,
            n_mels=self.n_mels,
            frames=self.frames,
        )
        y = torch.tensor(int(self.labels[index]), dtype=torch.long)
        return x, y


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
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    model.eval()
    losses: list[float] = []
    predictions: list[int] = []
    labels: list[int] = []

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            logits = model(x)
            loss = criterion(logits, y)
            losses.append(float(loss.item()))
            predictions.extend(torch.argmax(logits, dim=1).cpu().numpy().tolist())
            labels.extend(y.cpu().numpy().tolist())

    avg_loss = float(np.mean(losses)) if losses else 0.0
    accuracy = accuracy_score(labels, predictions) if labels else 0.0
    macro_f1 = f1_score(labels, predictions, average="macro", zero_division=0) if labels else 0.0
    return avg_loss, accuracy, macro_f1, np.array(labels), np.array(predictions)


def _train_one_architecture(
    architecture: str,
    train_tracks: list[dict[str, Any]],
    test_tracks: list[dict[str, Any]],
    y_train: np.ndarray,
    y_test: np.ndarray,
    class_names: list[str],
    args: Any,
    output_dir: Path,
    device: torch.device,
) -> dict[str, Any]:
    n_mels = int(_arg(args, "n_mels", 64))
    frames = int(_arg(args, "frames", 128))
    sample_rate = int(_arg(args, "sample_rate", 22_050))
    audio_duration = float(_arg(args, "audio_duration", 30.0))
    batch_size = int(_arg(args, "batch_size", 16))
    epochs = int(_arg(args, "epochs", 20))
    learning_rate = float(_arg(args, "learning_rate", 1e-3))

    train_dataset = SpectrogramDataset(train_tracks, y_train, sample_rate, audio_duration, n_mels, frames)
    test_dataset = SpectrogramDataset(test_tracks, y_test, sample_rate, audio_duration, n_mels, frames)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    model = _build_model(architecture, len(class_names), n_mels, frames).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    best_macro_f1 = -1.0
    best_state = None
    history: list[dict[str, float]] = []

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses: list[float] = []

        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            train_losses.append(float(loss.item()))

        test_loss, accuracy, macro_f1, _, _ = _evaluate(model, test_loader, criterion, device)
        train_loss = float(np.mean(train_losses)) if train_losses else 0.0

        history.append(
            {
                "epoch": float(epoch),
                "train_loss": train_loss,
                "test_loss": test_loss,
                "accuracy": accuracy,
                "macro_f1": macro_f1,
            }
        )

        print(
            f"[{architecture}] epoch={epoch} "
            f"train_loss={train_loss:.4f} test_loss={test_loss:.4f} "
            f"acc={accuracy:.4f} macro_f1={macro_f1:.4f}"
        )

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    final_loss, final_accuracy, final_macro_f1, true_labels, predicted_labels = _evaluate(
        model,
        test_loader,
        criterion,
        device,
    )
    weighted_f1 = f1_score(true_labels, predicted_labels, average="weighted", zero_division=0)

    arch_dir = output_dir / architecture
    arch_dir.mkdir(parents=True, exist_ok=True)

    report = classification_report(
        true_labels,
        predicted_labels,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
    )
    (arch_dir / "classification_report.txt").write_text(report, encoding="utf-8")

    with (arch_dir / "history.csv").open("w", encoding="utf-8") as f:
        f.write("epoch,train_loss,test_loss,accuracy,macro_f1\n")
        for row in history:
            f.write(
                f"{int(row['epoch'])},{row['train_loss']:.6f},"
                f"{row['test_loss']:.6f},{row['accuracy']:.6f},{row['macro_f1']:.6f}\n"
            )

    torch.save(
        {
            "architecture": architecture,
            "state_dict": model.state_dict(),
            "class_names": class_names,
            "n_mels": n_mels,
            "frames": frames,
            "sample_rate": sample_rate,
            "audio_duration": audio_duration,
            "accuracy": final_accuracy,
            "macro_f1": final_macro_f1,
            "weighted_f1": weighted_f1,
        },
        arch_dir / "model.pt",
    )

    print(f"\n{architecture} classification report")
    print(report)

    return {
        "architecture": architecture,
        "accuracy": final_accuracy,
        "macro_f1": final_macro_f1,
        "weighted_f1": weighted_f1,
        "test_loss": final_loss,
    }


def run_train_cnn(args) -> None:
    manifest_path = Path(_arg(args, "manifest", "data/library/tracks.json")).expanduser()
    tracks = json.loads(manifest_path.read_text(encoding="utf-8"))

    label_column = _arg(args, "label_column", "genre_label")
    tracks = _filter_tracks(
        tracks=tracks,
        label_column=label_column,
        min_per_class=int(_arg(args, "min_per_class", 5)),
        top_classes=_arg(args, "top_classes", None),
        balance_classes=bool(_arg(args, "balance_classes", False)),
        max_per_class=_arg(args, "max_per_class", None),
    )

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

    train_indices, test_indices = train_test_split(
        np.arange(len(tracks)),
        test_size=float(_arg(args, "test_size", 0.2)),
        random_state=42,
        stratify=labels,
    )

    train_tracks = [tracks[int(index)] for index in train_indices]
    test_tracks = [tracks[int(index)] for index in test_indices]
    y_train = labels[train_indices]
    y_test = labels[test_indices]

    requested_architecture = _arg(args, "architecture", "lenet")
    if requested_architecture == "all":
        architectures = ["lenet", "vgg", "resnet"]
    else:
        architectures = [requested_architecture]

    output_dir = Path(_arg(args, "output_dir", "artifacts/models/cnn")).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

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
            test_tracks=test_tracks,
            y_train=y_train,
            y_test=y_test,
            class_names=class_names,
            args=args,
            output_dir=output_dir,
            device=device,
        )
        rows.append(row)

    summary_path = output_dir / "cnn_architecture_comparison.csv"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("architecture,accuracy,macro_f1,weighted_f1,test_loss\n")
        for row in sorted(rows, key=lambda item: item["macro_f1"], reverse=True):
            f.write(
                f"{row['architecture']},{row['accuracy']:.6f},{row['macro_f1']:.6f},"
                f"{row['weighted_f1']:.6f},{row['test_loss']:.6f}\n"
            )

    best = max(rows, key=lambda item: item["macro_f1"])

    print("\nCNN architecture comparison complete")
    print("architecture accuracy macro_f1 weighted_f1 test_loss")
    for row in sorted(rows, key=lambda item: item["macro_f1"], reverse=True):
        print(
            f"{row['architecture']:>12} "
            f"{row['accuracy']:.4f} "
            f"{row['macro_f1']:.4f} "
            f"{row['weighted_f1']:.4f} "
            f"{row['test_loss']:.4f}"
        )
    print(f"Best architecture: {best['architecture']}")
    print(f"Artifacts: {output_dir}")
