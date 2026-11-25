"""Offline controls for the prototype; actual sharing requires Windows CI."""

import ctypes
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from windows_maintenance_lease import (
    INVALID_HANDLE, _FileInformation, identified_lease, lease,
)


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

    def configure_identity(self, attributes: int = 0x80, links: int = 1,
                           index: int = 0x123456789ABCDEF0) -> None:
        """Populate the actual Win32 layout through the mocked native output."""
        info = _FileInformation()
        info.attributes = attributes
        info.links = links
        info.volume = 0x11223344
        info.index_high = index >> 32
        info.index_low = index & 0xFFFFFFFF

        def populate(handle: int, output: object) -> bool:
            self.assertEqual(handle, 123)
            ctypes.memmove(output, ctypes.byref(info), ctypes.sizeof(info))
            return True

        self.kernel.GetFileInformationByHandle.side_effect = populate

    def test_identity_layout_and_match(self) -> None:
        """Decode the fixed Win32 layout and compare the full 64-bit index."""
        self.assertEqual(ctypes.sizeof(_FileInformation), 52)
        self.configure_identity()
        expected = (0x11223344, 0x123456789ABCDEF0)
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with identified_lease(self.path, False, expected) as identity:
                self.assertEqual(identity, expected)
                self.kernel.CloseHandle.assert_not_called()
        self.kernel.CloseHandle.assert_called_once_with(123)

    def test_identity_mismatch(self) -> None:
        """Reject a wrong expected identity and close the acquired handle."""
        self.configure_identity()
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                with identified_lease(self.path, True, (0, 1)):
                    self.fail("Wrong identity admitted")
        self.kernel.CloseHandle.assert_called_once_with(123)

    def test_identity_unsafe(self) -> None:
        """Reject links, directories, reparse attributes and unavailable indices."""
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            for attributes, links, index in ((0x80, 2, 1), (0x10, 1, 1),
                                             (0x400, 1, 1), (0x80, 1, 0)):
                self.configure_identity(attributes, links, index)
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    with identified_lease(self.path, False):
                        self.fail("Unsafe identity admitted")
        self.assertEqual(self.kernel.CloseHandle.call_count, 4)

    def test_identity_query_error(self) -> None:
        """Do not classify native identity query failure as busy."""
        self.kernel.GetFileInformationByHandle.return_value = False
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with patch("windows_maintenance_lease._last_error", return_value=5):
                with self.assertRaises(OSError):
                    with identified_lease(self.path, False):
                        self.fail("Failed identity query admitted")
        self.kernel.CloseHandle.assert_called_once_with(123)

    def test_identity_invalid_expected(self) -> None:
        """Refuse ambiguous or out-of-range expected identities before open."""
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel) as kernel:
            for expected in ((True, 1), (0, 0), (1 << 32, 1), (0, 1 << 64), [0, 1]):
                with self.assertRaisesRegex(ValueError, "Invalid expected"):
                    with identified_lease(self.path, False, expected):
                        self.fail("Invalid expected identity admitted")
        kernel.assert_not_called()

    def test_identity_busy(self) -> None:
        """A sharing violation does not query or close an unacquired handle."""
        self.kernel.CreateFileW.return_value = INVALID_HANDLE
        with patch("windows_maintenance_lease._kernel", return_value=self.kernel):
            with patch("windows_maintenance_lease._last_error", return_value=32):
                with identified_lease(self.path, True, (0, 1)) as identity:
                    self.assertIsNone(identity)
        self.kernel.GetFileInformationByHandle.assert_not_called()
        self.kernel.CloseHandle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
