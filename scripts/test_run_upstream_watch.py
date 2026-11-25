"""Offline source-bound watch bundle tests; never contact GitHub."""

import contextlib
from datetime import timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_upstream_watch as watch


class WatchTests(unittest.TestCase):
    """Verify collection and readback without actual network or Git mutation."""

    def setUp(self) -> None:
        """Create a private fixture root and trusted source identity."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "bundle"
        self.source = {"git_commit": "a" * 40, "git_tree": "b" * 40}
        self.observation = json.loads(watch.BASELINE.read_bytes())
        self.mock_source = patch.object(watch, "evidence", return_value=self.source)
        self.source_fn = self.mock_source.start()
        self.addCleanup(self.mock_source.stop)

    def collect(self, complete: bool = True) -> str:
        """Inject normalized fixture data without network access."""
        with patch.object(watch, "collect", return_value=(self.observation, complete)):
            return watch.run(self.output, self.source["git_commit"])

    def verify(self) -> str:
        """Verify the bundle using the same trusted identity and current clock."""
        return watch.verify_bundle(self.output, self.source["git_commit"],
                                   self.source["git_tree"], watch.utc_now())

    def test_round_trip(self) -> None:
        """Create and verify all four exact bundle files."""
        self.assertEqual(self.collect(), "UNCHANGED")
        self.assertEqual(self.verify(), "UNCHANGED")
        self.assertEqual(self.source_fn.call_count, 3)

    def test_review(self) -> None:
        """Preserve review-required result for complete changed metadata."""
        self.observation["repositories"]["ClassicOldSong/Apollo"]["head"] = "f" * 40
        self.assertEqual(self.collect(), "REVIEW")
        self.assertEqual(self.verify(), "REVIEW")

    def test_incomplete(self) -> None:
        """Preserve incomplete evidence but reject successful verification."""
        del self.observation["repositories"]["ClassicOldSong/Apollo"]
        self.assertEqual(self.collect(False), "ERROR")
        with self.assertRaises(ValueError):
            self.verify()

    def test_source_change(self) -> None:
        """Refuse publication if source identity changed during collection."""
        self.source_fn.side_effect = [self.source, {**self.source, "git_tree": "c" * 40}]
        with self.assertRaises(ValueError):
            self.collect()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_existing_directory(self) -> None:
        """Never overwrite or merge with an earlier evidence directory."""
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.collect()

    def test_baseline_and_report_tamper(self) -> None:
        """Refuse even a whitespace-only baseline change or false report."""
        self.collect()
        baseline = self.output / "baseline.json"
        original = baseline.read_bytes()
        baseline.write_bytes(original + b"\n")
        with self.assertRaises(ValueError):
            self.verify()
        baseline.write_bytes(original)
        (self.output / "report.json").write_text("{}")
        with self.assertRaises(ValueError):
            self.verify()

    def test_extra_file_and_stale(self) -> None:
        """Reject unexpected artifacts and elapsed observation validity."""
        self.collect()
        extra = self.output / "extra.json"
        extra.touch()
        with self.assertRaises(ValueError):
            self.verify()
        extra.unlink()
        with self.assertRaises(ValueError):
            watch.verify_bundle(self.output, self.source["git_commit"],
                                self.source["git_tree"], watch.utc_now() + timedelta(days=2))

    def test_cli_error_redaction(self) -> None:
        """Emit only a fixed error message rather than an exception value."""
        args = ["watch", "collect", "--output", str(self.output), "--expected-commit", "a" * 40]
        with patch.object(watch.sys, "argv", args), patch.object(watch, "run", side_effect=ValueError("private canary")):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(watch.main(), 1)
            self.assertNotIn("private canary", stderr.getvalue())
