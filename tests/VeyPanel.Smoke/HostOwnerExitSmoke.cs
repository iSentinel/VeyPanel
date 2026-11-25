using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using VeyPanel.Shared;

// Isolated Windows CI fixture: observe the real managed Host after its owner exits.
internal static class HostOwnerExitSmoke
{
    internal static async Task<int> RunAsync(string directory)
    {
        if (!OperatingSystem.IsWindows()) return 1;
        try
        {
            using var owner = StartOwner(Path.GetFullPath(directory));
            var drain = owner.StandardError.BaseStream.CopyToAsync(Stream.Null);
            try
            {
                var line = await owner.StandardOutput.ReadLineAsync().WaitAsync(TimeSpan.FromSeconds(35));
                using var host = OpenObservedHost(directory, line);
                await owner.StandardInput.WriteLineAsync("EXIT_FIXTURE");
                owner.StandardInput.Close();
                await owner.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(10));
                if (owner.ExitCode != 0) throw new InvalidOperationException("Fixture owner exit failed.");
                await host.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(15));
                if (host.ExitCode != 0) throw new InvalidOperationException("Managed Host exit failed.");
                Console.WriteLine("PASS: managed Host exits after fixture owner disappears");
            }
            finally
            {
                await CleanupOwnerAsync(owner);
                await drain.WaitAsync(TimeSpan.FromSeconds(5));
            }
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: Host owner exit fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static Process StartOwner(string directory)
    {
        var executable = Environment.ProcessPath
            ?? throw new InvalidOperationException("Smoke executable unavailable.");
        var info = new ProcessStartInfo(executable)
        {
            UseShellExecute = false, CreateNoWindow = true, RedirectStandardInput = true,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        if (string.Equals(Path.GetFileNameWithoutExtension(executable), "dotnet",
            StringComparison.OrdinalIgnoreCase))
            info.ArgumentList.Add(Assembly.GetExecutingAssembly().Location);
        info.ArgumentList.Add("--host-owner-exit-probe");
        info.ArgumentList.Add(directory);
        return Process.Start(info) ?? throw new InvalidOperationException("Fixture owner unavailable.");
    }

    private static Process OpenObservedHost(string directory, string? line)
    {
        var parts = line?.Split(' ');
        if (parts is not { Length: 3 } || parts[0] != "OWNED_FIXTURE"
            || !int.TryParse(parts[1], NumberStyles.None, CultureInfo.InvariantCulture, out var pid)
            || pid <= 0 || !long.TryParse(parts[2], NumberStyles.None, CultureInfo.InvariantCulture, out var ticks))
            throw new InvalidOperationException("Invalid private fixture identity.");
        var process = Process.GetProcessById(pid);
        try
        {
            // Retain the actual process handle before allowing the owner to exit.
            _ = process.Handle;
            var expected = Path.GetFullPath(Path.Combine(directory, "VeyPanel.Host.exe"));
            if (process.HasExited || process.StartTime.ToUniversalTime().Ticks != ticks
                || !string.Equals(process.MainModule?.FileName, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Fixture identity mismatch.");
            return process;
        }
        catch { process.Dispose(); throw; }
    }

    private static async Task CleanupOwnerAsync(Process owner)
    {
        if (owner.HasExited) return;
        try { owner.StandardInput.Close(); }
        catch (IOException) { }
        try { await owner.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(15)); }
        catch (TimeoutException)
        {
            // Only the directly started smoke owner; never terminate by observed Host PID.
            if (!owner.HasExited) owner.Kill();
            await owner.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(5));
            throw;
        }
    }

    internal static async Task<int> ProbeAsync(string directory)
    {
        if (!OperatingSystem.IsWindows() || !Console.IsInputRedirected || !Console.IsOutputRedirected)
            return 1;
        try
        {
            await using var controller = new HostController(directory);
            await controller.StartAsync();
            var field = typeof(HostController).GetField("process", BindingFlags.Instance | BindingFlags.NonPublic)
                ?? throw new InvalidOperationException("Fixture process field unavailable.");
            var host = field.GetValue(controller) as Process
                ?? throw new InvalidOperationException("Fixture owned Host unavailable.");
            Console.WriteLine(FormattableString.Invariant(
                $"OWNED_FIXTURE {host.Id} {host.StartTime.ToUniversalTime().Ticks}"));
            Console.Out.Flush();
            var command = await Console.In.ReadLineAsync().WaitAsync(TimeSpan.FromSeconds(20));
            if (command != "EXIT_FIXTURE") return 1;
            // Deliberately leave only the synthetic owner without running Dispose.
            // The real managed Host must observe EOF on its own stdin.
            Environment.Exit(0);
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: Host owner fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }
}
