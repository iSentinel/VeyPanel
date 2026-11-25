using System.Diagnostics;
using System.Reflection;
using VeyPanel.Shared;

internal static class DesktopAdmissionSmoke
{
    private const string FixturePrefix = @"Local\VeyPanel.Desktop.Fixture.";

    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) return 1;
        var name = FixturePrefix + Guid.NewGuid().ToString("N");
        try
        {
            using (var owner = DesktopSessionAdmission.TryAcquire(name)
                ?? throw new InvalidOperationException("Initial admission refused."))
            {
                Require(!AcquireOnOtherThread(name), "Competing thread refused");
                var wrongThread = Task.Run(() =>
                {
                    try { owner.Dispose(); return false; }
                    catch (InvalidOperationException) { return true; }
                });
                Require(wrongThread.WaitAsync(TimeSpan.FromSeconds(5)).GetAwaiter().GetResult(),
                    "Nonowner release refused");
                Require(!AcquireOnOtherThread(name), "Owner remains admitted");
                Require(RunChild(name, "normal") == 2, "Competing process refused");
            }
            Require(AcquireOnOtherThread(name), "Admission after owner release");
            Require(RunChild(name, "normal") == 0, "Process admitted after release");
            CheckAbandonment();
            Console.WriteLine("PASS: Desktop session admission");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: Desktop session admission (" + error.GetType().Name + ")");
            return 1;
        }
    }

    // Keep a non-owning kernel handle alive so process exit cannot destroy the test object.
    private static void CheckAbandonment()
    {
        var name = FixturePrefix + Guid.NewGuid().ToString("N");
        using var observer = new Mutex(false, name);
        Require(RunChild(name, "abandon") == 0, "Owned fixture exited without release");
        using var recovered = DesktopSessionAdmission.TryAcquire(name);
        Require(recovered is not null, "Admission after abandoned process");
        Require(RunChild(name, "normal") == 2, "Recovered owner excludes contender");
    }

    internal static int Probe(string name, string mode)
    {
        if (!OperatingSystem.IsWindows() || !name.StartsWith(FixturePrefix, StringComparison.Ordinal)
            || !Guid.TryParseExact(name[FixturePrefix.Length..], "N", out _)
            || mode is not ("normal" or "abandon")) return 1;
        using var owner = DesktopSessionAdmission.TryAcquire(name);
        if (owner is null) return 2;
        // Intentional exit without Dispose, only on the unique inert CI fixture.
        if (mode == "abandon") Environment.Exit(0);
        return 0;
    }

    private static int RunChild(string name, string mode)
    {
        var executable = Environment.ProcessPath
            ?? throw new InvalidOperationException("Smoke executable unavailable.");
        var info = new ProcessStartInfo(executable) { UseShellExecute = false, CreateNoWindow = true };
        if (string.Equals(Path.GetFileNameWithoutExtension(executable), "dotnet",
            StringComparison.OrdinalIgnoreCase))
            info.ArgumentList.Add(Assembly.GetExecutingAssembly().Location);
        info.ArgumentList.Add("--desktop-admission-probe");
        info.ArgumentList.Add(name);
        info.ArgumentList.Add(mode);
        using var child = Process.Start(info)
            ?? throw new InvalidOperationException("Fixture process did not start.");
        if (!child.WaitForExit(10000))
        {
            try { child.Kill(); }
            catch (InvalidOperationException) when (child.HasExited) { }
            if (!child.WaitForExit(5000))
                throw new InvalidOperationException("Owned fixture exit not confirmed.");
            throw new TimeoutException("Desktop admission fixture timed out.");
        }
        return child.ExitCode;
    }

    private static bool AcquireOnOtherThread(string name)
    {
        return Task.Run(() =>
        {
            using var contender = DesktopSessionAdmission.TryAcquire(name);
            return contender is not null;
        }).WaitAsync(TimeSpan.FromSeconds(5)).GetAwaiter().GetResult();
    }

    private static void Require(bool value, string label)
    {
        if (!value) throw new InvalidOperationException(label);
        Console.WriteLine("PASS: " + label);
    }
}
