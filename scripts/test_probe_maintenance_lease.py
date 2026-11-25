"""Offline scope checks for the isolated reverse lease contender."""

from pathlib import Path
import tempfile
import unittest

from probe_maintenance_lease import fixture_path


class FixturePathTests(unittest.TestCase):
    """Keep fixture commands restricted to the expected temporary child."""

    def setUp(self) -> None:
        """Create a temporary parent and fixed inert fixture directory."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve(strict=True)
        self.parent = self.root / "veypanel-lease-test"
        self.parent.mkdir()
        self.path = self.parent / "admission.fixture"

    def test_fixed_scope(self) -> None:
        """Resolve the parent without opening or requiring the held leaf."""
        self.assertEqual(fixture_path(self.path, self.root), self.path)
        self.assertFalse(self.path.exists())

    def test_wrong_name(self) -> None:
        """Reject other file names under the same fixture directory."""
        with self.assertRaisesRegex(ValueError, "scope"):
            fixture_path(self.parent / "other.fixture", self.root)

    def test_nested_or_outside(self) -> None:
        """Refuse a nested fixture and explicit parent traversal."""
        nested = self.parent / "veypanel-lease-nested"
        nested.mkdir()
        with self.assertRaisesRegex(ValueError, "scope"):
            fixture_path(nested / self.path.name, self.root)
        with self.assertRaisesRegex(ValueError, "path"):
            fixture_path(self.parent / ".." / self.parent.name / self.path.name, self.root)


if __name__ == "__main__":
    unittest.main()
