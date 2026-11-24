"""Offline artifact manifest membership, mutation and path fixtures."""

import tempfile
import unittest
from pathlib import Path

from artifact_manifest import MANIFEST, collect, compare, safe_entry


class ManifestTests(unittest.TestCase):
    """Test exact membership and fail-closed local tree traversal."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "binary.dll").write_bytes(b"fixture")

    def test_stable(self):
        self.assertEqual(collect(self.root), collect(self.root))

    def test_changed(self):
        before = collect(self.root)
        (self.root / "binary.dll").write_bytes(b"changed")
        self.assertEqual(compare(before, collect(self.root))["changed"], ["binary.dll"])

    def test_added(self):
        before = collect(self.root)
        (self.root / "new.txt").write_text("new")
        self.assertEqual(compare(before, collect(self.root))["added"], ["new.txt"])

    def test_manifest_excluded(self):
        before = collect(self.root)
        (self.root / MANIFEST).write_text("fixture")
        self.assertEqual(before, collect(self.root))

    def test_empty(self):
        (self.root / "binary.dll").unlink()
        with self.assertRaisesRegex(ValueError, "Empty"):
            collect(self.root)

    def test_paths(self):
        for name in ("../bad", "x//y", "x/.", "C:bad", "x\\y", "x/hidden."):
            self.assertFalse(safe_entry(name))
        self.assertTrue(safe_entry("a/binary.dll"))

    def test_symlink(self):
        try:
            (self.root / "link").symlink_to(self.root / "binary.dll")
        except OSError:
            self.skipTest("Symlink fixture unavailable")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            collect(self.root)


if __name__ == "__main__":
    unittest.main()
