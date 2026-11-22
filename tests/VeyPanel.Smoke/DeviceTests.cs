using System.Text;
using System.Net;
using System.Net.Http.Headers;
using System.Net.WebSockets;
using System.Text.Json;
using VeyPanel.Host;
using VeyPanel.Shared;

internal static class DeviceTests
{
    internal static int Run()
    {
        var now = DateTimeOffset.UtcNow;
        var owner = new string('A', 64);
        var registry = new DeviceRegistry(owner);
        var issued = registry.Issue("Tablet", now)!;
        var bytes = Encoding.ASCII.GetBytes(issued.Token);
        var grant = registry.Authenticate(bytes, false, now);
        var valid = grant is { Owner: false } && registry.Authenticate(Encoding.ASCII.GetBytes(owner), false, now) is null
            && registry.Authenticate(Encoding.ASCII.GetBytes(owner), true, now) is { Owner: true }
            && registry.Authenticate(bytes, false, now.AddHours(25)) is null
            && !registry.Active(grant, now.AddHours(25))
            && !JsonSerializer.Serialize(registry.List(now)).Contains(issued.Token);
        var second = registry.Issue("Second", now)!;
        var secondGrant = registry.Authenticate(Encoding.ASCII.GetBytes(second.Token), true, now)!;
        valid &= registry.Revoke(second.Device.Id) && !registry.Active(secondGrant, now)
            && registry.Authenticate(Encoding.ASCII.GetBytes(second.Token), true, now) is null
            && !DeviceRegistry.ValidName(" bad ") && !DeviceRegistry.ValidName("x\n");
        for (var i = 0; i < 32; i++) valid &= registry.Issue($"Device {i}", now) is not null;
        valid &= registry.Issue("Overflow", now) is null;
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} Device scope, expiry, revoke, capacity and privacy");
        return valid ? 0 : 1;
    }

    internal static async Task<int> SmokeAsync(string directory)
    {
        try
        {
            await using var host = new HostController(directory);
            await host.StartAsync();
            var owner = (await host.DashboardUrlAsync()).Split("#token=")[1];
            using var http = new HttpClient(new HttpClientHandler { UseProxy = false })
                { BaseAddress = new Uri("http://127.0.0.1:47860/"), Timeout = TimeSpan.FromSeconds(5) };
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(20));
            var ct = deadline.Token;
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", owner);
            using var created = await http.PostAsync("api/v1/devices",
                new StringContent("{\"name\":\"Tablet\"}", Encoding.UTF8, "application/json"), ct);
            Console.WriteLine($"Create device HTTP status: {(int)created.StatusCode}");
            Check(created.StatusCode == HttpStatusCode.Created, "Create device");
            using var json = JsonDocument.Parse(await created.Content.ReadAsByteArrayAsync(ct));
            var token = json.RootElement.GetProperty("token").GetString()!;
            var id = json.RootElement.GetProperty("device").GetProperty("id").GetGuid();
            using var foreign = new HttpRequestMessage(HttpMethod.Get, "api/v1/devices");
            foreign.Headers.TryAddWithoutValidation("Origin", "http://example.invalid");
            using var deniedOrigin = await http.SendAsync(foreign, ct);
            Check(deniedOrigin.StatusCode == HttpStatusCode.Forbidden, "Foreign admin origin denied");
            using var rebinding = new HttpRequestMessage(HttpMethod.Get, "api/v1/devices");
            rebinding.Headers.Host = "untrusted.example:47860";
            using var deniedHost = await http.SendAsync(rebinding, ct);
            Check(deniedHost.StatusCode == HttpStatusCode.Forbidden, "Unexpected admin Host denied");
            using var list = await http.GetAsync("api/v1/devices", ct);
            Check(list.IsSuccessStatusCode && !(await list.Content.ReadAsStringAsync(ct)).Contains(token), "No tokens in list");
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
            using var denied = await http.GetAsync("api/v1/devices", ct);
            Check(denied.StatusCode == HttpStatusCode.Forbidden, "Device cannot administer");
            using var sample = await http.GetAsync("api/v1/telemetry", ct);
            Check(sample.IsSuccessStatusCode, "Device telemetry allowed");
            using var ws = new ClientWebSocket();
            await ws.ConnectAsync(new Uri("ws://127.0.0.1:47860/api/v1/telemetry/ws"), ct);
            await ws.SendAsync(Encoding.ASCII.GetBytes(token).AsMemory(), WebSocketMessageType.Text, true, ct);
            await WebSocketSmoke.ReadSample(ws, ct);
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", owner);
            using var removed = await http.DeleteAsync($"api/v1/devices/{id}", ct);
            Check(removed.StatusCode == HttpStatusCode.NoContent, "Revoke device");
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
            using var revoked = await http.GetAsync("api/v1/telemetry", ct);
            Check(revoked.StatusCode == HttpStatusCode.Unauthorized, "Revoked REST denied");
            await ClosedAsync(ws, ct);
            Console.WriteLine("PASS: device API and active WebSocket revocation");
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine($"FAIL: device smoke ({ex.GetType().Name})"); return 1; }
    }

    private static async Task ClosedAsync(ClientWebSocket socket, CancellationToken ct)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(ct);
        deadline.CancelAfter(TimeSpan.FromSeconds(5));
        var buffer = new byte[16384];
        try
        {
            while (socket.State == WebSocketState.Open)
                if ((await socket.ReceiveAsync(buffer.AsMemory(), deadline.Token)).MessageType == WebSocketMessageType.Close) return;
        }
        catch (WebSocketException) { return; }
        if (socket.State == WebSocketState.Open) throw new InvalidOperationException("Revocation did not close session");
    }

    private static void Check(bool pass, string label)
    {
        if (!pass) { Console.WriteLine($"FAIL: {label}"); throw new InvalidOperationException(label); }
        Console.WriteLine($"PASS: {label}");
    }
}
