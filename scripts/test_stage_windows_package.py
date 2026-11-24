"""Isolated staging fixtures; no real executable is launched."""

import json
from pathlib import Path
import tempfile
import unittest

from artifact_manifest import MANIFEST, collect, hash_file
from portable_zip import write_zip
from stage_windows_package import stage


def manifest(root):
    """Write the fixture manifest."""
    (root / MANIFEST).write_text(json.dumps(collect(root)), encoding="utf-8")


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.host = self.source / "host"
        self.host.mkdir(parents=True)
        for directory, name in ((self.source, "VeyPanel.Desktop"),
                                (self.host, "VeyPanel.Host")):
            for ext in (".exe", ".dll"):
                (directory / (name + ext)).write_bytes(b"fixture")
            (directory / "build-source.json").write_text(json.dumps({
                "schema": 1, "tracked_checkout_clean": True,
                "git_commit": "a" * 40, "git_tree": "b" * 40,
                "source_commit_epoch_utc": 1700000000}), encoding="utf-8")
        self.package = self.root / "package.zip"
        self.dest = self.root / "stage"
        self.pack()

    def pack(self):
        """Build a new consistent package."""
        self.package.unlink(missing_ok=True)
        manifest(self.host)
        manifest(self.source)
        write_zip(self.source, self.package)
        self.sha = hash_file(self.package)

    def test_dry_run(self):
        self.assertEqual(stage(self.package, self.sha, self.dest), 7)
        self.assertFalse(self.dest.exists())

    def test_apply(self):
        stage(self.package, self.sha, self.dest, False)
        self.assertEqual(collect(self.source), collect(self.dest))

    def test_wrong_digest(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            stage(self.package, "0" * 64, self.dest, False)
        self.assertFalse(self.dest.exists())

    def test_existing(self):
        self.dest.mkdir()
        sentinel = self.dest / "keep"
        sentinel.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage(self.package, self.sha, self.dest, False)
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_missing_parent(self):
        with self.assertRaisesRegex(ValueError, "ancestor"):
            stage(self.package, self.sha, self.dest / "child", False)

    def test_mixed_sources(self):
        (self.host / "build-source.json").write_text('{"other":true}')
        self.pack()
        with self.assertRaisesRegex(ValueError, "source evidence differs"):
            stage(self.package, self.sha, self.dest, False)

    def test_invalid_source_evidence(self):
        for directory in (self.source, self.host):
            (directory / "build-source.json").write_text("{}")
        self.pack()
        with self.assertRaisesRegex(ValueError, "Invalid package source"):
            stage(self.package, self.sha, self.dest, False)

    def test_destination_traversal(self):
        with self.assertRaisesRegex(ValueError, "parent traversal"):
            stage(self.package, self.sha, self.root / ".." / "target", False)

    def test_wrong_nested_manifest(self):
        (self.host / "VeyPanel.Host.dll").write_bytes(b"modified")
        manifest(self.source)
        self.package.unlink()
        write_zip(self.source, self.package)
        with self.assertRaisesRegex(ValueError, "Nested Host manifest mismatch"):
            stage(self.package, hash_file(self.package), self.dest, False)


if __name__ == "__main__":
    unittest.main()
