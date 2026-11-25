"""Exercise explicit corrupt metadata repair on isolated inert installations."""

from pathlib import Path
from contextlib import redirect_stderr
from io import StringIO
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import collect
from inspect_package_recovery import inspect
from recover_corrupt_selection import BACKUP, main, repair
from test_windows_package_selection import fixture
from windows_package_selection import LOCK, MAX_STATE, STATE, select, status, version_path


class CorruptRecoveryTests(unittest.TestCase):
    """Verify backup preservation and fail-closed reconciliation."""

    def setUp(self) -> None:
        """Create an isolated package and replace its metadata with a corrupt fixture."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "install"
        self.root.mkdir()
        self.package, self.digest = fixture(base, "a", b"inert fixture")
        select(self.root, self.package, self.digest, True)
        self.path = self.root / STATE
        self.original = b'{"invalid":'
        self.path.write_bytes(self.original)
        self.backup = self.root / BACKUP
        self.version = version_path(self.root, self.digest)

    def test_plan_and_apply(self) -> None:
        """Preserve original bytes and payload inventory, then verify state."""
        before = collect(self.version)
        planned = repair(self.root, self.package, self.digest)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(self.backup.exists())
        actual = repair(self.root, self.package, self.digest, True, planned["plan_sha256"])
        self.assertEqual(actual["selection"], status(self.root))
        self.assertEqual(self.backup.read_bytes(), self.original)
        self.assertEqual(collect(self.version), before)
        self.assertFalse(actual["started"])
        self.assertTrue(inspect(self.root)["manual_review_required"])

    def test_changed_corruption(self) -> None:
        """Reject a plan after the corrupt bytes change."""
        planned = repair(self.root, self.package, self.digest)
        self.path.write_bytes(b"other invalid state")
        with self.assertRaisesRegex(ValueError, "plan changed"):
            repair(self.root, self.package, self.digest, True, planned["plan_sha256"])
        self.assertFalse(self.backup.exists())

    def test_existing_backup(self) -> None:
        """Do not overwrite any previous recovery backup."""
        self.backup.write_bytes(b"previous backup")
        with self.assertRaisesRegex(ValueError, "Unexpected root"):
            repair(self.root, self.package, self.digest)
        self.assertEqual(self.backup.read_bytes(), b"previous backup")

    def test_valid_state_refused(self) -> None:
        """Reject syntactically and structurally valid metadata."""
        self.path.unlink()
        from windows_package_selection import write_state
        from artifact_manifest import MANIFEST, hash_file
        write_state(self.root, {"schema": 1, "active": {
            "package_sha256": self.digest,
            "manifest_sha256": hash_file(self.version / MANIFEST)}, "previous": None})
        with self.assertRaisesRegex(ValueError, "valid metadata"):
            repair(self.root, self.package, self.digest)

    def test_oversized(self) -> None:
        """Do not treat an oversized metadata read as repairable corruption."""
        self.path.write_bytes(b"x" * (MAX_STATE + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            repair(self.root, self.package, self.digest)

    def test_replace_failure(self) -> None:
        """Retain the original and backup if atomic state replacement fails."""
        planned = repair(self.root, self.package, self.digest)
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                repair(self.root, self.package, self.digest, True, planned["plan_sha256"])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), self.original)
        self.assertFalse((self.root / LOCK).exists())

    def test_backup_failure(self) -> None:
        """Never replace state after a backup failure."""
        planned = repair(self.root, self.package, self.digest)
        with patch("recover_corrupt_selection.preserve", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                repair(self.root, self.package, self.digest, True, planned["plan_sha256"])
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_existing_lock(self) -> None:
        """Never clear an interrupted operation's lock."""
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            repair(self.root, self.package, self.digest)
        self.assertTrue((self.root / LOCK).is_dir())

    def test_multiple_versions(self) -> None:
        """Do not infer which of several retained versions should be selected."""
        (self.version.parent / ("1" * 64)).mkdir()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            repair(self.root, self.package, self.digest)

    def test_tampered_payload(self) -> None:
        """Refuse a corrupt state with a modified staged executable."""
        (self.version / "VeyPanel.Desktop.exe").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "files differ"):
            repair(self.root, self.package, self.digest)
        self.assertFalse(self.backup.exists())

    def test_wrong_plan(self) -> None:
        """A wrong plan must not create a backup or replace state."""
        with self.assertRaisesRegex(ValueError, "plan changed"):
            repair(self.root, self.package, self.digest, True, "0" * 64)
        self.assertFalse(self.backup.exists())
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_safe_cli_error(self) -> None:
        """Do not export arbitrary corruption or exception text."""
        sink = StringIO()
        args = ["repair", "--root", "unused", "--package", "unused", "--sha256", "0" * 64]
        with patch("sys.argv", args), patch("recover_corrupt_selection.repair",
                                           side_effect=OSError("secret-canary")):
            with redirect_stderr(sink):
                self.assertEqual(main(), 1)
        self.assertIn("FILESYSTEM_ERROR", sink.getvalue())
        self.assertNotIn("secret-canary", sink.getvalue())


if __name__ == "__main__":
    unittest.main()
