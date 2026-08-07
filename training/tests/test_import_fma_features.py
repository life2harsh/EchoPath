from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from echopath.commands.import_fma_features import _records


class FmaFeatureImportTests(unittest.TestCase):
    def test_records_merge_metadata_audio_and_official_features(self) -> None:
        columns = pd.MultiIndex.from_tuples(
            [
                ("rhythm", "tempo", ""),
                ("rmse", "mean", ""),
                ("spectral_centroid", "mean", ""),
                ("chroma_stft", "mean", "01"),
                ("chroma_stft", "mean", "02"),
            ]
        )
        features = pd.DataFrame([[120.0, 0.1, 2_000.0, 0.3, 0.5]], index=[2], columns=columns)
        metadata_columns = pd.MultiIndex.from_tuples(
            [
                ("track", "title"),
                ("artist", "name"),
                ("track", "duration"),
                ("track", "genre_top"),
            ]
        )
        metadata = pd.DataFrame(
            [["Example", "Artist", 30, "Rock"], ["Missing", "Artist", 30, "Jazz"]],
            index=[2, 3],
            columns=metadata_columns,
        )

        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "000002.mp3"
            audio_path.touch()
            records, missing = _records(features, metadata, {2: audio_path})

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["track_id"], "000002")
        self.assertEqual(records[0]["genre_label"], "Rock")
        self.assertEqual(records[0]["tempo"], 120.0)
        self.assertIn("fma_rhythm_tempo", records[0])
        self.assertEqual(missing, ["000003: audio file missing"])
