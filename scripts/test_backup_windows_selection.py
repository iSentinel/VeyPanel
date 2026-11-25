"""Verify private archive backups without mutating a source installation."""

from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import collect
from backup_windows_selection import RECEIPT, backup, verify_backup
from test_windows_package_selection import fixture
from windows_package_selection import STATE, select


class BackupTests(unittest.TestCase):
    """Exercise reviewed copy, refusal and independent readback."""

    def setUp(self) -> None:
        """Create a private inert installation with two trusted archives."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "install"
        self.root.mkdir()
        self.target = base / "backup"
        first, first_sha = fixture(base, "a", b"first")
        second, second_sha = fixture(base, "b", b"second")
        self.archives = {first_sha: first, second_sha: second}
        select(self.root, first, first_sha, True)
        select(self.root, second, second_sha, True)

    def create(self) -> dict:
        """Create an explicitly plan-bound inert backup."""
        planned = backup(self.root, self.archives, self.target)
        return backup(self.root, self.archives, self.target, True, planned["plan_sha256"])

    def test_verified_copy(self) -> None:
        """Preserve source inventory and exact metadata and archive bytes."""
        before = collect(self.root)
        planned = backup(self.root, self.archives, self.target)
        self.assertFalse(self.target.exists())
        result = self.create()
        self.assertEqual(planned["plan_sha256"], result["plan_sha256"])
        self.assertEqual(verify_backup(self.target, result["plan_sha256"]), result)
        self.assertEqual(collect(self.root), before)
        self.assertEqual((self.target / STATE).read_bytes(), (self.root / STATE).read_bytes())
        for key, source in self.archives.items():
            self.assertEqual((self.target / (key + ".zip")).read_bytes(), source.read_bytes())

    def test_wrong_plan(self) -> None:
        """Reject an unreviewed or changed plan before any copy."""
        with self.assertRaisesRegex(ValueError, "plan changed"):
            backup(self.root, self.archives, self.target, True, "0" * 64)
        self.assertFalse(self.target.exists())

    def test_inside_root(self) -> None:
        """Refuse to create a backup within the source installation."""
        with self.assertRaisesRegex(ValueError, "outside"):
            backup(self.root, self.archives, self.root / "backup")

    def test_existing_destination(self) -> None:
        """Never overwrite an existing destination or partial backup."""
        self.target.mkdir()
        marker = self.target / "private.txt"
        marker.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "already exists"):
            backup(self.root, self.archives, self.target)
        self.assertEqual(marker.read_bytes(), b"preserve")

    def test_tampered_archive(self) -> None:
        """Independent verification rejects a modified backup archive."""
        result = self.create()
        (self.target / (next(iter(self.archives)) + ".zip")).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_backup(self.target, result["plan_sha256"])

    def test_tampered_binding(self) -> None:
        """A copied plan digest alone cannot hide rewritten metadata."""
        result = self.create()
        state = self.target / STATE
        state.write_bytes(state.read_bytes() + b"\n")
        receipt_path = self.target / RECEIPT
        receipt = json.loads(receipt_path.read_text())
        import hashlib
        receipt["selection_sha256"] = hashlib.sha256(state.read_bytes()).hexdigest()
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            verify_backup(self.target, result["plan_sha256"])

    def test_partial_copy(self) -> None:
        """Keep partial evidence without publishing a completion receipt."""
        planned = backup(self.root, self.archives, self.target)
        before = collect(self.root)
        with patch("backup_windows_selection.copy_archive", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                backup(self.root, self.archives, self.target, True, planned["plan_sha256"])
        self.assertTrue(self.target.is_dir())
        self.assertFalse((self.target / RECEIPT).exists())
        self.assertEqual(collect(self.root), before)
        with self.assertRaises(OSError):
            verify_backup(self.target, planned["plan_sha256"])


if __name__ == "__main__":
    unittest.main()
