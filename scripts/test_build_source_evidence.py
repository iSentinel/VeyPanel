"""Test actual Git checkout capture and clean tracked source enforcement."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from build_source_evidence import evidence, git


class SourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "source.txt").write_text("fixture", encoding="utf-8")
        git(self.root, "add", "source.txt")
        git(self.root, "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        self.sha = git(self.root, "rev-parse", "HEAD")

    def test_matching_checkout(self):
        report = evidence(self.root, self.sha)
        self.assertEqual(report["git_commit"], self.sha)
        self.assertTrue(report["tracked_checkout_clean"])

    def test_wrong_sha(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            evidence(self.root, "0" * 40)

    def test_short_sha(self):
        with self.assertRaisesRegex(ValueError, "complete"):
            evidence(self.root, self.sha[:7])

    def test_dirty_tracked(self):
        (self.root / "source.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "uncommitted"):
            evidence(self.root, self.sha)

    def test_staged_change(self):
        (self.root / "source.txt").write_text("changed", encoding="utf-8")
        git(self.root, "add", "source.txt")
        with self.assertRaisesRegex(ValueError, "uncommitted"):
            evidence(self.root, self.sha)

    def test_generated_untracked_output(self):
        (self.root / "generated.txt").write_text("artifact", encoding="utf-8")
        self.assertEqual(evidence(self.root, self.sha)["git_commit"], self.sha)


if __name__ == "__main__":
    unittest.main()
