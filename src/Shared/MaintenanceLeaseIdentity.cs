using System;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace VeyPanel.Shared;

// Smoke-only identity observation on an already acquired Windows handle.
internal readonly record struct MaintenanceLeaseIdentity(uint Volume, ulong FileIndex)
{
    [StructLayout(LayoutKind.Sequential)]
    private struct FileInformation
    {
        internal uint Attributes;
        internal uint CreationLow, CreationHigh;
        internal uint AccessLow, AccessHigh;
        internal uint WriteLow, WriteHigh;
        internal uint VolumeSerial;
        internal uint SizeHigh, SizeLow;
        internal uint Links;
        internal uint IndexHigh, IndexLow;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileInformationByHandle(
        SafeFileHandle handle, out FileInformation information);

    internal static MaintenanceLeaseIdentity Read(FileStream stream)
    {
        if (!OperatingSystem.IsWindows())
            throw new PlatformNotSupportedException("Native Windows file identity required.");
        if (!GetFileInformationByHandle(stream.SafeFileHandle, out var info))
            throw new IOException("Lease file identity unavailable.");
        if ((info.Attributes & (uint)(FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0
            || info.Links != 1)
            throw new IOException("Unsafe lease file identity.");
        var index = ((ulong)info.IndexHigh << 32) | info.IndexLow;
        if (index == 0) throw new IOException("Lease file index unavailable.");
        return new MaintenanceLeaseIdentity(info.VolumeSerial, index);
    }
}
