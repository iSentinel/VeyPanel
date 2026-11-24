"""Verify launch policy with inert packages and a mocked process boundary."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from artifact_manifest import MANIFEST, collect, hash_file
from launch_windows_package import launch
from test_windows_package_selection import fixture
from windows_package_selection import LOCK, STATE, select, version_path


class LaunchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "install"
        self.root.mkdir()
        self.package, self.sha = fixture(Path(temp.name), "a", b"fixture")
        self.other, self.other_sha = fixture(Path(temp.name), "b", b"other")
        self.record = select(self.root, self.package, self.sha, True)
        self.exe = version_path(self.root, self.sha) / "VeyPanel.Desktop.exe"

    def test_dry_run(self):
        before = (self.root / STATE).read_bytes()
        with patch("launch_windows_package.subprocess.Popen") as spawn:
            result = launch(self.root, self.package, self.sha)
        spawn.assert_not_called()
        self.assertFalse(result["started"])
        self.assertEqual(result["executable"], str(self.exe))
        self.assertEqual((self.root / STATE).read_bytes(), before)

    def test_explicit_apply(self):
        with patch("launch_windows_package.windows_runtime", return_value=True):
            with patch("launch_windows_package.subprocess.Popen") as spawn:
                spawn.return_value.pid = 123
                result = launch(self.root, self.package, self.sha, True)
                spawn.assert_called_once_with([str(self.exe)], cwd=str(self.exe.parent),
                                              shell=False)
        self.assertEqual(result["pid"], 123)
        self.assertFalse((self.root / LOCK).exists())

    def test_non_windows_apply_refused(self):
        with patch("launch_windows_package.windows_runtime", return_value=False):
            with self.assertRaisesRegex(ValueError, "native Windows"):
                launch(self.root, self.package, self.sha, True)

    def test_wrong_selected_digest(self):
        with self.assertRaisesRegex(ValueError, "Selected package"):
            launch(self.root, self.other, self.other_sha)

    def test_wrong_archive(self):
        with self.assertRaisesRegex(ValueError, "External SHA-256"):
            launch(self.root, self.other, self.sha)

    def test_modified_executable(self):
        self.exe.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "files differ"):
            launch(self.root, self.package, self.sha)

    def test_rewritten_manifest_and_state(self):
        self.exe.write_bytes(b"changed")
        manifest = self.exe.parent / MANIFEST
        manifest.write_text(json.dumps(collect(self.exe.parent)), encoding="utf-8")
        state = json.loads((self.root / STATE).read_text())
        state["active"]["manifest_sha256"] = hash_file(manifest)
        (self.root / STATE).write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "trusted archive"):
            launch(self.root, self.package, self.sha)

    def test_locked(self):
        (self.root / LOCK).mkdir()
        with self.assertRaisesRegex(ValueError, "locked"):
            launch(self.root, self.package, self.sha)

    def test_spawn_failure(self):
        with patch("launch_windows_package.windows_runtime", return_value=True):
            with patch("launch_windows_package.subprocess.Popen", side_effect=OSError("fixture")):
                with self.assertRaises(OSError):
                    launch(self.root, self.package, self.sha, True)
        self.assertFalse((self.root / LOCK).exists())


if __name__ == "__main__":
    unittest.main()
