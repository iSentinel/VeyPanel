using System.Diagnostics;
using System.Reflection;
using VeyPanel.Shared;

// All paths and processes belong to this isolated inert smoke fixture.
internal static class MaintenanceLeaseSmoke
{
    private const string Prefix = "veypanel-lease-";
    private const string LeaseName = "admission.fixture";

    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) return 1;
        try
        {
            var root = Directory.CreateTempSubdirectory(Prefix);
            var path = Path.Combine(root.FullName, LeaseName);
            try
            {
                File.WriteAllBytes(path, [0x56, 0x50]);
                CheckSharing(path);
                CheckExclusive(path);
                Require(RunChild(path, "exclusive-exit") == 0, "Owned lease process exited without Dispose");
                using (var recovered = MaintenanceLease.TryOpen(path, true))
                    Require(recovered is not null, "Lease available after process exit");
                Require(File.ReadAllBytes(path).SequenceEqual(new byte[] { 0x56, 0x50 }), "Lease bytes unchanged");
                CheckMissing(root.FullName);
                Console.WriteLine("PASS: isolated maintenance sharing lease");
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
            Console.Error.WriteLine("FAIL: maintenance sharing fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static void CheckSharing(string path)
    {
        using var desktop = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("First shared lease refused.");
        using (var host = MaintenanceLease.TryOpen(path, false)
            ?? throw new InvalidOperationException("Second shared lease refused."))
        {
            Require(RunChild(path, "shared") == 0, "Cross-process shared runtime admitted");
            Require(RunChild(path, "exclusive") == 2, "Maintenance refused during shared runtime");
        }
        Require(RunChild(path, "exclusive") == 2, "Remaining runtime lease blocks maintenance");
    }

    private static void CheckExclusive(string path)
    {
        using (var maintenance = MaintenanceLease.TryOpen(path, true)
            ?? throw new InvalidOperationException("Exclusive lease refused."))
        {
            Require(RunChild(path, "shared") == 2, "Exclusive lease blocks new runtime");
            Require(RunChild(path, "exclusive") == 2, "Exclusive lease blocks other maintenance");
        }
        Require(RunChild(path, "shared") == 0, "Runtime admitted after maintenance release");
    }

    private static void CheckMissing(string root)
    {
        var missing = Path.Combine(root, "missing.fixture");
        try
        {
            using var unexpected = MaintenanceLease.TryOpen(missing, true);
            throw new InvalidOperationException("Missing lease accepted.");
        }
        catch (FileNotFoundException) { }
        Require(!File.Exists(missing), "Missing lease fails closed without creating file");
    }

    internal static int Probe(string path, string mode)
    {
        if (!OperatingSystem.IsWindows()
            || mode is not ("shared" or "exclusive" or "exclusive-exit")
            || !Path.IsPathFullyQualified(path) || Path.GetFullPath(path) != path
            || Path.GetFileName(path) != LeaseName) return 1;
        var parent = Directory.GetParent(path);
        if (parent is null || !parent.Name.StartsWith(Prefix, StringComparison.Ordinal)
            || !string.Equals(parent.Parent?.FullName,
                Path.TrimEndingDirectorySeparator(Path.GetFullPath(Path.GetTempPath())),
                StringComparison.OrdinalIgnoreCase)) return 1;
        using var lease = MaintenanceLease.TryOpen(path, mode != "shared");
        if (lease is null) return 2;
        if (mode == "exclusive-exit") Environment.Exit(0);
        return 0;
    }

    private static int RunChild(string path, string mode)
    {
        var executable = Environment.ProcessPath
            ?? throw new InvalidOperationException("Smoke executable unavailable.");
        var info = new ProcessStartInfo(executable) { UseShellExecute = false, CreateNoWindow = true };
        if (string.Equals(Path.GetFileNameWithoutExtension(executable), "dotnet",
            StringComparison.OrdinalIgnoreCase))
            info.ArgumentList.Add(Assembly.GetExecutingAssembly().Location);
        info.ArgumentList.Add("--maintenance-lease-probe");
        info.ArgumentList.Add(path);
        info.ArgumentList.Add(mode);
        using var child = Process.Start(info)
            ?? throw new InvalidOperationException("Fixture process unavailable.");
        if (!child.WaitForExit(10000))
        {
            try { child.Kill(); }
            catch (InvalidOperationException) when (child.HasExited) { }
            if (!child.WaitForExit(5000))
                throw new InvalidOperationException("Owned fixture exit not confirmed.");
            throw new TimeoutException("Maintenance lease fixture timed out.");
        }
        return child.ExitCode;
    }

    private static void Require(bool value, string label)
    {
        if (!value) throw new InvalidOperationException(label);
        Console.WriteLine("PASS: " + label);
    }
}
