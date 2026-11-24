"""Fixtures for narrowly scoped deterministic static endpoint metadata."""

import copy
import unittest

from normalize_static_endpoints import normalize


def fixture():
    return {"Version": 1, "ManifestType": "Publish", "Endpoints": [{
        "Route": "app.js", "AssetFile": "app.js.gz",
        "ResponseHeaders": [
            {"Name": "ETag", "Value": '"fixture"'},
            {"Name": "Last-Modified", "Value": "Tue, 24 Nov 2026 10:45:18 GMT"},
        ],
    }]}


class NormalizeTests(unittest.TestCase):
    def test_only_timestamp_changes(self):
        data = fixture()
        expected = copy.deepcopy(data)
        expected["Endpoints"][0]["ResponseHeaders"][1]["Value"] = "Tue, 14 Nov 2023 22:13:20 GMT"
        self.assertEqual(normalize(data, 1700000000), 1)
        self.assertEqual(data, expected)

    def test_idempotent(self):
        data = fixture()
        normalize(data, 1700000000)
        before = copy.deepcopy(data)
        normalize(data, 1700000000)
        self.assertEqual(data, before)

    def test_duplicate_header(self):
        data = fixture()
        data["Endpoints"][0]["ResponseHeaders"].append(
            {"Name": "last-modified", "Value": "Tue, 24 Nov 2026 10:45:18 GMT"})
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            normalize(data, 1700000000)

    def test_missing_header(self):
        data = fixture()
        data["Endpoints"][0]["ResponseHeaders"].pop()
        with self.assertRaisesRegex(ValueError, "Missing"):
            normalize(data, 1700000000)

    def test_wrong_manifest(self):
        data = fixture()
        data["ManifestType"] = "Build"
        with self.assertRaisesRegex(ValueError, "published"):
            normalize(data, 1700000000)

    def test_invalid_epoch(self):
        with self.assertRaisesRegex(ValueError, "epoch"):
            normalize(fixture(), 0)


if __name__ == "__main__":
    unittest.main()
