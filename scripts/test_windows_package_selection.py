"""Exercise side-by-side selection, rollback and failure boundaries."""

import json
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import MANIFEST, collect, hash_file
from portable_zip import write_zip
from windows_package_selection import (LOCK, STATE, MAX_STATE, main, rollback,
                                       select, status, version_path, write_state)


def fixture(root: Path, name: str, contents: bytes) -> tuple[Path, str]:
    """Create a complete synthetic Desktop and Host package."""
    source = root / name
    host = source / "host"
    host.mkdir(parents=True)
    for directory, stem in ((source, "VeyPanel.Desktop"), (host, "VeyPanel.Host")):
        for suffix in (".exe", ".dll"):
            (directory / (stem + suffix)).write_bytes(contents)
        (directory / "build-source.json").write_text(json.dumps({
            "schema": 1, "tracked_checkout_clean": True,
            "git_commit": "a" * 40, "git_tree": "b" * 40,
            "source_commit_epoch_utc": 1700000000}), encoding="utf-8")
    for directory in (host, source):
        (directory / MANIFEST).write_text(json.dumps(collect(directory)), encoding="utf-8")
    archive = root / (name + ".zip")
    write_zip(source, archive)
    return archive, hash_file(archive)


class SelectionTests(unittest.TestCase):
    """Operate only on temporary private directories and inert fixture files."""

    def setUp(self) -> None:
        """Prepare two inert side-by-side packages in an isolated root."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "install"
        self.root.mkdir()
        self.a = fixture(Path(temp.name), "a", b"version one")
        self.b = fixture(Path(temp.name), "b", b"version two")

    def test_dry_run(self) -> None:
        """Dry-run leaves the root empty."""
        select(self.root, *self.a, False)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_select_and_idempotence(self) -> None:
        """An identical package preserves selection bytes."""
        first = select(self.root, *self.a, True)
        before = (self.root / STATE).read_bytes()
        self.assertEqual(select(self.root, *self.a, True), first)
        self.assertEqual((self.root / STATE).read_bytes(), before)
        self.assertEqual(status(self.root), first)

    def test_update_and_rollback(self) -> None:
        """Switch and roll back without deleting old versions."""
        first = select(self.root, *self.a, True)
        second = select(self.root, *self.b, True)
        self.assertEqual(second["previous"], first["active"])
        before = (self.root / STATE).read_bytes()
        self.assertEqual(rollback(self.root, False)["active"], first["active"])
        self.assertEqual((self.root / STATE).read_bytes(), before)
        self.assertEqual(rollback(self.root, True)["active"], first["active"])
        self.assertTrue(version_path(self.root, self.b[1]).is_dir())

    def test_no_previous(self) -> None:
        """Refuse rollback without a previous record."""
        select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "No previous"):
            rollback(self.root, True)

    def test_bad_update_digest(self) -> None:
        """A wrong archive digest preserves the active selection."""
        first = select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            select(self.root, self.b[0], "0" * 64, True)
        self.assertEqual(status(self.root), first)

    def test_commit_failure_preserves_old_selection(self) -> None:
        """Preserve the old state and staged orphan on write failure."""
        first = select(self.root, *self.a, True)
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, *self.b, True)
        self.assertEqual(status(self.root), first)
        self.assertTrue(version_path(self.root, self.b[1]).is_dir())
        with self.assertRaisesRegex(ValueError, "already exists"):
            select(self.root, *self.b, True)

    def test_first_commit_failure_requires_inspection(self) -> None:
        """Do not adopt an unreferenced first-stage tree."""
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, *self.a, True)
        self.assertFalse((self.root / STATE).exists())
        with self.assertRaisesRegex(ValueError, "Unreferenced versions"):
            status(self.root)

    def test_idempotent_wrong_archive(self) -> None:
        """Refuse the wrong original archive for an existing selection."""
        first = select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            select(self.root, self.b[0], self.a[1], True)
        self.assertEqual(status(self.root), first)

    def test_tampered_previous_refused(self) -> None:
        """Reject rollback to modified package files."""
        select(self.root, *self.a, True)
        second = select(self.root, *self.b, True)
        (version_path(self.root, self.a[1]) / "VeyPanel.Desktop.dll").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "files differ"):
            rollback(self.root, True)
        self.assertEqual(status(self.root), second)

    def test_rollback_from_damaged_active(self) -> None:
        """Permit rollback to an intact previous package."""
        first = select(self.root, *self.a, True)
        select(self.root, *self.b, True)
        (version_path(self.root, self.b[1]) / "VeyPanel.Desktop.dll").write_bytes(b"bad")
        self.assertEqual(rollback(self.root, True)["active"], first["active"])

    def test_manifest_tampering(self) -> None:
        """Reject a manifest that differs from its stored digest."""
        select(self.root, *self.a, True)
        (version_path(self.root, self.a[1]) / MANIFEST).write_text("{}")
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            status(self.root)

    def test_locked(self) -> None:
        """Refuse an existing cooperating lock."""
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "locked"):
            status(self.root)

    def test_invalid_state(self) -> None:
        """Refuse an invalid selection record."""
        (self.root / STATE).write_text('{"schema":1,"active":"../outside","previous":null}')
        with self.assertRaisesRegex(ValueError, "Invalid selection state"):
            status(self.root)

    def test_duplicate_state_key(self) -> None:
        """Reject a duplicate schema key, even with the same value."""
        select(self.root, *self.a, True)
        path = self.root / STATE
        path.write_bytes(path.read_bytes().replace(b'"schema": 1', b'"schema": 1, "schema": 1'))
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            status(self.root)

    def test_duplicate_record_key(self) -> None:
        """Reject duplicate keys nested inside the active record."""
        select(self.root, *self.a, True)
        path = self.root / STATE
        path.write_bytes(path.read_bytes().replace(
            b'"package_sha256":', b'"package_sha256": null, "package_sha256":'))
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            status(self.root)

    def test_oversized_state(self) -> None:
        """Reject metadata above the bounded read budget."""
        (self.root / STATE).write_bytes(b" " * (MAX_STATE + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            status(self.root)

    def test_duplicate_pinned_manifest(self) -> None:
        """Reject ambiguous manifest JSON even with a matching stored digest."""
        state = select(self.root, *self.a, True)
        path = version_path(self.root, self.a[1]) / MANIFEST
        path.write_bytes(path.read_bytes().replace(b'"schema": 1', b'"schema": 1, "schema": 1'))
        state["active"]["manifest_sha256"] = hash_file(path)
        write_state(self.root, state)
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            status(self.root)

    def test_invalid_write_preserves_state(self) -> None:
        """Invalid state must not replace the previous valid metadata."""
        select(self.root, *self.a, True)
        before = (self.root / STATE).read_bytes()
        with self.assertRaisesRegex(ValueError, "Invalid selection state"):
            write_state(self.root, {"schema": 1, "active": None, "previous": None})
        self.assertEqual((self.root / STATE).read_bytes(), before)

    def test_safe_cli_failure(self) -> None:
        """Do not emit an arbitrary exception message in shared diagnostics."""
        sink = StringIO()
        with patch("sys.argv", ["selection", "--root", "unused", "status"]), patch(
                "windows_package_selection.status", side_effect=OSError("secret-canary")):
            with redirect_stderr(sink):
                self.assertEqual(main(), 1)
        self.assertIn("FILESYSTEM_ERROR", sink.getvalue())
        self.assertNotIn("secret-canary", sink.getvalue())


if __name__ == "__main__":
    unittest.main()
