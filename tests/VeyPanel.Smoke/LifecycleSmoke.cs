using System.Diagnostics;
using System.Reflection;
using VeyPanel.Shared;

internal static class LifecycleSmoke
{
    internal static async Task<int> RunAsync(string directory)
    {
        try
        {
            await using var host = new HostController(directory);
            await host.StartAsync();
            Check(await host.GetStateAsync() == HostLifecycleState.Ready, "Managed Host started");
            var first = await host.DashboardUrlAsync();
            await host.StartAsync();
            Check(first == await host.DashboardUrlAsync(), "Start idempotent");
            await using (var rival = new HostController(directory))
            {
                var rejected = false;
                try { await rival.StartAsync(); } catch { rejected = true; }
                Check(rejected && await host.IsRunningAsync(), "Port collision preserves owned Host");
            }
            await VerifyCleanupRequiredAsync(host);
            await host.StopAsync();
            Check(await host.GetStateAsync() == HostLifecycleState.Stopped, "Managed Host stopped");
            await host.StopAsync();
            await host.StartAsync();
            Check(first != await host.DashboardUrlAsync(), "Restart rotates token");
            await host.DisposeAsync();
            Check(!await host.IsRunningAsync(), "Dispose stops owned Host");
            Console.WriteLine("PASS: managed lifecycle");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FAIL: managed lifecycle ({ex.GetType().Name})");
            return 1;
        }
    }

    // Simulate the cleared-token state of an owned, still-live Host after failed cleanup.
    // No actual Stop failure is injected; the existing owned Host fixture is used.
    private static async Task VerifyCleanupRequiredAsync(HostController host)
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        var processField = typeof(HostController).GetField("process", flags)
            ?? throw new InvalidOperationException("Fixture process field missing.");
        var tokenField = typeof(HostController).GetField("token", flags)
            ?? throw new InvalidOperationException("Fixture token field missing.");
        var owned = processField.GetValue(host) as Process
            ?? throw new InvalidOperationException("Fixture has no owned Host.");
        tokenField.SetValue(host, null);
        Check(await host.GetStateAsync() == HostLifecycleState.CleanupRequired,
            "Live owned Host without readiness requires cleanup");
        var rejected = false;
        try { await host.StartAsync(); }
        catch (InvalidOperationException) { rejected = true; }
        Check(rejected && ReferenceEquals(owned, processField.GetValue(host)) && !owned.HasExited,
            "Start refused without replacing owned Host");
        rejected = false;
        try { _ = await host.DashboardUrlAsync(); }
        catch (InvalidOperationException) { rejected = true; }
        Check(rejected, "Dashboard refused during cleanup");
    }

    private static void Check(bool condition, string label)
    {
        if (!condition) throw new InvalidOperationException(label);
        Console.WriteLine($"PASS: {label}");
    }
}
