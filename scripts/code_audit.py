#!/usr/bin/env python3
"""Audit tracked Python source without importing it; enforce exact debt identity."""

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

Finding = dict[str, str | int]
Identity = tuple[str, str, str, str]
MAX_SOURCE = 2 * 1024 * 1024
MAX_BASELINE = 8 * 1024 * 1024


def tracked_python(root: Path) -> list[str]:
    """List tracked Python files, including staged additions."""
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "*.py"],
                            check=True, capture_output=True, timeout=30)
    return sorted(set(result.stdout.decode("utf-8").rstrip("\0").split("\0")) - {""})


def finding(path: str, symbol: str, node: ast.AST, rule: str, detail: str) -> Finding:
    """Return a finding with stable identity and informational line number."""
    return {"path": path, "symbol": symbol, "line": node.lineno,
            "rule": rule, "detail": detail}


def public(name: str, parent_public: bool) -> bool:
    """Include constructors and public symbols in public scopes."""
    return parent_public and (not name.startswith("_") or name == "__init__")


def function_findings(path: str, symbol: str, node: ast.FunctionDef | ast.AsyncFunctionDef,
                      exposed: bool) -> list[Finding]:
    """Check length and the documented public signature rules."""
    rows = []
    if node.end_lineno - node.lineno + 1 > 40:
        rows.append(finding(path, symbol, node, "length", "function exceeds 40 lines"))
    if not exposed:
        return rows
    if not ast.get_docstring(node):
        rows.append(finding(path, symbol, node, "docstring", "missing public docstring"))
    args = node.args
    parameters = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    parameters.extend(arg for arg in (args.vararg, args.kwarg) if arg is not None)
    for parameter in parameters:
        if parameter.arg not in ("self", "cls") and parameter.annotation is None:
            rows.append(finding(path, symbol, node, "annotation",
                                "missing parameter: " + parameter.arg))
    if node.returns is None:
        rows.append(finding(path, symbol, node, "annotation", "missing return"))
    return rows


def scan_node(path: str, node: ast.AST, prefix: str = "",
              parent_public: bool = True) -> list[Finding]:
    """Traverse lexical scopes, including nested/private functions for length."""
    rows = []
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        symbol = prefix + node.name
        exposed = public(node.name, parent_public)
        if isinstance(node, ast.ClassDef):
            if exposed and not ast.get_docstring(node):
                rows.append(finding(path, symbol, node, "docstring", "missing public docstring"))
            parent_public = exposed
        else:
            rows.extend(function_findings(path, symbol, node, exposed))
            parent_public = False
        prefix = symbol + "."
    for child in ast.iter_child_nodes(node):
        rows.extend(scan_node(path, child, prefix, parent_public))
    return rows


def scan(root: Path) -> list[Finding]:
    """Parse bounded tracked files; reject missing or linked source."""
    rows = []
    for name in tracked_python(root):
        path = root / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_SOURCE:
            raise ValueError("Unsafe or missing tracked source: " + name)
        rows.extend(scan_node(name, ast.parse(path.read_bytes(), filename=name)))
    return sorted(rows, key=lambda row: (*identity(row), row["line"]))


def identity(row: Finding) -> Identity:
    """Ignore line number but retain all stable finding fields."""
    values = tuple(row[key] for key in ("path", "symbol", "rule", "detail"))
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError("Invalid finding identity")
    return values


def differences(actual: list[Finding], baseline: list[Finding]) -> dict[str, list[Identity]]:
    """Preserve duplicate multiplicity; reject additions and stale debt entries."""
    a, b = Counter(map(identity, actual)), Counter(map(identity, baseline))
    return {"new": sorted((a - b).elements()), "resolved": sorted((b - a).elements())}


def load_baseline(path: Path) -> list[Finding]:
    """Read the committed baseline without any automatic regeneration."""
    if path.stat().st_size > MAX_BASELINE:
        raise ValueError("Debt baseline exceeds size budget")
    data = json.loads(path.read_bytes())
    if data.get("schema") != 1 or not isinstance(data.get("findings"), list):
        raise ValueError("Invalid debt baseline schema")
    return data["findings"]


def main() -> int:
    """Print versioned audit JSON and fail on new or stale baseline findings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--baseline", type=Path, default=Path("config/code-audit-baseline.json"))
    parser.add_argument("--inventory", action="store_true", help="Report only; never passes a gate")
    args = parser.parse_args()
    try:
        rows = scan(args.root)
        report: dict[str, Any] = {"schema": 1, "findings": rows}
        if args.inventory:
            report["status"] = "INCONCLUSIVE"
        else:
            report.update(differences(rows, load_baseline(args.baseline)))
            report["status"] = "FAIL" if report["new"] or report["resolved"] else "PASS"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 2
    except (OSError, ValueError, SyntaxError, KeyError, TypeError,
            AttributeError, subprocess.SubprocessError) as error:
        print("FAIL: source audit: " + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
