using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

internal static class PersistentHostSmoke
{
    private static readonly Uri Root = new("http://127.0.0.1:47860/");

    internal static async Task<int> RunAsync(string publishDirectory)
    {
        if (!OperatingSystem.IsWindows()) return 2;
        // This explicit test is intended for an isolated CI Windows account.
        var profile = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrEmpty(profile)) return 2;
        var store = Path.Combine(profile, "VeyPanel-GrantStore-v1");
        if (Directory.Exists(store) || File.Exists(store))
        {
            Console.Error.WriteLine("FAIL: persistent smoke refuses an existing store");
            return 2;
        }
        try
        {
            using var http = new HttpClient(new HttpClientHandler { UseProxy = false, AllowAutoRedirect = false })
                { BaseAddress = Root, Timeout = TimeSpan.FromSeconds(4) };
            var exe = Path.Combine(Path.GetFullPath(publishDirectory), "VeyPanel.Host.exe");
            var (id, reader, oldOwner) = await CreateAsync(exe, http);
            await RevokeAfterRestartAsync(exe, http, id, reader, oldOwner);
            await VerifyAfterRevokeAsync(exe, http, reader);
            File.WriteAllBytes(Path.Combine(store, "transaction.pending"), [1]);
            using var blocked = Start(exe, new(TaskCreationOptions.RunContinuationsAsynchronously));
            await blocked.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(15));
            Check(blocked.ExitCode == 1, "Interrupted store refuses process startup");
            Console.WriteLine("PASS: persistent Host restart and fail-closed startup");
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine($"FAIL: persistent Host ({ex.GetType().Name})"); return 1; }
        finally
        {
            if (Directory.Exists(store)) Directory.Delete(store, recursive: true);
        }
    }

    private static async Task<(Guid Id, string Reader, string Owner)> CreateAsync(string exe, HttpClient http)
    {
        var ready = NewSource();
        using var child = Start(exe, ready);
        try
        {
            var owner = await ReadyAsync(child, http, ready);
            using var state = await http.GetAsync("api/v1/devices/status");
            using var status = JsonDocument.Parse(await state.Content.ReadAsByteArrayAsync());
            Check(status.RootElement.GetProperty("storage").GetString() == "protected", "Protected Host mode active");
            using var content = new StringContent("{\"name\":\"CI Tablet\"}", Encoding.UTF8, "application/json");
            using var created = await http.PostAsync("api/v1/devices", content);
            Check(created.StatusCode == HttpStatusCode.Created, "Persistent reader issued");
            using var json = JsonDocument.Parse(await created.Content.ReadAsByteArrayAsync());
            return (json.RootElement.GetProperty("device").GetProperty("id").GetGuid(),
                json.RootElement.GetProperty("token").GetString()!, owner);
        }
        finally { await StopAsync(child); }
    }

    private static async Task RevokeAfterRestartAsync(string exe, HttpClient http, Guid id, string reader, string oldOwner)
    {
        var ready = NewSource();
        using var child = Start(exe, ready);
        try
        {
            var owner = await ReadyAsync(child, http, ready);
            await ExpectAsync(http, oldOwner, HttpStatusCode.Unauthorized, "Old owner rejected after process restart");
            await ExpectAsync(http, reader, HttpStatusCode.OK, "Reader survives process termination/restart");
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", owner);
            using var removed = await http.DeleteAsync($"api/v1/devices/{id}");
            Check(removed.StatusCode == HttpStatusCode.NoContent, "Persistent revocation acknowledged");
        }
        finally { await StopAsync(child); }
    }

    private static async Task VerifyAfterRevokeAsync(string exe, HttpClient http, string reader)
    {
        var ready = NewSource();
        using var child = Start(exe, ready);
        try
        {
            await ReadyAsync(child, http, ready);
            await ExpectAsync(http, reader, HttpStatusCode.Unauthorized, "Revoked reader denied after process restart");
        }
        finally { await StopAsync(child); }
    }

    private static async Task ExpectAsync(HttpClient http, string token, HttpStatusCode expected, string label)
    {
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        using var response = await http.GetAsync("api/v1/telemetry");
        Check(response.StatusCode == expected, label);
    }

    private static TaskCompletionSource<string> NewSource() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    private static Process Start(string exe, TaskCompletionSource<string> ready)
    {
        var info = new ProcessStartInfo(exe) {
            WorkingDirectory = Path.GetDirectoryName(exe)!, UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        info.Environment["VEYPANEL_PERSIST_GRANTS"] = "1";
        foreach (var key in new[] { "VEYPANEL_LAN_IP", "VEYPANEL_PFX", "VEYPANEL_PFX_PASSWORD" })
            info.Environment.Remove(key);
        var child = Process.Start(info) ?? throw new InvalidOperationException("Host start failed");
        child.OutputDataReceived += (_, e) =>
        {
            var match = Regex.Match(e.Data ?? "", @"^Local dashboard: http://127\.0\.0\.1:47860/#token=([A-F0-9]{64})$");
            if (match.Success) ready.TrySetResult(match.Groups[1].Value);
        };
        child.ErrorDataReceived += (_, _) => { }; // Never print child output, which can contain secrets.
        child.BeginOutputReadLine();
        child.BeginErrorReadLine();
        return child;
    }

    private static async Task<string> ReadyAsync(Process child, HttpClient http, TaskCompletionSource<string> ready)
    {
        var owner = await ready.Task.WaitAsync(TimeSpan.FromSeconds(15));
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", owner);
        for (var i = 0; i < 20 && !child.HasExited; i++)
        {
            try
            {
                using var response = await http.GetAsync("api/v1/telemetry");
                if (response.IsSuccessStatusCode && !child.HasExited) return owner;
            }
            catch (HttpRequestException) { }
            await Task.Delay(250);
        }
        throw new InvalidOperationException("Persistent Host not ready");
    }

    private static async Task StopAsync(Process child)
    {
        if (!child.HasExited) child.Kill(entireProcessTree: true);
        await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(10));
    }
    private static void Check(bool pass, string label)
    {
        Console.WriteLine($"{(pass ? "PASS" : "FAIL")}: {label}");
        if (!pass) throw new InvalidOperationException(label);
    }
}
