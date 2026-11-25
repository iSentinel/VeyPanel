"""Test isolated restore without activating or replacing an installation."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import collect
from backup_windows_selection import backup
from restore_windows_selection import restore
from test_windows_package_selection import fixture
from windows_package_selection import STATE, select


class RestoreTests(unittest.TestCase):
    """Exercise exact restore and fail-closed destination handling."""

    def setUp(self) -> None:
        """Create a private two-version backup of inert package fixtures."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "install"
        self.root.mkdir()
        self.backup = base / "backup"
        self.target = base / "restored"
        first, first_sha = fixture(base, "a", b"first")
        second, second_sha = fixture(base, "b", b"second")
        archives = {first_sha: first, second_sha: second}
        select(self.root, first, first_sha, True)
        select(self.root, second, second_sha, True)
        planned = backup(self.root, archives, self.backup)
        self.sha = planned["plan_sha256"]
        backup(self.root, archives, self.backup, True, self.sha)

    def planned(self) -> dict:
        """Return the read-only restore plan."""
        return restore(self.backup, self.sha, self.target)

    def test_restore(self) -> None:
        """Reconstruct both versions and exact metadata without activation."""
        before = collect(self.root)
        copy_before = collect(self.backup)
        planned = self.planned()
        self.assertFalse(self.target.exists())
        result = restore(self.backup, self.sha, self.target, True, planned["plan_sha256"])
        self.assertTrue(result["restored"])
        self.assertFalse(result["started"])
        self.assertFalse(result["maintenance_admitted"])
        self.assertEqual(collect(self.target), before)
        self.assertEqual(collect(self.root), before)
        self.assertEqual(collect(self.backup), copy_before)

    def test_existing_destination(self) -> None:
        """Never overwrite even an empty existing target."""
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.planned()

    def test_wrong_backup_plan(self) -> None:
        """Reject backup without the independently retained plan digest."""
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            restore(self.backup, "0" * 64, self.target)
        self.assertFalse(self.target.exists())

    def test_wrong_restore_plan(self) -> None:
        """Refuse apply with a stale or different destination binding."""
        with self.assertRaisesRegex(ValueError, "Restore plan changed"):
            restore(self.backup, self.sha, self.target, True, "0" * 64)
        self.assertFalse(self.target.exists())

    def test_inside_backup(self) -> None:
        """Do not stage inside the source backup."""
        with self.assertRaisesRegex(ValueError, "outside"):
            restore(self.backup, self.sha, self.backup / "restored")

    def test_partial_restore(self) -> None:
        """Do not publish selected metadata after a staged extraction failure."""
        planned = self.planned()
        with patch("restore_windows_selection.stage", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                restore(self.backup, self.sha, self.target, True, planned["plan_sha256"])
        self.assertTrue(self.target.is_dir())
        self.assertFalse((self.target / STATE).exists())

    def test_changed_backup(self) -> None:
        """Refuse changed archive before creating any target."""
        planned = self.planned()
        next(self.backup.glob("*.zip")).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            restore(self.backup, self.sha, self.target, True, planned["plan_sha256"])
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
