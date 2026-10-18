from __future__ import annotations

import os
import unittest
from unittest import mock

from echopath.commands import ingest


def _fake_extract(job: tuple[str, float]) -> tuple[str, dict[str, float] | None, str | None]:
    audio_path, _ = job
    if "bad" in audio_path:
        os._exit(1)
    return audio_path, {"energy": 0.5}, None


class IngestCrashTests(unittest.TestCase):
    def test_crashing_file_is_skipped_and_rest_complete(self) -> None:
        jobs = [(f"good_{index}.mp3", 30.0) for index in range(12)]
        jobs.insert(5, ("bad_one.mp3", 30.0))
        with mock.patch.object(ingest, "_extract_one", _fake_extract):
            results = list(ingest._extract_all(jobs, workers=4))

        succeeded = sorted(path for path, features, _ in results if features is not None)
        failed = [path for path, features, _ in results if features is None]
        self.assertEqual(succeeded, sorted(path for path, _ in jobs if "good" in path))
        self.assertEqual(failed, ["bad_one.mp3"])

    def test_first_file_runs_alone_before_parallel_pool(self) -> None:
        pool_sizes: list[int] = []
        real_executor = ingest.ProcessPoolExecutor

        def recording_executor(max_workers: int):
            pool_sizes.append(max_workers)
            return real_executor(max_workers=max_workers)

        jobs = [(f"good_{index}.mp3", 30.0) for index in range(6)]
        with mock.patch.object(ingest, "_extract_one", _fake_extract), mock.patch.object(ingest, "ProcessPoolExecutor", recording_executor):
            results = list(ingest._extract_all(jobs, workers=4))

        self.assertEqual(pool_sizes, [1, 4])
        self.assertEqual(results[0][0], "good_0.mp3")
        self.assertEqual(len(results), 6)

    def test_gives_up_when_every_file_crashes(self) -> None:
        jobs = [(f"bad_{index}.mp3", 30.0) for index in range(8)]
        with mock.patch.object(ingest, "_extract_one", _fake_extract):
            with self.assertRaises(SystemExit):
                list(ingest._extract_all(jobs, workers=2, max_consecutive_crashes=3))


if __name__ == "__main__":
    unittest.main()
