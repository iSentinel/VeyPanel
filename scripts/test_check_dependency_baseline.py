"""Fixtures for post-resolution component drift detection."""

import unittest

from check_dependency_baseline import compare


def inventory(*urls, scope="VeyPanel-Android-debug"):
    """Build a minimal component inventory."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {"component": {"name": scope}},
        "components": [{"purl": url} for url in urls],
    }


class BaselineTests(unittest.TestCase):
    """Exercise version, membership, order, and scope drift."""

    def test_order_independent(self):
        a, b = "pkg:maven/org.example/a@1", "pkg:maven/org.example/b@2"
        self.assertEqual(compare(inventory(a, b), inventory(b, a)), ([], []))

    def test_version_changed(self):
        a, b = "pkg:maven/org.example/a@1", "pkg:maven/org.example/a@2"
        self.assertEqual(compare(inventory(a), inventory(b)), ([b], [a]))

    def test_added(self):
        a, b = "pkg:maven/org.example/a@1", "pkg:maven/org.example/b@2"
        self.assertEqual(compare(inventory(a), inventory(a, b)), ([b], []))

    def test_removed(self):
        a, b = "pkg:maven/org.example/a@1", "pkg:maven/org.example/b@2"
        self.assertEqual(compare(inventory(a, b), inventory(a)), ([], [b]))

    def test_scope_mismatch(self):
        a = "pkg:maven/org.example/a@1"
        with self.assertRaisesRegex(ValueError, "scope"):
            compare(inventory(a), inventory(a, scope="unrelated"))

    def test_duplicate(self):
        a = "pkg:maven/org.example/a@1"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare(inventory(a), inventory(a, a))

    def test_empty(self):
        with self.assertRaises(ValueError):
            compare(inventory(), inventory())

    def test_invalid_purl(self):
        with self.assertRaises(ValueError):
            compare(inventory("invalid"), inventory("invalid"))


if __name__ == "__main__":
    unittest.main()
