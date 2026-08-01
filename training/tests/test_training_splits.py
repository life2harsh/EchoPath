from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np

from echopath.splits import load_or_create_splits


class TrainingSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = []
        self.labels = []
        for label in ("ambient", "rock", "jazz"):
            for index in range(24):
                self.records.append(
                    {
                        "track_id": f"{label}-{index:02d}",
                        "artist": f"{label}-artist-{index // 2:02d}",
                    }
                )
                self.labels.append(label)

    def test_split_is_persisted_reusable_and_artist_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "splits.csv"
            first = load_or_create_splits(
                self.records,
                self.labels,
                path,
                validation_size=0.2,
                test_size=0.2,
                seed=17,
            )
            order = np.arange(len(self.records))[::-1]
            reordered_records = [self.records[int(index)] for index in order]
            reordered_labels = [self.labels[int(index)] for index in order]
            second = load_or_create_splits(
                reordered_records,
                reordered_labels,
                path,
                validation_size=0.2,
                test_size=0.2,
                seed=17,
            )

            self.assertEqual(set(first), {"train", "validation", "test"})
            by_id = {record["track_id"]: split for record, split in zip(self.records, first)}
            self.assertEqual(second.tolist(), [by_id[record["track_id"]] for record in reordered_records])
            artist_splits: dict[str, set[str]] = {}
            for record, split in zip(self.records, first):
                artist_splits.setdefault(record["artist"], set()).add(str(split))
            self.assertTrue(all(len(splits) == 1 for splits in artist_splits.values()))
            self.assertTrue(path.with_suffix(".csv.metadata.json").exists())

    def test_changed_dataset_requires_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "splits.csv"
            load_or_create_splits(
                self.records,
                self.labels,
                path,
                validation_size=0.2,
                test_size=0.2,
                seed=42,
            )
            changed_labels = list(self.labels)
            changed_labels[0] = "changed"
            with self.assertRaisesRegex(ValueError, "regenerate-splits"):
                load_or_create_splits(
                    self.records,
                    changed_labels,
                    path,
                    validation_size=0.2,
                    test_size=0.2,
                    seed=42,
                )

    def test_unknown_artists_are_independent_groups(self) -> None:
        records = [{"track_id": f"track-{index}", "artist": "Unknown Artist"} for index in range(30)]
        labels = ["a" if index % 2 else "b" for index in range(30)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "splits.csv"
            splits = load_or_create_splits(
                records,
                labels,
                path,
                validation_size=0.2,
                test_size=0.2,
                seed=42,
            )
            self.assertEqual(set(splits), {"train", "validation", "test"})
            with path.open("r", encoding="utf-8", newline="") as handle:
                groups = [row["group"] for row in csv.DictReader(handle)]
            self.assertEqual(len(set(groups)), len(records))


if __name__ == "__main__":
    unittest.main()
