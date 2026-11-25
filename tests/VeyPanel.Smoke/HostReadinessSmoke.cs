using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using VeyPanel.Shared;

internal static class HostReadinessSmoke
{
    internal static async Task<int> RunAsync()
    {
        try
        {
            CheckManagedEnvironment();
            await CheckStatusAsync(200, true);
            await CheckStatusAsync(403, false);
            Console.WriteLine("PASS: Host readiness does not consume response body");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: Host readiness fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static void CheckManagedEnvironment()
    {
        string[] keys = ["VEYPANEL_LAN_IP", "VEYPANEL_PFX", "VEYPANEL_PFX_PASSWORD", "VEYPANEL_PERSIST_GRANTS"];
        var original = keys.Select(Environment.GetEnvironmentVariable).ToArray();
        try
        {
            foreach (var key in keys) Environment.SetEnvironmentVariable(key, "synthetic-fixture");
            var info = HostController.ManagedStartInfo("fixture.exe", Path.GetTempPath());
            if (keys.Any(info.Environment.ContainsKey) || !info.ArgumentList.SequenceEqual(new[] { "--managed-local" })
                || info.UseShellExecute || !info.RedirectStandardInput
                || !info.RedirectStandardOutput || !info.RedirectStandardError)
                throw new InvalidOperationException("Managed environment not isolated.");
            Console.WriteLine("PASS: managed Host excludes inherited LAN, TLS and persistence settings");
        }
        finally
        {
            for (var i = 0; i < keys.Length; i++) Environment.SetEnvironmentVariable(keys[i], original[i]);
        }
    }

    private static async Task CheckStatusAsync(int status, bool expected)
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(8));
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        using var http = new HttpClient(new SocketsHttpHandler
        {
            UseProxy = false, AllowAutoRedirect = false,
            MaxResponseHeadersLength = 16, MaxResponseDrainSize = 0
        }) { Timeout = TimeSpan.FromSeconds(3) };
        var release = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var server = ServeAsync(listener, status, release.Task, deadline.Token);
        try
        {
            var accepted = await HostController.ReadReadyStatusAsync(
                http, new Uri($"http://127.0.0.1:{port}/fixture"), deadline.Token);
            if (accepted != expected || server.IsCompleted)
                throw new InvalidOperationException("Unexpected readiness decision.");
        }
        finally
        {
            release.TrySetResult();
            await server.WaitAsync(deadline.Token);
        }
    }

    private static async Task ServeAsync(TcpListener listener, int status, Task release, CancellationToken cancellation)
    {
        using var client = await listener.AcceptTcpClientAsync(cancellation);
        using var stream = client.GetStream();
        // Read only a bounded request header; no user data, no production endpoint.
        var bytes = new byte[4096];
        var length = 0;
        while (length < bytes.Length)
        {
            if (await stream.ReadAsync(bytes.AsMemory(length, 1), cancellation) != 1)
                throw new IOException("Incomplete fixture request.");
            length++;
            if (length >= 4 && bytes[length-4] == 13 && bytes[length-3] == 10
                && bytes[length-2] == 13 && bytes[length-1] == 10) break;
        }
        if (length == bytes.Length) throw new IOException("Fixture request exceeds budget.");
        var headers = Encoding.ASCII.GetBytes(
            $"HTTP/1.1 {status} Fixture\r\nContent-Length: 1048576\r\nConnection: close\r\n\r\n");
        await stream.WriteAsync(headers, cancellation);
        // Never send the declared body. Only the supervisor releases this fixture.
        await release.WaitAsync(cancellation);
    }
}
