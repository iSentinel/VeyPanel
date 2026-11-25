"""Offline artifact manifest membership, mutation and path fixtures."""

import os
import stat
from types import SimpleNamespace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_manifest import MANIFEST, collect, compare, hash_file, load_manifest, safe_entry, same_open_file, write_manifest


class ManifestTests(unittest.TestCase):
    """Test exact membership and fail-closed local tree traversal."""

    def setUp(self) -> None:
        """Create a disposable regular artifact directory."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "binary.dll").write_bytes(b"fixture")

    def test_stable(self) -> None:
        """Repeated inventories of a stable tree agree."""
        self.assertEqual(collect(self.root), collect(self.root))

    def test_changed(self) -> None:
        """Detect changed bytes."""
        before = collect(self.root)
        (self.root / "binary.dll").write_bytes(b"changed")
        self.assertEqual(compare(before, collect(self.root))["changed"], ["binary.dll"])

    def test_added(self) -> None:
        """Detect added files."""
        before = collect(self.root)
        (self.root / "new.txt").write_text("new")
        self.assertEqual(compare(before, collect(self.root))["added"], ["new.txt"])

    def test_manifest_excluded(self) -> None:
        """Exclude only the root manifest from its own inventory."""
        before = collect(self.root)
        (self.root / MANIFEST).write_text("fixture")
        self.assertEqual(before, collect(self.root))

    def test_empty(self) -> None:
        """Reject an empty publication."""
        (self.root / "binary.dll").unlink()
        with self.assertRaisesRegex(ValueError, "Empty"):
            collect(self.root)

    def test_paths(self) -> None:
        """Reject ambiguous path syntax."""
        for name in ("../bad", "x//y", "x/.", "C:bad", "x\\y", "x/hidden."):
            self.assertFalse(safe_entry(name))
        self.assertTrue(safe_entry("a/binary.dll"))

    def test_removed(self) -> None:
        """Detect removed files."""
        before = collect(self.root)
        (self.root / "extra.txt").write_text("keep")
        after = collect(self.root)
        (self.root / "binary.dll").unlink()
        self.assertEqual(compare(after, collect(self.root))["removed"], ["binary.dll"])
        self.assertEqual(len(before["files"]), 1)

    def test_malformed_manifest(self) -> None:
        """Reject a malformed digest."""
        before = collect(self.root)
        bad = collect(self.root)
        bad["files"][0]["sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "Invalid"):
            compare(before, bad)

    def test_hidden_file(self) -> None:
        """Reject hidden artifact members."""
        (self.root / ".hidden").write_text("not uploaded")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            collect(self.root)

    def test_symlink(self) -> None:
        """Reject links when fixture creation is supported."""
        try:
            (self.root / "link").symlink_to(self.root / "binary.dll")
        except OSError:
            self.skipTest("Symlink fixture unavailable")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            collect(self.root)

    def test_walk_error(self) -> None:
        """An unreadable directory cannot be silently omitted."""
        def broken_walk(*args, **kwargs):
            kwargs["onerror"](PermissionError("fixture"))
            return iter(())
        with patch("artifact_manifest.os.walk", side_effect=broken_walk):
            with self.assertRaises(PermissionError):
                collect(self.root)

    def test_same_size_mutation(self) -> None:
        """Detect a same-length rewrite with changed observed metadata."""
        path = self.root / "binary.dll"

        def mutate(target):
            original = hash_file(target)
            before = target.stat()
            target.write_bytes(b"changed")
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
            return original

        with patch("artifact_manifest.hash_file", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed while hashing"):
                collect(self.root)

    def test_entry_budget(self) -> None:
        """Count directories as well as files against the traversal budget."""
        (self.root / "dir").mkdir()
        with patch("artifact_manifest.MAX_ENTRIES", 1):
            with self.assertRaisesRegex(ValueError, "entry-count"):
                collect(self.root)

    def test_manifest_bound(self) -> None:
        """Reject an oversized input before JSON parsing."""
        path = self.root / MANIFEST
        path.write_bytes(b"x" * 16)
        with patch("artifact_manifest.MAX_MANIFEST", 8):
            with self.assertRaisesRegex(ValueError, "oversized"):
                load_manifest(path)

    def test_exact_schema(self) -> None:
        """Reject Boolean schema and unexpected fields."""
        original = collect(self.root)
        for bad in ({**original, "schema": True}, {**original, "extra": 1}):
            with self.assertRaisesRegex(ValueError, "schema"):
                compare(original, bad)

    def test_atomic_write_failure(self) -> None:
        """A failed replacement preserves the previous staging manifest."""
        report = collect(self.root)
        write_manifest(self.root, report)
        previous = (self.root / MANIFEST).read_bytes()
        with patch("artifact_manifest.os.replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                write_manifest(self.root, report)
        self.assertEqual((self.root / MANIFEST).read_bytes(), previous)
        self.assertEqual(load_manifest(self.root / MANIFEST), report)
        self.assertEqual(len(list(self.root.iterdir())), 2)

    def test_windows_cross_api_metadata(self) -> None:
        """Permit only Windows cross-API ctime and extension mode differences."""
        path = dict(st_dev=11, st_ino=23, st_size=7, st_mtime_ns=100,
                    st_ctime_ns=10, st_birthtime_ns=10, st_mode=stat.S_IFREG | 0o777)
        handle = {**path, "st_ctime_ns": 50, "st_mode": stat.S_IFREG | 0o666}
        with patch("artifact_manifest.os.name", "nt"):
            self.assertTrue(same_open_file(SimpleNamespace(**path), SimpleNamespace(**handle)))
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_birthtime_ns"):
                changed = {**handle, key: handle[key] + 1}
                self.assertFalse(same_open_file(SimpleNamespace(**path), SimpleNamespace(**changed)))
            changed = {**handle, "st_mode": stat.S_IFREG | 0o444}
            self.assertFalse(same_open_file(SimpleNamespace(**path), SimpleNamespace(**changed)))
        with patch("artifact_manifest.os.name", "posix"):
            self.assertFalse(same_open_file(SimpleNamespace(**path), SimpleNamespace(**handle)))

    def test_hash_executable_and_manifest(self) -> None:
        """Hash a real executable-named fixture and reopen its manifest."""
        (self.root / "fixture.exe").write_bytes(b"inert fixture")
        report = collect(self.root)
        write_manifest(self.root, report)
        self.assertEqual(load_manifest(self.root / MANIFEST), report)
        self.assertEqual(hash_file(self.root / "fixture.exe"),
                         next(x["sha256"] for x in report["files"] if x["path"] == "fixture.exe"))


if __name__ == "__main__":
    unittest.main()
