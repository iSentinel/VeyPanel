"""Verify deterministic bytes, archive membership and refusal cases."""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from artifact_manifest import MANIFEST, collect
from portable_zip import verify_zip, windows_path, write_zip, zip_info


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


if __name__ == "__main__":
    unittest.main()
