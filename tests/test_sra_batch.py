import tempfile
import unittest
from pathlib import Path

from nexumics.sra_batch import append_manifest_event, iter_batch_windows, load_completed_retstarts


class SraBatchTests(unittest.TestCase):
    def test_iter_batch_windows_splits_target_records(self) -> None:
        windows = iter_batch_windows(total_records=450, batch_size=200)

        self.assertEqual(windows, [(0, 200), (200, 200), (400, 50)])

    def test_iter_batch_windows_handles_empty_targets(self) -> None:
        self.assertEqual(iter_batch_windows(total_records=0, batch_size=200), [])

    def test_load_completed_retstarts_only_reads_success_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.jsonl"
            append_manifest_event(manifest_path, {"status": "success", "retstart": 0})
            append_manifest_event(manifest_path, {"status": "failure", "retstart": 200})
            append_manifest_event(manifest_path, {"status": "success", "retstart": 400})

            completed = load_completed_retstarts(manifest_path)

            self.assertEqual(completed, {0, 400})
