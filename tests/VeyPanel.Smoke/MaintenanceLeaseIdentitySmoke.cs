using System.Runtime.InteropServices;
using VeyPanel.Shared;

internal static class MaintenanceLeaseIdentitySmoke
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CreateHardLinkW(string link, string existing, IntPtr reserved);

    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) return 1;
        try
        {
            var root = Directory.CreateTempSubdirectory("veypanel-identity-");
            var path = Path.Combine(root.FullName, "lease.fixture");
            var replacement = Path.Combine(root.FullName, "replacement.fixture");
            var link = Path.Combine(root.FullName, "alias.fixture");
            try
            {
                File.WriteAllBytes(path, [0x56, 0x50]);
                File.WriteAllBytes(replacement, [0x56, 0x50]);
                var original = CheckHeldIdentity(path, replacement);
                CheckHardLink(path, link);
                File.Move(replacement, path, overwrite: true);
                using var current = MaintenanceLease.TryOpen(path, false)
                    ?? throw new InvalidOperationException("Replacement lease unavailable.");
                Require(MaintenanceLeaseIdentity.Read(current) != original, "Replacement changes handle identity");
                Console.WriteLine("PASS: isolated maintenance lease identity");
                return 0;
            }
            finally
            {
                // Only unique inert fixture files; no installed tree is touched.
                File.Delete(link);
                File.Delete(replacement);
                File.Delete(path);
                root.Delete();
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: maintenance identity fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static MaintenanceLeaseIdentity CheckHeldIdentity(string path, string replacement)
    {
        using var first = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("Shared fixture unavailable.");
        using var second = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("Second fixture unavailable.");
        var original = MaintenanceLeaseIdentity.Read(first);
        Require(original == MaintenanceLeaseIdentity.Read(second), "Shared handles identify the same file");
        Require(Refused(() => File.Move(replacement, path, overwrite: true)),
            "Held runtime lease blocks file replacement");
        Require(Refused(() => File.Delete(path)), "Held runtime lease blocks file deletion");
        Require(original == MaintenanceLeaseIdentity.Read(first), "Held identity unchanged");
        Require(File.Exists(path) && File.Exists(replacement), "Both fixture names retained");
        return original;
    }

    private static void CheckHardLink(string path, string link)
    {
        if (!CreateHardLinkW(link, path, IntPtr.Zero))
            throw new IOException("Isolated hard-link fixture unavailable.");
        using (var lease = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("Aliased fixture unavailable."))
        {
            Require(Refused(() => { _ = MaintenanceLeaseIdentity.Read(lease); }),
                "Multiple-link file rejected by handle identity check");
        }
        File.Delete(link);
        using var single = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("Single-link fixture unavailable.");
        _ = MaintenanceLeaseIdentity.Read(single);
        Console.WriteLine("PASS: single-link identity accepted after alias removal");
    }

    private static bool Refused(Action action)
    {
        try { action(); return false; }
        catch (IOException) { return true; }
        catch (UnauthorizedAccessException) { return true; }
    }

    private static void Require(bool value, string label)
    {
        if (!value) throw new InvalidOperationException(label);
        Console.WriteLine("PASS: " + label);
    }
}
