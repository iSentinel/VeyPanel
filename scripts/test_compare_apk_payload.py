"""Synthetic signing block structural tests, not signature validation."""

import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from compare_apk_payload import MAGIC, V2, signing_bounds
from compare_apk_payload import compare
from verify_android_apk import NOTICES


def fixture(path, payload=b"code", signature=b"fake"):
    """Insert a synthetic v2 record in a conventional test ZIP."""
    with zipfile.ZipFile(path, "w") as archive:
        for name in sorted(NOTICES | {"AndroidManifest.xml", "classes.dex", "resources.arsc"}):
            archive.writestr(name, payload)
    raw = path.read_bytes()
    end = raw.rfind(b"PK\x05\x06")
    offset = struct.unpack_from("<I", raw, end + 16)[0]
    pair = struct.pack("<QI", len(signature) + 4, V2) + signature
    size = len(pair) + 24
    block = struct.pack("<Q", size) + pair + struct.pack("<Q", size) + MAGIC
    data = bytearray(raw[:offset] + block + raw[offset:])
    struct.pack_into("<I", data, end + len(block) + 16, offset + len(block))
    path.write_bytes(data)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / "a.apk"
        self.b = Path(self.temp.name) / "b.apk"
        fixture(self.a)
        # Preserve all ZIP metadata from the first fixture.
        raw = self.a.read_bytes()
        start, end = signing_bounds(raw)
        self.b.write_bytes(raw[:start + 20] + b"diff" + raw[start + 24:])

    def test_signature_only(self):
        report = compare(self.a, self.b)
        self.assertTrue(report["outside_signing_block_identical"])
        self.assertFalse(report["full_bytes_identical"])
        self.assertFalse(report["signing_block_identical"])

    def test_identical(self):
        self.assertTrue(compare(self.a, self.a)["full_bytes_identical"])

    def test_bad_size(self):
        raw = bytearray(self.a.read_bytes())
        start, _ = signing_bounds(raw)
        raw[start] ^= 1
        with self.assertRaisesRegex(ValueError, "size"):
            signing_bounds(raw)

    def test_missing_magic(self):
        raw = self.a.read_bytes().replace(MAGIC, b"x" * len(MAGIC))
        with self.assertRaises(ValueError):
            signing_bounds(raw)

    def test_payload_difference(self):
        fixture(self.b, payload=b"xxxx")
        self.assertFalse(compare(self.a, self.b)["outside_signing_block_identical"])

    def test_different_block_sizes(self):
        fixture(self.b, signature=b"longer signature")
        self.assertFalse(compare(self.a, self.b)["outside_signing_block_identical"])


if __name__ == "__main__":
    unittest.main()
