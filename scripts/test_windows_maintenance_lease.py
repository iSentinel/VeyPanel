"""Offline controls for the prototype; actual sharing requires Windows CI."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from windows_maintenance_lease import INVALID_HANDLE, lease


class LeaseTests(unittest.TestCase):
    """Check adapter validation, error classification and handle cleanup."""

    def setUp(self) -> None:
        """Use an inert private fixture file and mocked kernel API."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name).absolute() / "lease.fixture"
        self.path.write_bytes(b"VP")
        self.kernel = Mock()
        self.kernel.CreateFileW.return_value = 123
        self.kernel.CloseHandle.return_value = True

    def test_access_and_close(self) -> None:
        """Use exact Windows access/share flags and close both modes."""
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            for exclusive, access, share in ((False, 0x80000000, 1), (True, 0xC0000000, 0)):
                with lease(self.path, exclusive) as admitted:
                    self.assertTrue(admitted)
                self.kernel.CreateFileW.assert_called_with(
                    str(self.path), access, share, None, 3, 0x80, None)
        self.assertEqual(self.kernel.CloseHandle.call_count, 2)
        self.assertEqual(self.path.read_bytes(), b"VP")

    def test_busy_only(self) -> None:
        """Classify only sharing violation as contention, never access denied."""
        self.kernel.CreateFileW.return_value = INVALID_HANDLE
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with patch("windows_maintenance_lease._last_error", return_value=32):
                with lease(self.path, True) as admitted:
                    self.assertFalse(admitted)
            with patch("windows_maintenance_lease._last_error", return_value=5):
                with self.assertRaises(OSError):
                    with lease(self.path, True):
                        self.fail("Access denied admitted")
        self.kernel.CloseHandle.assert_not_called()

    def test_close_on_exception(self) -> None:
        """Release the handle when the operation raises."""
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                with lease(self.path, True):
                    raise RuntimeError("fixture")
        self.kernel.CloseHandle.assert_called_once_with(123)

    def test_missing_and_directory(self) -> None:
        """Refuse absent or directory paths before native open."""
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel) as kernel:
            with self.assertRaises(OSError):
                with lease(self.path.with_name("missing"), True):
                    self.fail("Missing lease admitted")
            with self.assertRaises(ValueError):
                with lease(self.path.parent, True):
                    self.fail("Directory lease admitted")
        kernel.assert_not_called()


if __name__ == "__main__":
    unittest.main()
