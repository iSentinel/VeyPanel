using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Text.RegularExpressions;

/// <summary>
/// Exercises private request data against an owned, published loopback Host.
/// No captured child line or credential is written to the test report.
/// </summary>
internal static class RequestLogPrivacySmoke
{
    private const string BaseUrl = "http://127.0.0.1:47860/";

    /// <summary>Run a bounded real-process privacy and authorization smoke.</summary>
    internal static async Task<int> RunAsync(string directory)
    {
        try
        {
            await VerifyAsync(Path.GetFullPath(directory));
            Console.WriteLine("PASS: request log privacy and authorization");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FAIL: request log privacy ({ex.GetType().Name})");
            return 1;
        }
    }

    private static Process CreateHost(string directory, PrivateCapture capture)
    {
        var info = new ProcessStartInfo(Path.Combine(directory, "VeyPanel.Host.exe"))
        {
            WorkingDirectory = directory, UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true
        };
        info.ArgumentList.Add("--managed-local");
        foreach (var key in new[] { "VEYPANEL_LAN_IP", "VEYPANEL_PFX", "VEYPANEL_PFX_PASSWORD", "VEYPANEL_PERSIST_GRANTS" })
            info.Environment.Remove(key);
        info.Environment["Logging__LogLevel__Default"] = "Trace";
        info.Environment["Logging__LogLevel__Microsoft.AspNetCore"] = "Trace";
        var child = new Process { StartInfo = info };
        child.OutputDataReceived += (_, args) => capture.Observe(args.Data, true);
        child.ErrorDataReceived += (_, args) => capture.Observe(args.Data, false);
        return child;
    }

    private static async Task VerifyAsync(string directory)
    {
        var canary = "fixture-private-" + Guid.NewGuid().ToString("N");
        var capture = new PrivateCapture(canary);
        var negative = new PrivateCapture(canary);
        negative.Observe("synthetic line " + canary, false);
        Require(negative.Leaked, "Privacy observer failed to detect canary");
        using var child = CreateHost(directory, capture);
        if (!child.Start()) throw new InvalidOperationException("Host did not start");
        try
        {
            child.BeginOutputReadLine();
            child.BeginErrorReadLine();
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(50));
            var ct = timeout.Token;
            var token = await capture.Token.Task.WaitAsync(ct);
            using var client = new HttpClient(new HttpClientHandler { UseProxy = false, AllowAutoRedirect = false })
                { BaseAddress = new Uri(BaseUrl), Timeout = TimeSpan.FromSeconds(5) };
            await WaitReadyAsync(client, child, ct);
            await VerifyRequestsAsync(client, token, canary, ct);
            Require(!child.HasExited, "Host stopped unexpectedly");
            child.StandardInput.Close();
            await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(10));
            await Task.WhenAll(capture.OutputEnd.Task, capture.ErrorEnd.Task).WaitAsync(TimeSpan.FromSeconds(5));
            Require(child.ExitCode == 0, "Host did not stop cleanly");
            Require(!capture.Leaked && capture.BootstrapCount == 1, "Private value captured outside bootstrap");
        }
        finally
        {
            if (!child.HasExited)
            {
                child.Kill(entireProcessTree: true);
                await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(10));
            }
        }
    }

    private static async Task WaitReadyAsync(HttpClient client, Process child, CancellationToken ct)
    {
        for (var attempt = 0; attempt < 30; attempt++)
        {
            Require(!child.HasExited, "Host exited before readiness");
            try
            {
                using var response = await client.GetAsync("", ct);
                if (response.StatusCode == HttpStatusCode.OK) return;
            }
            catch (HttpRequestException) { }
            await Task.Delay(200, ct);
        }
        throw new TimeoutException("Host readiness timeout");
    }

    private static async Task VerifyRequestsAsync(HttpClient client, string token, string canary, CancellationToken ct)
    {
        using (var request = new HttpRequestMessage(HttpMethod.Get, "api/v1/telemetry"))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", canary);
            using var response = await client.SendAsync(request, ct);
            Require(response.StatusCode == HttpStatusCode.Unauthorized, "Invalid credential accepted");
        }
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        client.DefaultRequestHeaders.Add("X-VeyPanel-Privacy-Fixture", canary);
        using (var response = await client.GetAsync("api/v1/telemetry?fixture=" + canary, ct))
            Require(response.StatusCode == HttpStatusCode.Forbidden, "Query accepted");
        using (var response = await client.GetAsync("fixture/" + canary, ct))
            Require(response.StatusCode == HttpStatusCode.NotFound, "Unknown path accepted");
        using (var response = await client.GetAsync("api/v1/telemetry", ct))
            Require(response.StatusCode == HttpStatusCode.OK, "Valid telemetry rejected");
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    /// <summary>Keep only a bootstrap token and bounded observation flags.</summary>
    private sealed class PrivateCapture(string canary)
    {
        private static readonly Regex Bootstrap = new(
            @"^Local dashboard: http://127\.0\.0\.1:47860/#token=([A-F0-9]{64})$",
            RegexOptions.CultureInvariant, TimeSpan.FromMilliseconds(100));
        private int leaked;
        private int count;
        internal TaskCompletionSource<string> Token { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
        internal TaskCompletionSource<bool> OutputEnd { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
        internal TaskCompletionSource<bool> ErrorEnd { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
        internal bool Leaked => Volatile.Read(ref leaked) != 0;
        internal int BootstrapCount => Volatile.Read(ref count);

        /// <summary>Check a line without storing or echoing its contents.</summary>
        internal void Observe(string? line, bool stdout)
        {
            if (line is null)
            {
                (stdout ? OutputEnd : ErrorEnd).TrySetResult(true);
                return;
            }
            if (stdout)
            {
                var match = Bootstrap.Match(line);
                if (match.Success)
                {
                    if (Interlocked.Increment(ref count) != 1) Interlocked.Exchange(ref leaked, 1);
                    Token.TrySetResult(match.Groups[1].Value);
                    return;
                }
            }
            if (line.Contains(canary, StringComparison.Ordinal)
                || (Token.Task.IsCompletedSuccessfully && line.Contains(Token.Task.Result, StringComparison.Ordinal)))
                Interlocked.Exchange(ref leaked, 1);
        }
    }
}
