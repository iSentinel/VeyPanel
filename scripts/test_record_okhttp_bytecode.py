"""Verify static bytecode evidence boundaries with inert ZIP fixtures."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from record_okhttp_bytecode import CLASSES, COORDINATE, MAX_JAR, disassemble, inspect_jar, record


class BytecodeEvidenceTests(unittest.TestCase):
    """Verify exact-byte input and safe, bounded disassembly capture."""

    def setUp(self) -> None:
        """Create one disposable, non-executable class-header fixture."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.jar = Path(temp.name) / "fixture.jar"
        with zipfile.ZipFile(self.jar, "w") as archive:
            for name in CLASSES:
                archive.writestr(name.replace(".", "/") + ".class", bytes.fromhex("cafebabe"))

    def test_exact_bytes(self) -> None:
        """Return only bytes matching the expected digest and class inventory."""
        raw = self.jar.read_bytes()
        self.assertEqual(inspect_jar(self.jar, hashlib.sha256(raw).hexdigest())[0], raw)
        self.assertEqual(len(inspect_jar(self.jar, hashlib.sha256(raw).hexdigest())[1]), 3)

    def test_wrong_hash(self) -> None:
        """Do not parse a wrong-digest archive."""
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            inspect_jar(self.jar, "0" * 64)

    def test_oversized(self) -> None:
        """Refuse a file larger than the fixed JAR budget."""
        self.jar.write_bytes(b"x" * (MAX_JAR + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            inspect_jar(self.jar, "0" * 64)

    def test_duplicate_class(self) -> None:
        """Reject ambiguous class entries even in a digest-matching fixture."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.jar, "a") as archive:
                archive.writestr(CLASSES[0].replace(".", "/") + ".class", b"duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect_jar(self.jar, hashlib.sha256(self.jar.read_bytes()).hexdigest())

    def test_disassembly_input(self) -> None:
        """Pass the exact verified snapshot to a fixed non-shell javap invocation."""
        raw = self.jar.read_bytes()
        expected = "\n".join(CLASSES).encode("ascii")

        def fake_run(args, **kwargs):
            self.assertEqual(args[:4], ["javap", "-c", "-p", "-classpath"])
            self.assertEqual(Path(args[4]).read_bytes(), raw)
            self.assertEqual(tuple(args[5:]), CLASSES)
            self.assertEqual(kwargs["timeout"], 30)
            self.assertTrue(kwargs["check"])
            return subprocess.CompletedProcess(args, 0, stdout=expected)

        with patch("record_okhttp_bytecode.subprocess.run", side_effect=fake_run):
            self.assertEqual(disassemble(raw), expected)

    def test_incomplete_output(self) -> None:
        """Reject a successful process with missing class evidence."""
        with patch("record_okhttp_bytecode.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, stdout=b"not complete")):
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                disassemble(b"fixture")

    def test_report_scope(self) -> None:
        """Record actual digests and explicit limits without overwriting evidence."""
        raw = self.jar.read_bytes()
        expected = hashlib.sha256(raw).hexdigest()
        report = "\n".join(CLASSES).encode("ascii")
        output = self.jar.parent / "report"
        with patch("record_okhttp_bytecode.read_metadata"), patch(
                "record_okhttp_bytecode.inventory", return_value={COORDINATE: expected}), patch(
                "record_okhttp_bytecode.disassemble", return_value=report):
            record(self.jar, self.jar, output)
            data = json.loads((output / "summary.json").read_text())
            self.assertEqual(data["jar_sha256"], expected)
            self.assertEqual(data["javap_sha256"], hashlib.sha256(report).hexdigest())
            self.assertEqual(data["source_to_binary"], "NOT_ESTABLISHED")
            self.assertEqual(data["preallocation_bound"], "REVIEW_REQUIRED")
            with self.assertRaises(FileExistsError):
                record(self.jar, self.jar, output)
        self.assertEqual((output / "javap.txt").read_bytes(), report)


if __name__ == "__main__":
    unittest.main()
