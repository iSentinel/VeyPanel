"""Verify deterministic bytes, archive membership and refusal cases."""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from artifact_manifest import MANIFEST, collect
from portable_zip import MAX_MANIFEST, read_zip_metadata, verify_zip, windows_path, write_zip, zip_info


class PortableZipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "binary.exe").write_bytes(b"test binary")
        self.manifest = self.source / MANIFEST
        self.manifest.write_text(json.dumps(collect(self.source)), encoding="utf-8")
        self.archive = self.root / "output.zip"

    def test_reproducible(self):
        write_zip(self.source, self.archive)
        second = self.root / "second.zip"
        write_zip(self.source, second)
        self.assertEqual(self.archive.read_bytes(), second.read_bytes())
        self.assertEqual(verify_zip(self.archive), 1)

    def test_no_overwrite(self):
        self.archive.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            write_zip(self.source, self.archive)
        self.assertEqual(self.archive.read_bytes(), b"existing")

    def test_tampered_source(self):
        (self.source / "binary.exe").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "manifest mismatch"):
            write_zip(self.source, self.archive)
        self.assertFalse(self.archive.exists())

    def test_output_inside_source(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            write_zip(self.source, self.source / "output.zip")

    def test_windows_names(self):
        for name in ("../file", "CON.txt", "folder/NUL", "x/COM1.dll", "x/LPT²"):
            self.assertFalse(windows_path(name))
        self.assertTrue(windows_path("host/library.dll"))

    def test_bad_member_hash(self):
        with zipfile.ZipFile(self.archive, "w") as archive:
            raw = self.manifest.read_bytes()
            archive.writestr(zip_info(MANIFEST, len(raw)), raw)
            archive.writestr(zip_info("binary.exe", 11), b"bad content")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            verify_zip(self.archive)

    def test_unlisted_member(self):
        with zipfile.ZipFile(self.archive, "w") as archive:
            raw = self.manifest.read_bytes()
            archive.writestr(zip_info(MANIFEST, len(raw)), raw)
            archive.writestr(zip_info("binary.exe", 11), b"test binary")
            archive.writestr(zip_info("extra.txt", 1), b"x")
        with self.assertRaisesRegex(ValueError, "membership"):
            verify_zip(self.archive)

    def test_case_collision(self):
        with zipfile.ZipFile(self.archive, "w") as archive:
            for name in ("BINARY.EXE", MANIFEST, "binary.exe"):
                archive.writestr(zip_info(name, 1), b"x")
        with self.assertRaisesRegex(ValueError, "membership"):
            verify_zip(self.archive)

    def test_duplicate_source_schema(self) -> None:
        """Reject ambiguous source manifest before creating a ZIP."""
        raw = self.manifest.read_text().replace('"schema": 1', '"schema": 2, "schema": 1')
        self.manifest.write_text(raw)
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            write_zip(self.source, self.archive)
        self.assertFalse(self.archive.exists())

    def test_duplicate_archive_schema(self) -> None:
        """Reject ambiguous embedded manifests even when payload hash matches."""
        raw = self.manifest.read_bytes().replace(b'"schema": 1', b'"schema": 2, "schema": 1')
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr(zip_info(MANIFEST, len(raw)), raw)
            archive.writestr(zip_info("binary.exe", 11), b"test binary")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            verify_zip(self.archive)

    def test_oversized_source_manifest(self) -> None:
        """Refuse source metadata exceeding the shared bounded read budget."""
        self.manifest.write_bytes(b"x" * (MAX_MANIFEST + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            write_zip(self.source, self.archive)
        self.assertFalse(self.archive.exists())

    def test_embedded_metadata_limit(self) -> None:
        """Refuse a declared member beyond the supplied metadata budget."""
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("fixture", b"12345")
        with zipfile.ZipFile(self.archive) as archive:
            with self.assertRaisesRegex(ValueError, "Oversized"):
                read_zip_metadata(archive, "fixture", 4)
            self.assertEqual(read_zip_metadata(archive, "fixture", 5), b"12345")


if __name__ == "__main__":
    unittest.main()
