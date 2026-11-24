"""Exercise side-by-side selection, rollback and failure boundaries."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import MANIFEST, collect, hash_file
from portable_zip import write_zip
from windows_package_selection import LOCK, STATE, rollback, select, status, version_path


def fixture(root, name, contents):
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

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "install"
        self.root.mkdir()
        self.a = fixture(Path(temp.name), "a", b"version one")
        self.b = fixture(Path(temp.name), "b", b"version two")

    def test_dry_run(self):
        select(self.root, *self.a, False)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_select_and_idempotence(self):
        first = select(self.root, *self.a, True)
        before = (self.root / STATE).read_bytes()
        self.assertEqual(select(self.root, *self.a, True), first)
        self.assertEqual((self.root / STATE).read_bytes(), before)
        self.assertEqual(status(self.root), first)

    def test_update_and_rollback(self):
        first = select(self.root, *self.a, True)
        second = select(self.root, *self.b, True)
        self.assertEqual(second["previous"], first["active"])
        before = (self.root / STATE).read_bytes()
        self.assertEqual(rollback(self.root, False)["active"], first["active"])
        self.assertEqual((self.root / STATE).read_bytes(), before)
        self.assertEqual(rollback(self.root, True)["active"], first["active"])
        self.assertTrue(version_path(self.root, self.b[1]).is_dir())

    def test_no_previous(self):
        select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "No previous"):
            rollback(self.root, True)

    def test_bad_update_digest(self):
        first = select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            select(self.root, self.b[0], "0" * 64, True)
        self.assertEqual(status(self.root), first)

    def test_commit_failure_preserves_old_selection(self):
        first = select(self.root, *self.a, True)
        with patch("windows_package_selection.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                select(self.root, *self.b, True)
        self.assertEqual(status(self.root), first)
        self.assertTrue(version_path(self.root, self.b[1]).is_dir())
        with self.assertRaisesRegex(ValueError, "already exists"):
            select(self.root, *self.b, True)

    def test_tampered_previous_refused(self):
        select(self.root, *self.a, True)
        second = select(self.root, *self.b, True)
        (version_path(self.root, self.a[1]) / "VeyPanel.Desktop.dll").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "files differ"):
            rollback(self.root, True)
        self.assertEqual(status(self.root), second)

    def test_rollback_from_damaged_active(self):
        first = select(self.root, *self.a, True)
        select(self.root, *self.b, True)
        (version_path(self.root, self.b[1]) / "VeyPanel.Desktop.dll").write_bytes(b"bad")
        self.assertEqual(rollback(self.root, True)["active"], first["active"])

    def test_manifest_tampering(self):
        select(self.root, *self.a, True)
        (version_path(self.root, self.a[1]) / MANIFEST).write_text("{}")
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            status(self.root)

    def test_locked(self):
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            select(self.root, *self.a, True)
        with self.assertRaisesRegex(ValueError, "locked"):
            status(self.root)

    def test_invalid_state(self):
        (self.root / STATE).write_text('{"schema":1,"active":"../outside","previous":null}')
        with self.assertRaisesRegex(ValueError, "Invalid selection state"):
            status(self.root)


if __name__ == "__main__":
    unittest.main()
