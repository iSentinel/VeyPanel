using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text.Json;

namespace VeyPanel.Host;

internal sealed class TelemetrySocket(DeviceRegistry registry, string? lan, JsonSerializerOptions json)
{
    internal const int Capacity = 8;
    internal const int MaxPayloadBytes = 1024 * 1024;

    internal static bool PayloadAllowed(int length) => length > 0 && length <= MaxPayloadBytes;
    private readonly SemaphoreSlim slots = new(Capacity, Capacity);

    internal static bool OriginAllowed(string? origin, bool https, string? lan)
    {
        // Native clients may omit Origin. Browser clients must match the explicit listener.
        if (origin is null) return true;
        var expected = https && lan is not null ? $"https://{lan}:47861" : "http://127.0.0.1:47860";
        return (!https || lan is not null) && string.Equals(origin, expected, StringComparison.OrdinalIgnoreCase);
    }

    internal async Task HandleAsync(HttpContext context, Telemetry telemetry, IHostApplicationLifetime lifetime)
    {
        if (!context.WebSockets.IsWebSocketRequest || context.Request.QueryString.HasValue)
        { context.Response.StatusCode = 400; return; }
        var origins = context.Request.Headers.Origin;
        if (origins.Count > 1 || !OriginAllowed(origins.Count == 0 ? null : origins[0], context.Request.IsHttps, lan))
        { context.Response.StatusCode = 403; return; }
        if (!slots.Wait(0))
        { context.Response.StatusCode = 503; return; }
        try
        {
            using var socket = await context.WebSockets.AcceptWebSocketAsync();
            using var stop = CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted, lifetime.ApplicationStopping);
            var grant = await AuthenticateAsync(socket, DeviceRegistry.LocalOwner(context), stop.Token);
            if (grant is null)
            {
                await CloseAsync(socket, WebSocketCloseStatus.PolicyViolation, "Authentication required");
                return;
            }
            await StreamAsync(socket, telemetry, grant, stop);
        }
        catch (Exception ex) when (ex is WebSocketException or OperationCanceledException or IOException)
        { /* Untrusted disconnects and payloads are never logged. */ }
        finally { slots.Release(); }
    }

    private async Task<DeviceGrant?> AuthenticateAsync(WebSocket socket, bool local, CancellationToken ct)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeout.CancelAfter(TimeSpan.FromSeconds(5));
        var buffer = new byte[65];
        try
        {
            var message = await socket.ReceiveAsync(buffer.AsMemory(), timeout.Token);
            return message.MessageType == WebSocketMessageType.Text && message.EndOfMessage
                ? registry.Authenticate(buffer.AsSpan(0, message.Count), local, DateTimeOffset.UtcNow) : null;
        }
        catch (OperationCanceledException) { return null; }
        finally { CryptographicOperations.ZeroMemory(buffer); }
    }

    private async Task StreamAsync(WebSocket socket, Telemetry telemetry, DeviceGrant grant, CancellationTokenSource stop)
    {
        var peer = ObservePeerAsync(socket, stop);
        try
        {
            using var timer = new PeriodicTimer(TimeSpan.FromSeconds(1));
            do
            {
                if (socket.State != WebSocketState.Open || !registry.Active(grant, DateTimeOffset.UtcNow)) break;
                var payload = JsonSerializer.SerializeToUtf8Bytes(telemetry.Latest, json);
                if (!PayloadAllowed(payload.Length))
                {
                    await CloseAsync(socket, WebSocketCloseStatus.MessageTooBig, "Telemetry size limit");
                    break;
                }
                using var send = CancellationTokenSource.CreateLinkedTokenSource(stop.Token);
                send.CancelAfter(TimeSpan.FromSeconds(3));
                await socket.SendAsync(payload.AsMemory(), WebSocketMessageType.Text, true, send.Token);
            } while (await timer.WaitForNextTickAsync(stop.Token));
        }
        catch (Exception ex) when (ex is OperationCanceledException or WebSocketException or IOException) { }
        finally
        {
            stop.Cancel();
            await peer;
            await CloseAsync(socket, WebSocketCloseStatus.NormalClosure, "Telemetry ended");
        }
    }

    private static async Task ObservePeerAsync(WebSocket socket, CancellationTokenSource stop)
    {
        try
        {
            // Any extra application message ends the read-only session.
            await socket.ReceiveAsync(new byte[1].AsMemory(), stop.Token);
        }
        catch (Exception ex) when (ex is OperationCanceledException or WebSocketException or IOException) { }
        finally { stop.Cancel(); }
    }

    private static async Task CloseAsync(WebSocket socket, WebSocketCloseStatus status, string reason)
    {
        if (socket.State is not (WebSocketState.Open or WebSocketState.CloseReceived)) return;
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(1));
        try { await socket.CloseOutputAsync(status, reason, timeout.Token); }
        catch (Exception ex) when (ex is OperationCanceledException or WebSocketException or IOException) { socket.Abort(); }
    }
}
