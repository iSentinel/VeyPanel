using VeyPanel.Shared;

internal static class LifecycleSmoke
{
    internal static async Task<int> RunAsync(string directory)
    {
        try
        {
            await using var host = new HostController(directory);
            await host.StartAsync();
            Check(await host.IsRunningAsync(), "Managed Host started");
            var first = await host.DashboardUrlAsync();
            await host.StartAsync();
            Check(first == await host.DashboardUrlAsync(), "Start idempotent");
            await using (var rival = new HostController(directory))
            {
                var rejected = false;
                try { await rival.StartAsync(); } catch { rejected = true; }
                Check(rejected && await host.IsRunningAsync(), "Port collision preserves owned Host");
            }
            await host.StopAsync();
            Check(!await host.IsRunningAsync(), "Managed Host stopped");
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

    private static void Check(bool condition, string label)
    {
        if (!condition) throw new InvalidOperationException(label);
        Console.WriteLine($"PASS: {label}");
    }
}
