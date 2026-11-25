using System.Diagnostics;
using VeyPanel.Shared;

// Separate inert fixture: C# owns the handle and Python is the contender.
internal static class MaintenanceLeaseReverseSmoke
{
    internal static int Run(string python, string script)
    {
        if (!OperatingSystem.IsWindows()) return 1;
        try
        {
            var root = Directory.CreateTempSubdirectory("veypanel-lease-");
            var path = Path.Combine(root.FullName, "admission.fixture");
            try
            {
                File.WriteAllBytes(path, [0x56, 0x50]);
                Check(python, script, path, "shared", 0);
                Check(python, script, path, "exclusive", 0);
                using (var runtime = MaintenanceLease.TryOpen(path, false)
                    ?? throw new InvalidOperationException("Shared fixture unavailable."))
                {
                    Check(python, script, path, "shared", 0);
                    Check(python, script, path, "exclusive", 2);
                    Console.WriteLine("PASS: C# shared lease admits Python runtime and blocks maintenance");
                }
                using (var maintenance = MaintenanceLease.TryOpen(path, true)
                    ?? throw new InvalidOperationException("Exclusive fixture unavailable."))
                {
                    Check(python, script, path, "shared", 2);
                    Check(python, script, path, "exclusive", 2);
                    Console.WriteLine("PASS: C# exclusive lease blocks Python runtime and maintenance");
                }
                Check(python, script, path, "shared", 0);
                Check(python, script, path, "exclusive", 0);
                if (!File.ReadAllBytes(path).SequenceEqual(new byte[] { 0x56, 0x50 }))
                    throw new InvalidOperationException("Fixture bytes changed.");
                Console.WriteLine("PASS: reverse cross-language lease release and unchanged bytes");
                return 0;
            }
            finally
            {
                File.Delete(path);
                root.Delete();
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: reverse lease fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static void Check(string python, string script, string path, string mode, int expected)
    {
        if (!Path.IsPathFullyQualified(python) || !Path.IsPathFullyQualified(script)
            || Path.GetFileName(script) != "probe_maintenance_lease.py")
            throw new ArgumentException("Expected trusted absolute fixture commands.");
        var info = new ProcessStartInfo(python) { UseShellExecute = false, CreateNoWindow = true };
        info.ArgumentList.Add("-B");
        info.ArgumentList.Add(script);
        info.ArgumentList.Add(path);
        info.ArgumentList.Add(mode);
        var temporary = Directory.GetParent(path)?.Parent?.FullName
            ?? throw new InvalidOperationException("Fixture parent unavailable.");
        info.Environment["TEMP"] = temporary;
        info.Environment["TMP"] = temporary;
        using var child = Process.Start(info)
            ?? throw new InvalidOperationException("Fixture contender unavailable.");
        if (!child.WaitForExit(15000))
        {
            try { child.Kill(); }
            catch (InvalidOperationException) when (child.HasExited) { }
            if (!child.WaitForExit(5000))
                throw new InvalidOperationException("Owned contender exit not confirmed.");
            throw new TimeoutException("Fixture contender timed out.");
        }
        if (child.ExitCode != expected)
        {
            Console.Error.WriteLine($"FAIL: Python contender mode={mode} expected={expected} actual={child.ExitCode}");
            throw new InvalidOperationException("Unexpected fixture contender result.");
        }
    }
}
