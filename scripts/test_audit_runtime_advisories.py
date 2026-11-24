"""Offline fixtures for bounded, complete OSV advisory collection."""

import unittest

from audit_runtime_advisories import scan


class AuditTests(unittest.TestCase):
    """Check matching, pagination and failure cases."""

    def setUp(self):
        self.entries = {"pkg:maven/example/lib@1":
                        {"package": {"name": "example:lib", "ecosystem": "Maven"},
                         "version": "1"}}

    def test_empty_matches(self):
        self.assertEqual(scan(self.entries, lambda _: {"results": [{}]}),
                         {"pkg:maven/example/lib@1": {}})

    def test_match(self):
        record = {"id": "TEST-1", "modified": "2026-11-24T00:00:00Z"}
        result = scan(self.entries, lambda _: {"results": [{"vulns": [record]}]})
        self.assertEqual(result["pkg:maven/example/lib@1"]["TEST-1"], record["modified"])

    def test_pages(self):
        def request(queries):
            if "page_token" not in queries[0]:
                return {"results": [{"next_page_token": "next"}]}
            return {"results": [{"vulns": [{"id": "TEST-2", "modified": "time"}]}]}
        self.assertIn("TEST-2", scan(self.entries, request)["pkg:maven/example/lib@1"])

    def test_incomplete(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            scan(self.entries, lambda _: {"results": []})

    def test_repeated_page(self):
        with self.assertRaisesRegex(ValueError, "repeated"):
            scan(self.entries, lambda _: {"results": [{"next_page_token": "same"}]})

    def test_unknown_schema(self):
        with self.assertRaisesRegex(ValueError, "schema"):
            scan(self.entries, lambda _: {"results": [{"error": "not available"}]})


if __name__ == "__main__":
    unittest.main()
