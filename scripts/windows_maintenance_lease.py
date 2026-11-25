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

Identity = tuple[int, int]


class _FileInformation(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in (
        "attributes", "creation_low", "creation_high", "access_low", "access_high",
        "write_low", "write_high", "volume", "size_high", "size_low", "links",
        "index_high", "index_low",
    )]


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
    kernel.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_FileInformation),
    ]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    return kernel


def _last_error() -> int:
    return ctypes.get_last_error()


@contextmanager
def _open_handle(path: Path, exclusive: bool) -> Iterator[tuple[Any, int | None]]:
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
        yield kernel, None
        return
    if handle is None or handle == 0:
        raise OSError("Invalid native lease handle")
    try:
        yield kernel, handle
    finally:
        if not kernel.CloseHandle(handle):
            raise OSError(_last_error(), "Lease close failed")


@contextmanager
def lease(path: Path, exclusive: bool) -> Iterator[bool]:
    """Yield False only for sharing contention; close every acquired handle."""
    with _open_handle(path, exclusive) as (_, handle):
        yield handle is not None


def _read_identity(kernel: Any, handle: int) -> Identity:
    info = _FileInformation()
    if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise OSError(_last_error(), "Lease handle identity unavailable")
    index = (info.index_high << 32) | info.index_low
    if info.attributes & 0x410 or info.links != 1 or index == 0:
        raise ValueError("Unsafe lease handle identity")
    return info.volume, index


def _validate_expected(expected: Identity) -> None:
    if (not isinstance(expected, tuple) or len(expected) != 2
            or any(type(value) is not int for value in expected)
            or not 0 <= expected[0] <= 0xFFFFFFFF
            or not 0 < expected[1] <= 0xFFFFFFFFFFFFFFFF):
        raise ValueError("Invalid expected lease identity")


@contextmanager
def identified_lease(path: Path, exclusive: bool,
                     expected: Identity | None = None) -> Iterator[Identity | None]:
    """Observe a held handle or require a supplied identity; None means busy."""
    if expected is not None:
        _validate_expected(expected)
    with _open_handle(path, exclusive) as (kernel, handle):
        if handle is None:
            yield None
            return
        identity = _read_identity(kernel, handle)
        if expected is not None and identity != expected:
            raise ValueError("Lease handle identity mismatch")
        yield identity
