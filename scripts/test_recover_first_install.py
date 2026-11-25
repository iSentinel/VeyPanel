"""Exercise explicit recovery in isolated private roots with inert packages."""

from pathlib import Path
from contextlib import redirect_stderr
from io import StringIO
import tempfile
import unittest
from unittest.mock import patch

from recover_first_install import main, recover
from test_windows_package_selection import fixture
from windows_package_selection import LOCK, STATE, select, status, version_path


class FirstRecoveryTests(unittest.TestCase):
    """Verify plan binding, refusal and atomic metadata-only recovery."""

    def setUp(self) -> None:
        """Create an orphan by injecting a failed first selection write."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.root = base / "install"
        self.root.mkdir()
        self.package, self.sha = fixture(base, "a", b"inert fixture")
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, self.package, self.sha, True)
        self.version = version_path(self.root, self.sha)

    def test_plan_and_apply(self) -> None:
        """Restore only selection metadata; preserve all staged files."""
        before = {p.relative_to(self.version): p.read_bytes()
                  for p in self.version.rglob("*") if p.is_file()}
        planned = recover(self.root, self.package, self.sha)
        self.assertFalse((self.root / STATE).exists())
        self.assertFalse(planned["applied"])
        actual = recover(self.root, self.package, self.sha, True, planned["plan_sha256"])
        self.assertEqual(actual["selection"], status(self.root))
        self.assertTrue(actual["applied"])
        self.assertFalse(actual["started"])
        self.assertEqual(before, {p.relative_to(self.version): p.read_bytes()
                                  for p in self.version.rglob("*") if p.is_file()})
        self.assertFalse((self.root / LOCK).exists())

    def test_wrong_plan(self) -> None:
        """A different plan digest cannot write state."""
        with self.assertRaisesRegex(ValueError, "plan changed"):
            recover(self.root, self.package, self.sha, True, "0" * 64)
        self.assertFalse((self.root / STATE).exists())

    def test_missing_plan(self) -> None:
        """Apply without a previously reviewed plan is refused."""
        with self.assertRaisesRegex(ValueError, "prior plan"):
            recover(self.root, self.package, self.sha, True)
        self.assertFalse((self.root / STATE).exists())

    def test_tampered_payload(self) -> None:
        """A changed staged binary cannot be adopted."""
        planned = recover(self.root, self.package, self.sha)
        (self.version / "VeyPanel.Desktop.exe").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "files differ"):
            recover(self.root, self.package, self.sha, True, planned["plan_sha256"])
        self.assertFalse((self.root / STATE).exists())

    def test_existing_state(self) -> None:
        """Never overwrite even malformed existing selection metadata."""
        (self.root / STATE).write_bytes(b"malformed")
        with self.assertRaisesRegex(ValueError, "Existing selection"):
            recover(self.root, self.package, self.sha)
        self.assertEqual((self.root / STATE).read_bytes(), b"malformed")

    def test_locked(self) -> None:
        """Never remove a preexisting lock."""
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            recover(self.root, self.package, self.sha)
        self.assertTrue((self.root / LOCK).is_dir())

    def test_temporary_state(self) -> None:
        """An interrupted temporary record requires manual inspection."""
        marker = self.root / ".selection-orphan"
        marker.write_bytes(b"partial")
        with self.assertRaisesRegex(ValueError, "Unexpected root"):
            recover(self.root, self.package, self.sha)
        self.assertEqual(marker.read_bytes(), b"partial")

    def test_multiple_versions(self) -> None:
        """Refuse ambiguous retained directories without removing them."""
        other = self.version.parent / ("1" * 64)
        other.mkdir()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            recover(self.root, self.package, self.sha)
        self.assertTrue(other.is_dir())

    def test_wrong_archive(self) -> None:
        """A different external archive is not trusted."""
        other, _ = fixture(self.package.parent, "b", b"other")
        with self.assertRaisesRegex(ValueError, "External SHA-256"):
            recover(self.root, other, self.sha)

    def test_failed_commit(self) -> None:
        """Failed replacement preserves staged files and absent state."""
        planned = recover(self.root, self.package, self.sha)
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                recover(self.root, self.package, self.sha, True, planned["plan_sha256"])
        self.assertFalse((self.root / STATE).exists())
        self.assertTrue(self.version.is_dir())
        self.assertFalse((self.root / LOCK).exists())

    def test_wrong_root(self) -> None:
        """A plan for one private root cannot authorize a second root."""
        other = self.root.parent / "other"
        other.mkdir()
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(other, self.package, self.sha, True)
        planned = recover(self.root, self.package, self.sha)
        with self.assertRaisesRegex(ValueError, "plan changed"):
            recover(other, self.package, self.sha, True, planned["plan_sha256"])
        self.assertFalse((other / STATE).exists())

    def test_safe_cli_error(self) -> None:
        """Do not export arbitrary filesystem error contents."""
        sink = StringIO()
        args = ["recover", "--root", "unused", "--package", "unused", "--sha256", "0" * 64]
        with patch("sys.argv", args), patch("recover_first_install.recover",
                                           side_effect=OSError("secret-canary")):
            with redirect_stderr(sink):
                self.assertEqual(main(), 1)
        self.assertIn("FILESYSTEM_ERROR", sink.getvalue())
        self.assertNotIn("secret-canary", sink.getvalue())


if __name__ == "__main__":
    unittest.main()
