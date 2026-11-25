using System;
using System.Diagnostics;
using System.ComponentModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace VeyPanel.Shared;

internal enum HostLifecycleState { Stopped, Ready, CleanupRequired }

// All mutations serialized by gate. Only the process started here can be stopped.
internal sealed class HostController : IAsyncDisposable
{
    private readonly SemaphoreSlim gate = new(1, 1);
    private readonly string directory;
    private Process? process;
    private string? token;
    private bool disposed;

    internal HostController(string directory) => this.directory = Path.GetFullPath(directory);

    private HostLifecycleState State()
    {
        if (process is null) return HostLifecycleState.Stopped;
        try
        {
            if (process.HasExited) return HostLifecycleState.Stopped;
            return token is null ? HostLifecycleState.CleanupRequired : HostLifecycleState.Ready;
        }
        catch (Exception error) when (error is InvalidOperationException or Win32Exception)
        {
            // A failed observation is not proof that the owned process exited.
            return HostLifecycleState.CleanupRequired;
        }
    }

    internal async Task StartAsync()
    {
        await gate.WaitAsync();
        try
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            var state = State();
            if (state == HostLifecycleState.Ready) return;
            if (state == HostLifecycleState.CleanupRequired)
                throw new InvalidOperationException("Owned Host cleanup required; stop before starting.");
            await StopCoreAsync();
            var exe = Path.Combine(directory, "VeyPanel.Host.exe");
            if (!File.Exists(exe)) throw new FileNotFoundException("Bundled Host is missing.");
            var ready = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            var info = new ProcessStartInfo(exe) {
                WorkingDirectory = directory, UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true
            };
            info.ArgumentList.Add("--managed-local");
            foreach (var key in new[] { "VEYPANEL_LAN_IP", "VEYPANEL_PFX", "VEYPANEL_PFX_PASSWORD" })
                info.Environment.Remove(key);
            var child = new Process { StartInfo = info, EnableRaisingEvents = true };
            child.OutputDataReceived += (_, args) =>
            {
                var match = Regex.Match(args.Data ?? "", @"^Local dashboard: http://127\.0\.0\.1:47860/#token=([A-F0-9]{64})$");
                if (match.Success) ready.TrySetResult(match.Groups[1].Value);
            };
            child.ErrorDataReceived += (_, _) => { }; // Do not persist potentially sensitive output.
            child.Exited += (_, _) => ready.TrySetException(new InvalidOperationException("Host exited."));
            try
            {
                if (!child.Start()) throw new InvalidOperationException("Host failed to start.");
                process = child;
                child.BeginOutputReadLine();
                child.BeginErrorReadLine();
                var candidate = await ready.Task.WaitAsync(TimeSpan.FromSeconds(15));
                await CheckReadyAsync(child, candidate);
                token = candidate;
            }
            catch
            {
                if (process == child) await StopCoreAsync();
                else child.Dispose();
                throw;
            }
        }
        finally { gate.Release(); }
    }

    private static async Task CheckReadyAsync(Process child, string candidate)
    {
        using var http = new HttpClient(new HttpClientHandler { UseProxy = false, AllowAutoRedirect = false })
            { Timeout = TimeSpan.FromSeconds(1) };
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", candidate);
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        while (!deadline.IsCancellationRequested && !child.HasExited)
        {
            try
            {
                using var response = await http.GetAsync("http://127.0.0.1:47860/api/v1/telemetry", deadline.Token);
                if (response.StatusCode == HttpStatusCode.OK && !child.HasExited) return;
            }
            catch (HttpRequestException) { }
            catch (OperationCanceledException) when (!deadline.IsCancellationRequested) { }
            await Task.Delay(200, deadline.Token);
        }
        throw new InvalidOperationException("Owned Host did not become ready.");
    }

    internal async Task StopAsync()
    {
        await gate.WaitAsync();
        try { await StopCoreAsync(); }
        finally { gate.Release(); }
    }

    private async Task StopCoreAsync()
    {
        token = null;
        var child = process;
        if (child is null) return;
        if (!child.HasExited)
        {
            try
            {
                child.StandardInput.Close();
                await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(5));
            }
            catch (Exception ex) when (ex is TimeoutException or IOException or InvalidOperationException)
            {
                if (!child.HasExited) child.Kill(entireProcessTree: true);
                await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(5));
            }
        }
        process = null;
        child.Dispose();
    }

    internal async Task<string> DashboardUrlAsync()
    {
        await gate.WaitAsync();
        try
        {
            if (State() != HostLifecycleState.Ready) throw new InvalidOperationException("Host is not ready.");
            return $"http://127.0.0.1:47860/#token={token}";
        }
        finally { gate.Release(); }
    }

    internal async Task<HostLifecycleState> GetStateAsync()
    {
        await gate.WaitAsync();
        try { return State(); }
        finally { gate.Release(); }
    }

    internal async Task<bool> IsRunningAsync() => await GetStateAsync() == HostLifecycleState.Ready;

    public async ValueTask DisposeAsync()
    {
        await gate.WaitAsync();
        try { await StopCoreAsync(); disposed = true; }
        finally { gate.Release(); }
    }
}
