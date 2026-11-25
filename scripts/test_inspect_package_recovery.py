"""Exercise read-only interrupted-selection diagnostics."""

from pathlib import Path
from contextlib import redirect_stderr
from io import StringIO
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from inspect_package_recovery import inspect, main
from test_windows_package_selection import fixture
from windows_package_selection import LOCK, STATE, select, version_path


class RecoveryTests(unittest.TestCase):
    """Inspect isolated package state without changing any existing file."""
    def setUp(self) -> None:
        """Create two inert packages and an empty private selection root."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "install"
        self.root.mkdir()
        self.a = fixture(base, "a", b"first")
        self.b = fixture(base, "b", b"second")

    def test_empty(self) -> None:
        """An empty root is a healthy uninitialized snapshot."""
        report = inspect(self.root)
        self.assertFalse(report["manual_review_required"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_healthy(self) -> None:
        """Verify a successfully selected package."""
        select(self.root, *self.a, True)
        report = inspect(self.root)
        self.assertFalse(report["manual_review_required"])
        self.assertEqual(report["active"]["status"], "verified")

    def test_lock_and_temporary_preserved(self) -> None:
        """Report and preserve interrupted-operation markers."""
        select(self.root, *self.a, True)
        (self.root / LOCK).mkdir()
        leftover = self.root / ".selection-interrupted"
        leftover.write_bytes(b"partial")
        before = (self.root / STATE).read_bytes()
        report = inspect(self.root)
        self.assertTrue(report["manual_review_required"])
        self.assertTrue(report["lock_present"])
        self.assertEqual(report["temporary_state_count"], 1)
        self.assertEqual(leftover.read_bytes(), b"partial")
        self.assertEqual((self.root / STATE).read_bytes(), before)
        self.assertTrue((self.root / LOCK).is_dir())

    def test_orphan_after_failed_commit(self) -> None:
        """Report an unreferenced staged version after write failure."""
        select(self.root, *self.a, True)
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, *self.b, True)
        report = inspect(self.root)
        self.assertTrue(report["manual_review_required"])
        self.assertIn({"status": "unreferenced", "package_sha256": self.b[1]},
                      report["versions"])

    def test_first_commit_interrupted(self) -> None:
        """Report incomplete initial selection without adopting it."""
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, *self.a, True)
        report = inspect(self.root)
        self.assertEqual(report["state_status"], "absent")
        self.assertTrue(report["manual_review_required"])
        self.assertTrue(version_path(self.root, self.a[1]).exists())

    def test_damaged_active(self) -> None:
        """Distinguish a damaged active tree from a verified previous tree."""
        select(self.root, *self.a, True)
        select(self.root, *self.b, True)
        (version_path(self.root, self.b[1]) / "VeyPanel.Desktop.dll").write_bytes(b"bad")
        report = inspect(self.root)
        self.assertEqual(report["active"]["status"], "invalid")
        self.assertEqual(report["previous"]["status"], "verified")
        self.assertTrue(report["manual_review_required"])

    def test_corrupt_state(self) -> None:
        """Report malformed state without modifying it."""
        (self.root / STATE).write_bytes(b"broken")
        report = inspect(self.root)
        self.assertEqual(report["state_status"], "invalid")
        self.assertTrue(report["manual_review_required"])

    def test_cli_review_exit(self) -> None:
        """Return review exit status without deleting the lock."""
        (self.root / LOCK).mkdir()
        script = Path(__file__).with_name("inspect_package_recovery.py")
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no changes made", result.stdout)
        self.assertTrue((self.root / LOCK).is_dir())

    def test_unexpected_version_entry(self) -> None:
        """Report unexpected inventory entries without deleting them."""
        versions = self.root / "versions"
        versions.mkdir()
        (versions / "not-a-package").write_bytes(b"preserve")
        report = inspect(self.root)
        self.assertTrue(report["manual_review_required"])
        self.assertEqual(report["versions"], [{"status": "unexpected-name"}])
        self.assertEqual((versions / "not-a-package").read_bytes(), b"preserve")

    def test_version_budget(self) -> None:
        """Reject an inventory above the inspection budget."""
        (self.root / "versions").mkdir()
        for name in ("one", "two"):
            (self.root / "versions" / name).mkdir()
        with patch("inspect_package_recovery.MAX_ITEMS", 1):
            with self.assertRaisesRegex(ValueError, "budget"):
                inspect(self.root)

    def test_safe_cli_error(self) -> None:
        """Keep arbitrary exception text and private paths out of diagnostics."""
        output = StringIO()
        with patch("sys.argv", ["inspect", "--root", "unused"]), patch(
                "inspect_package_recovery.inspect", side_effect=OSError("secret-canary")):
            with redirect_stderr(output):
                self.assertEqual(main(), 1)
        self.assertIn("FILESYSTEM_ERROR", output.getvalue())
        self.assertNotIn("secret-canary", output.getvalue())


if __name__ == "__main__":
    unittest.main()
