"""Synthetic positive and negative APK integrity fixtures."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from verify_android_apk import NOTICES, verify


class ApkVerifyTests(unittest.TestCase):
    """Exercise the ZIP policy without requiring Android tools."""

    def setUp(self) -> None:
        """Create a disposable APK path."""
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "test.apk"

    def tearDown(self) -> None:
        """Remove the disposable fixture directory."""
        self.temporary.cleanup()

    def make_archive(self, names: list[str], notices: bool = True) -> None:
        """Create a minimal ZIP with optionally bundled license notices."""
        all_names = list(names) + (sorted(NOTICES) if notices else [])
        with zipfile.ZipFile(self.path, "w") as output:
            for name in all_names:
                output.writestr(name, b"x")

    def test_valid_zip(self) -> None:
        """Required entries and CRCs are accepted."""
        self.make_archive(["AndroidManifest.xml", "classes.dex", "resources.arsc"])
        count, total, digest = verify(self.path)
        self.assertEqual((count, total), (3 + len(NOTICES), 3 + len(NOTICES)))
        self.assertEqual(len(digest), 64)

    def test_missing_manifest(self) -> None:
        """An ordinary ZIP without a manifest is rejected."""
        self.make_archive(["classes.dex", "resources.arsc"])
        with self.assertRaisesRegex(ValueError, "essential"):
            verify(self.path)

    def test_missing_notices(self) -> None:
        """Third-party notices must survive APK packaging."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc"],
            notices=False)
        with self.assertRaisesRegex(ValueError, "license notices"):
            verify(self.path)

    def test_path_traversal(self) -> None:
        """Traversal is an invalid entry name."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc", "../bad"])
        with self.assertRaisesRegex(ValueError, "entry name"):
            verify(self.path)

    def test_duplicate_casefold(self) -> None:
        """Case-insensitive duplicates are rejected."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc", "CLASSES.DEX"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            verify(self.path)

    def test_backslash_path(self) -> None:
        """Write an actual backslash byte without host ZIP normalization."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc",
             "assetsXunsafe"])
        raw = self.path.read_bytes()
        self.assertEqual(raw.count(b"assetsXunsafe"), 2)
        self.path.write_bytes(raw.replace(b"assetsXunsafe", b"assets\\unsafe"))
        with self.assertRaisesRegex(ValueError, "entry name"):
            verify(self.path)

    def test_nul_path(self) -> None:
        """Reject an original name truncated by ZIP parsing at NUL."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc",
             "assetsXunsafe"])
        raw = self.path.read_bytes()
        self.assertEqual(raw.count(b"assetsXunsafe"), 2)
        self.path.write_bytes(raw.replace(b"assetsXunsafe", b"assets\x00unsafe"))
        with self.assertRaisesRegex(ValueError, "entry name"):
            verify(self.path)

    def test_ambiguous_separator(self) -> None:
        """Empty directory components are rejected."""
        self.make_archive(
            ["AndroidManifest.xml", "classes.dex", "resources.arsc",
             "assets//unsafe"])
        with self.assertRaisesRegex(ValueError, "entry name"):
            verify(self.path)

    def test_truncated(self) -> None:
        """A truncated archive fails closed."""
        self.path.write_bytes(bytes([80, 75, 3, 4]))
        with self.assertRaises(zipfile.BadZipFile):
            verify(self.path)

    def test_symlink_rejected(self) -> None:
        """Unix symlinks are rejected."""
        with zipfile.ZipFile(self.path, "w") as output:
            for name in ["AndroidManifest.xml", "classes.dex", "resources.arsc"]:
                output.writestr(name, b"x")
            for name in sorted(NOTICES):
                output.writestr(name, b"x")
            link = zipfile.ZipInfo("link")
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            output.writestr(link, b"target")
        with self.assertRaisesRegex(ValueError, "symlink"):
            verify(self.path)

    def test_colon_in_entry(self) -> None:
        """Reject colon-delimited stream-like names."""
        for name in ("drive:stream", "assets/file:stream"):
            self.make_archive(["AndroidManifest.xml", "classes.dex", "resources.arsc", name])
            with self.assertRaisesRegex(ValueError, "entry name"):
                verify(self.path)

    def test_repeated_trailing_separator(self) -> None:
        """Reject multiple trailing directory separators."""
        self.make_archive(["AndroidManifest.xml", "classes.dex", "resources.arsc", "assets//"])
        with self.assertRaisesRegex(ValueError, "entry name"):
            verify(self.path)


if __name__ == "__main__":
    unittest.main()
