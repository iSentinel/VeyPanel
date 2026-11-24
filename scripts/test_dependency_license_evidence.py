"""Test literal license extraction and verified-cache enforcement."""

import base64
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from dependency_license_evidence import (archive_evidence, maven_licenses,
                                         maven_record, nuget_licenses, nuget_record, parse_xml)


class LicenseEvidenceTests(unittest.TestCase):
    """Synthetic fixtures do not assert upstream license terms."""

    def test_pom(self):
        raw = b'<project><licenses><license><name>Test</name></license></licenses></project>'
        self.assertEqual(maven_licenses(raw), [{"name": "Test", "url": None}])

    def test_missing_pom_license(self):
        self.assertEqual(maven_licenses(b"<project/>"), [])

    def test_nuspec(self):
        raw = b'<package><metadata><license type="expression">MIT</license></metadata></package>'
        self.assertEqual(nuget_licenses(raw), [{"type": "expression", "value": "MIT"}])

    def test_unsafe_xml(self):
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            parse_xml(b"<!DOCTYPE a><a/>")

    def test_notice_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lib.jar"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("META-INF/LICENSE", "fixture")
                archive.writestr("binary.class", "skip")
            result = archive_evidence(path)
            self.assertEqual(len(result["notice_files"]), 1)
            self.assertEqual(result["notice_files"][0]["sha256"],
                             hashlib.sha256(b"fixture").hexdigest())

    def test_nuget_locked_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "example/1.0/example.1.0.nupkg"
            path.parent.mkdir(parents=True)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("Example.nuspec",
                    '<package><metadata><license type="expression">MIT</license></metadata></package>')
                archive.writestr("LICENSE.txt", "fixture")
            component = {"name": "Example", "version": "1.0",
                         "purl": "pkg:nuget/Example@1.0"}
            digest = base64.b64encode(hashlib.sha512(path.read_bytes()).digest()).decode()
            lock = {"dependencies": {"net10.0": {"Example": {
                "resolved": "1.0", "contentHash": digest}}}}
            record = nuget_record(component, lock, root)
            self.assertEqual(record["artifacts"][0]["declared_licenses"],
                             [{"type": "expression", "value": "MIT"}])
            with path.open("ab") as output:
                output.write(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA-512 mismatch"):
                nuget_record(component, lock, root)

    def test_cache_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "org.example/lib/1/cache/lib-1.pom"
            path.parent.mkdir(parents=True)
            path.write_text("<project/>")
            component = {"group": "org.example", "name": "lib",
                         "version": "1", "purl": "pkg:maven/org.example/lib@1"}
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                maven_record(component, {("org.example", "lib", "1", path.name):
                                        "0" * 64}, root)


if __name__ == "__main__":
    unittest.main()
