from __future__ import annotations

import hashlib
import csv
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np


SPLIT_NAMES = ("train", "validation", "test")


def track_identity(record: dict[str, Any], index: int) -> str:
    track_id = record.get("track_id")
    if track_id is not None and str(track_id).strip():
        return str(track_id).strip()
    audio_path = record.get("audio_path")
    if audio_path is not None and str(audio_path).strip():
        return Path(str(audio_path)).expanduser().as_posix()
    return f"row:{index}"


def _group_identity(record: dict[str, Any], track_id: str, group_column: str | None) -> str:
    if group_column:
        value = record.get(group_column)
        normalized = str(value).strip() if value is not None else ""
        if normalized.lower() not in {"", "nan", "none", "unknown", "unknown artist"}:
            return f"{group_column}:{normalized.casefold()}"
    return f"track:{track_id}"


def _fingerprint(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(
        sorted((row["track_id"], row["label"], row["group"]) for row in rows),
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _assign_groups(rows: list[dict[str, str]], validation_size: float, test_size: float, seed: int) -> dict[str, str]:
    fractions = np.array([1.0 - validation_size - test_size, validation_size, test_size], dtype=float)
    labels = sorted({row["label"] for row in rows})
    label_index = {label: index for index, label in enumerate(labels)}
    groups: dict[str, np.ndarray] = {}
    group_sizes: dict[str, int] = {}
    for row in rows:
        groups.setdefault(row["group"], np.zeros(len(labels), dtype=float))[label_index[row["label"]]] += 1.0
        group_sizes[row["group"]] = group_sizes.get(row["group"], 0) + 1

    totals = np.sum(list(groups.values()), axis=0)
    target_labels = fractions[:, None] * totals[None, :]
    target_sizes = fractions * len(rows)
    split_labels = np.zeros_like(target_labels)
    split_sizes = np.zeros(3, dtype=float)

    def stable_order(group: str) -> tuple[int, str]:
        digest = hashlib.sha256(f"{seed}:{group}".encode("utf-8")).hexdigest()
        return -group_sizes[group], digest

    assignments: dict[str, str] = {}
    for group in sorted(groups, key=stable_order):
        group_labels = groups[group]
        size = group_sizes[group]
        scores: list[float] = []
        for split_index in range(3):
            candidate_labels = split_labels.copy()
            candidate_sizes = split_sizes.copy()
            candidate_labels[split_index] += group_labels
            candidate_sizes[split_index] += size
            label_error = np.square((candidate_labels - target_labels) / np.maximum(target_labels, 1.0)).sum()
            size_error = np.square((candidate_sizes - target_sizes) / np.maximum(target_sizes, 1.0)).sum()
            overflow = np.maximum(candidate_sizes - target_sizes, 0.0) / np.maximum(target_sizes, 1.0)
            scores.append(float(label_error + 0.25 * size_error + 2.0 * overflow.sum()))
        selected = min(range(3), key=lambda index: (scores[index], index))
        split_labels[selected] += group_labels
        split_sizes[selected] += size
        assignments[group] = SPLIT_NAMES[selected]
    return assignments


def load_or_create_splits(
    records: Sequence[dict[str, Any]],
    labels: Sequence[str],
    split_path: str | Path,
    *,
    validation_size: float,
    test_size: float,
    seed: int,
    group_column: str | None = "artist",
    regenerate: bool = False,
) -> np.ndarray:
    if len(records) != len(labels):
        raise ValueError("records and labels must have the same length")
    if not 0.0 < validation_size < 1.0 or not 0.0 < test_size < 1.0 or validation_size + test_size >= 1.0:
        raise ValueError("validation_size and test_size must be positive and sum to less than 1")

    rows: list[dict[str, str]] = []
    for index, (record, label) in enumerate(zip(records, labels)):
        identity = track_identity(record, index)
        rows.append(
            {
                "track_id": identity,
                "label": str(label),
                "group": _group_identity(record, identity, group_column),
            }
        )
    identities = [row["track_id"] for row in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("Split identities are not unique; provide unique track_id values")

    path = Path(split_path).expanduser().resolve()
    metadata_path = path.with_suffix(path.suffix + ".metadata.json")
    expected = {
        "version": 1,
        "seed": int(seed),
        "validation_size": float(validation_size),
        "test_size": float(test_size),
        "group_column": group_column,
        "dataset_fingerprint": _fingerprint(rows),
    }

    if path.exists() and not regenerate:
        if not metadata_path.exists():
            raise ValueError(f"Split metadata is missing: {metadata_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata != expected:
            raise ValueError("Existing split configuration or dataset differs; use --regenerate-splits")
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if set(reader.fieldnames or []) != {"track_id", "label", "group", "split"}:
                raise ValueError(f"Invalid split assignment columns in {path}")
            saved = list(reader)
        split_by_id = {row["track_id"]: row["split"] for row in saved}
        if len(saved) != len(split_by_id) or set(split_by_id) != set(identities) or set(split_by_id.values()) != set(SPLIT_NAMES):
            raise ValueError(f"Invalid split assignments in {path}")
        result = np.array([split_by_id[identity] for identity in identities], dtype=object)
    else:
        assignments = _assign_groups(rows, validation_size, test_size, seed)
        for row in rows:
            row["split"] = assignments[row["group"]]
        result = np.array([row["split"] for row in rows], dtype=object)
        if set(result) != set(SPLIT_NAMES):
            raise ValueError("Dataset is too small or too heavily grouped to create three non-empty splits")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["track_id", "label", "group", "split"])
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda row: row["track_id"]))
        metadata_path.write_text(json.dumps(expected, indent=2, sort_keys=True), encoding="utf-8")

    group_splits: dict[str, set[str]] = {}
    for row, split in zip(rows, result):
        group_splits.setdefault(row["group"], set()).add(str(split))
    if any(len(values) != 1 for values in group_splits.values()):
        raise ValueError("A group occurs in multiple persisted splits")
    return result
