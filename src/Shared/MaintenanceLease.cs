using System;
using System.IO;

namespace VeyPanel.Shared;

// Prototype only: all participants must use the same provisioned private file.
internal static class MaintenanceLease
{
    internal static FileStream? TryOpen(string path, bool exclusive)
    {
        if (!OperatingSystem.IsWindows())
            throw new PlatformNotSupportedException("Native Windows sharing required.");
        if (!Path.IsPathFullyQualified(path) || Path.GetFullPath(path) != path)
            throw new ArgumentException("Expected a canonical absolute lease path.");
        ValidatePath(path);
        try
        {
            return new FileStream(path, FileMode.Open,
                exclusive ? FileAccess.ReadWrite : FileAccess.Read,
                exclusive ? FileShare.None : FileShare.Read);
        }
        catch (IOException error) when ((error.HResult & 0xffff) == 32)
        {
            // Only a Win32 sharing violation means contention; other errors fail closed.
            return null;
        }
    }

    private static void ValidatePath(string path)
    {
        var attributes = File.GetAttributes(path);
        if ((attributes & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0)
            throw new IOException("Unsafe lease file.");
        for (var directory = Directory.GetParent(path); directory is not null; directory = directory.Parent)
        {
            attributes = directory.Attributes;
            if ((attributes & FileAttributes.Directory) == 0
                || (attributes & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Unsafe lease ancestor.");
        }
    }
}
