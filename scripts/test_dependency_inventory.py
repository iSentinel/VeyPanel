"""Fixtures for the scoped runtime component inventory."""

import unittest

from dependency_inventory import make_bom


class InventoryTests(unittest.TestCase):
    """Reject ambiguous graphs and preserve actual resolved versions."""

    def test_maven(self):
        data = [{"group": "z.example", "name": "leaf", "version": "2"},
                {"group": "a.example", "name": "base", "version": "1"}]
        bom = make_bom(data, "maven", "client")
        self.assertEqual([x["purl"] for x in bom["components"]],
                         ["pkg:maven/a.example/base@1", "pkg:maven/z.example/leaf@2"])

    def test_nuget(self):
        data = {"targets": {"net10.0/win-x64": {
            "Library/2.1.0": {"type": "package"},
            "Local/1.0": {"type": "project"}}}}
        bom = make_bom(data, "nuget", "host")
        self.assertEqual(bom["components"][0]["purl"], "pkg:nuget/Library@2.1.0")
        self.assertEqual(len(bom["components"]), 1)

    def test_missing_target(self):
        with self.assertRaises(ValueError):
            make_bom({"targets": {"net10.0": {}}}, "nuget", "host")

    def test_duplicate(self):
        item = {"group": "a", "name": "b", "version": "1"}
        with self.assertRaises(ValueError):
            make_bom([item, item], "maven", "client")

    def test_empty(self):
        with self.assertRaises(ValueError):
            make_bom([], "maven", "client")

    def test_invalid_coordinate(self):
        with self.assertRaises(ValueError):
            make_bom([{"group": "a", "name": "../bad", "version": "1"}],
                     "maven", "client")


if __name__ == "__main__":
    unittest.main()
