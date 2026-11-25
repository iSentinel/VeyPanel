"""Test maintenance inventory without removing or executing installed files."""

from pathlib import Path
import tempfile
import unittest

from artifact_manifest import collect
from plan_windows_maintenance import plan
from test_windows_package_selection import fixture
from windows_package_selection import LOCK, STATE, select, version_path


class MaintenancePlanTests(unittest.TestCase):
    """Require exact retained archives and refuse ambiguous installations."""

    def setUp(self) -> None:
        """Create two inert verified versions in a private test root."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "install"
        self.root.mkdir()
        first, self.first = fixture(base, "a", b"first")
        second, self.second = fixture(base, "b", b"second")
        self.archives = {self.first: first, self.second: second}
        select(self.root, first, self.first, True)
        select(self.root, second, self.second, True)

    def test_verified_read_only(self) -> None:
        """Return a stable inventory plan without authorizing mutation."""
        before = collect(self.root)
        result = plan(self.root, self.archives)
        self.assertEqual(result, plan(self.root, self.archives))
        self.assertEqual(collect(self.root), before)
        self.assertFalse(result["maintenance_admitted"])
        self.assertFalse(result["removed"])
        self.assertEqual(result["process_state"], "NOT_CHECKED")

    def test_missing_archive(self) -> None:
        """Require the previous archive as well as the active archive."""
        with self.assertRaisesRegex(ValueError, "archive set"):
            plan(self.root, {self.second: self.archives[self.second]})

    def test_unexpected_root(self) -> None:
        """Do not classify an unknown file as disposable package data."""
        unknown = self.root / "private.txt"
        unknown.write_bytes(b"fixture")
        with self.assertRaisesRegex(ValueError, "Unexpected root"):
            plan(self.root, self.archives)
        self.assertEqual(unknown.read_bytes(), b"fixture")

    def test_orphan_version(self) -> None:
        """Refuse an unreferenced version even if the name looks valid."""
        (self.root / "versions" / ("a" * 64)).mkdir()
        with self.assertRaisesRegex(ValueError, "retained versions"):
            plan(self.root, self.archives)

    def test_changed_payload(self) -> None:
        """Refuse modified files in the previous version too."""
        (version_path(self.root, self.first) / "VeyPanel.Desktop.exe").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "files differ"):
            plan(self.root, self.archives)

    def test_locked(self) -> None:
        """Never clear a lock left by a cooperating writer."""
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            plan(self.root, self.archives)
        self.assertTrue((self.root / LOCK).is_dir())

    def test_metadata_identity(self) -> None:
        """Bind the exact selection bytes, not just parsed values."""
        before = plan(self.root, self.archives)
        path = self.root / STATE
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertNotEqual(before["plan_sha256"], plan(self.root, self.archives)["plan_sha256"])

    def test_wrong_archive(self) -> None:
        """Refuse a duplicate archive masquerading as a previous version."""
        archives = dict(self.archives)
        archives[self.first] = archives[self.second]
        with self.assertRaisesRegex(ValueError, "External SHA-256"):
            plan(self.root, archives)

    def test_single_version(self) -> None:
        """Accept one verified selected version without inventing previous state."""
        root = self.root.parent / "single"
        root.mkdir()
        select(root, self.archives[self.first], self.first, True)
        result = plan(root, {self.first: self.archives[self.first]})
        self.assertIsNone(result["selection"]["previous"])
        self.assertFalse(result["maintenance_admitted"])


if __name__ == "__main__":
    unittest.main()
