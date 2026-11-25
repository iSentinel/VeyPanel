"""Regression tests for exact debt comparison and source-only checks."""

import ast
import unittest

from code_audit import differences, scan_node


class AuditTests(unittest.TestCase):
    """Exercise stable identities and precise scope."""

    def test_public_signature(self) -> None:
        """Public classes and methods require documentation and annotations."""
        rows = scan_node("fixture.py", ast.parse("class Thing:\n def __init__(self, x): pass\n"))
        self.assertEqual(len(rows), 4)
        self.assertIn("missing parameter: x", {row["detail"] for row in rows})

    def test_nested_private_length(self) -> None:
        """Private nested functions retain the length constraint."""
        source = "def outer() -> None:\n \"\"\"Outer.\"\"\"\n def _inner():\n" + "  pass\n" * 41
        rows = scan_node("fixture.py", ast.parse(source))
        self.assertEqual([(row["symbol"], row["rule"]) for row in rows],
                         [("outer", "length"), ("outer._inner", "length")])

    def test_line_shift(self) -> None:
        """Line number changes do not change finding identity."""
        a = scan_node("fixture.py", ast.parse("def f(): pass"))
        b = scan_node("fixture.py", ast.parse("\n\ndef f(): pass"))
        self.assertEqual(differences(a, b), {"new": [], "resolved": []})

    def test_no_netting(self) -> None:
        """New debt cannot be canceled by resolving unrelated debt."""
        a = scan_node("fixture.py", ast.parse("def f(): pass"))
        b = scan_node("fixture.py", ast.parse("def g(): pass"))
        result = differences(a, b)
        self.assertEqual(len(result["new"]), 2)
        self.assertEqual(len(result["resolved"]), 2)

    def test_duplicate_counts(self) -> None:
        """Identical repeated declarations retain their multiplicity."""
        a = scan_node("fixture.py", ast.parse("def f(): pass"))
        self.assertEqual(len(differences(a + a, a)["new"]), len(a))

    def test_no_execution(self) -> None:
        """Top-level source is parsed, not executed."""
        self.assertEqual(scan_node("fixture.py", ast.parse("raise RuntimeError()")), [])


if __name__ == "__main__":
    unittest.main()
