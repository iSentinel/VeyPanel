"""Exercise CI evidence admission and sealing without network requests."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_upstream_watch as watch
import run_upstream_watch_ci as ci


class WatchCiTests(unittest.TestCase):
    """Preserve complete review outcomes and reject failed evidence gates."""

    def setUp(self) -> None:
        """Use a private fixture and inject actual normalized observations."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "archive"
        self.commit, self.tree = "a" * 40, "b" * 40
        self.source = {"git_commit": self.commit, "git_tree": self.tree}
        self.document = json.loads(watch.BASELINE.read_bytes())
        for module in (watch, ci):
            patcher = patch.object(module, "evidence", return_value=self.source)
            patcher.start()
            self.addCleanup(patcher.stop)

    def execute(self, complete: bool = True) -> str:
        """Run the real offline bundle and seal path using synthetic rows."""
        with patch.object(watch, "collect", return_value=(self.document, complete)):
            return ci.execute(self.output, self.commit, self.tree)

    def verify(self) -> str:
        """Independently reopen and verify the sealed archive."""
        return ci.verify_sealed(self.output, self.commit, self.tree)

    def test_unchanged(self) -> None:
        """Seal exactly four complete bundle files and verify readback."""
        self.assertEqual(self.execute(), "UNCHANGED")
        self.assertEqual(self.verify(), "UNCHANGED")
        manifest = ci.load_manifest(self.output / ci.MANIFEST)
        self.assertEqual(len(manifest["files"]), 4)

    def test_review(self) -> None:
        """Changed upstream data is review evidence, never a silent unchanged."""
        self.document["repositories"]["ClassicOldSong/Apollo"]["head"] = "c" * 40
        self.assertEqual(self.execute(), "REVIEW")
        self.assertEqual(self.verify(), "REVIEW")

    def test_incomplete_no_seal(self) -> None:
        """Incomplete evidence is retained locally but never receives a seal."""
        del self.document["repositories"]["ClassicOldSong/Apollo"]
        with self.assertRaises(ValueError):
            self.execute(False)
        self.assertFalse((self.output / ci.MANIFEST).exists())
        self.assertTrue((self.output / "bundle" / "receipt.json").exists())
        with self.assertRaises(ValueError):
            self.verify()

    def test_source_preflight(self) -> None:
        """Refuse an unexpected tree before creating a directory or collecting."""
        with patch.object(ci, "run") as run:
            with self.assertRaises(ValueError):
                ci.execute(self.output, self.commit, "c" * 40)
            run.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_status_disagreement(self) -> None:
        """Refuse disagreement between collection and independent verification."""
        with patch.object(ci, "verify_bundle", return_value="REVIEW"):
            with self.assertRaises(ValueError):
                self.execute()
        self.assertFalse((self.output / ci.MANIFEST).exists())

    def test_tamper_and_extra(self) -> None:
        """Reject modified bytes and unexpected archive root entries."""
        self.execute()
        target = self.output / "bundle" / "observed.json"
        original = target.read_bytes()
        target.write_bytes(original + b"\n")
        with self.assertRaises(ValueError):
            self.verify()
        target.write_bytes(original)
        (self.output / "extra").touch()
        with self.assertRaises(ValueError):
            self.verify()

    def test_resealed_forgery(self) -> None:
        """A recomputed file manifest cannot bypass receipt and report validation."""
        self.execute()
        target = self.output / "bundle" / "observed.json"
        target.write_bytes(target.read_bytes() + b"\n")
        ci.write_manifest(self.output, ci.collect(self.output))
        with self.assertRaises(ValueError):
            self.verify()

    def test_cli_exit_mapping(self) -> None:
        """Preserve distinct status exits and redact unexpected error values."""
        args = ["ci", "collect", "--output", str(self.output),
                "--expected-commit", self.commit, "--expected-tree", self.tree]
        with patch.object(ci.sys, "argv", args):
            for status, code in (("UNCHANGED", 0), ("REVIEW", 2)):
                with patch.object(ci, "execute", return_value=status), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ci.main(), code)
            with patch.object(ci, "execute", side_effect=ValueError("private canary")), contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(ci.main(), 1)
                self.assertNotIn("private canary", stderr.getvalue())
