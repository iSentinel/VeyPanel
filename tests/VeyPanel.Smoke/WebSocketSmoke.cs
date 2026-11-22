using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using VeyPanel.Shared;

internal static class WebSocketSmoke
{
    private static readonly Uri Endpoint = new("ws://127.0.0.1:47860/api/v1/telemetry/ws");
    internal static async Task<int> RunAsync(string directory)
    {
        try
        {
            await using var host = new HostController(directory);
            await host.StartAsync();
            var token = (await host.DashboardUrlAsync()).Split("#token=")[1];
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(30));
            var ct = deadline.Token;
            await RejectedOrigin(ct);
            await RejectedToken(ct);
            await ValidSession(token, ct);
            await ValidSession(token, ct);
            await host.StopAsync();
            Console.WriteLine("PASS: WebSocket authorization, samples, reconnect and shutdown");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FAIL: WebSocket smoke ({ex.GetType().Name})");
            return 1;
        }
    }

    private static ClientWebSocket Client(string origin)
    {
        var socket = new ClientWebSocket();
        socket.Options.SetRequestHeader("Origin", origin);
        return socket;
    }

    private static async Task RejectedOrigin(CancellationToken ct)
    {
        using var socket = Client("http://example.invalid");
        try { await socket.ConnectAsync(Endpoint, ct); }
        catch (WebSocketException) { Console.WriteLine("PASS: cross-origin upgrade rejected"); return; }
        throw new InvalidOperationException("Foreign origin accepted.");
    }

    private static async Task RejectedToken(CancellationToken ct)
    {
        using var socket = Client("http://127.0.0.1:47860");
        await socket.ConnectAsync(Endpoint, ct);
        await socket.SendAsync(Encoding.ASCII.GetBytes(new string('0', 64)).AsMemory(), WebSocketMessageType.Text, true, ct);
        var result = await socket.ReceiveAsync(new byte[1024].AsMemory(), ct);
        if (result.MessageType != WebSocketMessageType.Close || socket.CloseStatus != WebSocketCloseStatus.PolicyViolation)
            throw new InvalidOperationException("Unauthenticated telemetry leaked.");
        Console.WriteLine("PASS: wrong token rejected before telemetry");
    }

    private static async Task ValidSession(string token, CancellationToken ct)
    {
        using var socket = Client("http://127.0.0.1:47860");
        await socket.ConnectAsync(Endpoint, ct);
        await socket.SendAsync(Encoding.ASCII.GetBytes(token).AsMemory(), WebSocketMessageType.Text, true, ct);
        var first = await ReadSample(socket, ct);
        DateTimeOffset next = first;
        for (var i = 0; i < 4 && next <= first; i++) next = await ReadSample(socket, ct);
        if (next <= first) throw new InvalidOperationException("Samples did not advance.");
        await socket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "", ct);
        Console.WriteLine("PASS: authorized advancing telemetry");
    }

    private static async Task<DateTimeOffset> ReadSample(ClientWebSocket socket, CancellationToken ct)
    {
        var buffer = new byte[16384];
        using var stream = new MemoryStream();
        ValueWebSocketReceiveResult result;
        do
        {
            result = await socket.ReceiveAsync(buffer.AsMemory(), ct);
            if (result.MessageType != WebSocketMessageType.Text || stream.Length + result.Count > 1024 * 1024)
                throw new InvalidOperationException("Unexpected frame.");
            stream.Write(buffer, 0, result.Count);
        } while (!result.EndOfMessage);
        using var json = JsonDocument.Parse(stream.ToArray());
        return json.RootElement.GetProperty("timestampUtc").GetDateTimeOffset();
    }
}
