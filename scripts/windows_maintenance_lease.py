"""Prototype Windows sharing lease; never create or write the lease file."""

from collections.abc import Iterator
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from pathlib import Path
import sys
from typing import Any

from windows_package_selection import plain, root_path

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 1
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE = ctypes.c_void_p(-1).value
SHARING_VIOLATION = 32


def _kernel() -> Any:
    if sys.platform != "win32":
        raise RuntimeError("Native Windows sharing required")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _last_error() -> int:
    return ctypes.get_last_error()


@contextmanager
def lease(path: Path, exclusive: bool) -> Iterator[bool]:
    """Yield False only for sharing contention; close every acquired handle."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Expected absolute lease path without traversal")
    root_path(path.parent)
    plain(path)
    kernel = _kernel()
    access = GENERIC_READ | GENERIC_WRITE if exclusive else GENERIC_READ
    share = 0 if exclusive else FILE_SHARE_READ
    handle = kernel.CreateFileW(str(path), access, share, None, OPEN_EXISTING,
                                FILE_ATTRIBUTE_NORMAL, None)
    if handle == INVALID_HANDLE:
        error = _last_error()
        if error != SHARING_VIOLATION:
            raise OSError(error, "Lease open failed")
        yield False
        return
    if handle is None or handle == 0:
        raise OSError("Invalid native lease handle")
    try:
        yield True
    finally:
        if not kernel.CloseHandle(handle):
            raise OSError(_last_error(), "Lease close failed")
