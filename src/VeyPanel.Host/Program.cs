using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using VeyPanel.Host;

if (args.Contains("--display-validate"))
{
    if (args.Length != 1)
    {
        Console.Error.WriteLine("Usage: VeyPanel.Host --display-validate");
        Environment.ExitCode = 2;
        return;
    }
    var validation = DisplayValidation.ValidateCurrent();
    Console.WriteLine(JsonSerializer.Serialize(validation, new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true }));
    Environment.ExitCode = validation.Status == "validated" ? 0 : 1;
    return;
}

if (args.Contains("--display-topology"))
{
    if (args.Length != 1)
    {
        Console.Error.WriteLine("Usage: VeyPanel.Host --display-topology");
        Environment.ExitCode = 2;
        return;
    }
    var topology = DisplayTopology.Capture();
    Console.WriteLine(JsonSerializer.Serialize(topology, new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true }));
    Environment.ExitCode = topology.Status == "ok" ? 0 : 1;
    return;
}

if (args.Contains("--display-inventory"))
{
    if (args.Length != 1)
    {
        Console.Error.WriteLine("Usage: VeyPanel.Host --display-inventory");
        Environment.ExitCode = 2;
        return;
    }
    var snapshot = DisplayInventory.Capture();
    Console.WriteLine(JsonSerializer.Serialize(snapshot, new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true }));
    Environment.ExitCode = snapshot.Status == "ok" ? 0 : 1;
    return;
}

if (args.Contains("--apollo-inspect") || args.Contains("--apollo-pair"))
{
    Environment.ExitCode = await ApolloInspectCommand.RunAsync(args);
    return;
}

if (args.Contains("--help") || args.Contains("-h"))
{
    Console.WriteLine("VeyPanel Host: local dashboard http://127.0.0.1:47860.\n" +
        "Optional LAN: set VEYPANEL_LAN_IP, VEYPANEL_PFX and VEYPANEL_PFX_PASSWORD.\n" +
        "LAN requires a certificate trusted by the client. Access token is generated on startup.\n" +
        "Apollo inventory: --apollo-inspect <verified-certificate-sha256>\n" +
        "Apollo pairing: --apollo-pair <verified-certificate-sha256>\n" +
        "Desktop source inventory: --display-inventory\n" +
        "Active display topology: --display-topology\n" +
        "Validate current topology without applying: --display-validate");
    return;
}
var managed = args.Length == 1 && args[0] == "--managed-local";
var builder = WebApplication.CreateBuilder(managed ? [] : args);
var lan = managed ? null : Environment.GetEnvironmentVariable("VEYPANEL_LAN_IP");
var pfx = Environment.GetEnvironmentVariable("VEYPANEL_PFX");
var password = Environment.GetEnvironmentVariable("VEYPANEL_PFX_PASSWORD");
var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
var tokenBytes = Encoding.ASCII.GetBytes(token);
var json = new JsonSerializerOptions(JsonSerializerDefaults.Web);

builder.WebHost.ConfigureKestrel(kestrel =>
{
    kestrel.Listen(IPAddress.Loopback, 47860);
    if (string.IsNullOrWhiteSpace(lan)) return;
    if (!IPAddress.TryParse(lan, out var address) || !LanAddressPolicy.IsPrivateIpv4(address)
        || string.IsNullOrWhiteSpace(pfx) || !File.Exists(pfx))
        throw new InvalidOperationException("LAN requires a specific RFC1918 private IPv4 address and an existing TLS PFX.");
    kestrel.Listen(address, 47861, options => options.UseHttps(pfx, password));
});
builder.Services.AddSingleton<Telemetry>();
builder.Services.AddHostedService<Telemetry>(services => services.GetRequiredService<Telemetry>());
var app = builder.Build();
var telemetrySocket = new TelemetrySocket(tokenBytes, lan, json);
app.UseWebSockets(new WebSocketOptions { KeepAliveInterval = TimeSpan.FromSeconds(15) });
app.Use(async (context, next) =>
{
    context.Response.Headers.CacheControl = "no-store";
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    var connect = context.Request.IsHttps && lan is not null ? $"wss://{lan}:47861" : "ws://127.0.0.1:47860";
    context.Response.Headers["Content-Security-Policy"] = $"default-src 'self'; connect-src 'self' {connect}; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    if (!context.Request.IsHttps && !IPAddress.IsLoopback(context.Connection.RemoteIpAddress ?? IPAddress.None))
    { context.Response.StatusCode = 403; return; }
    if (context.Request.Path.StartsWithSegments("/api") && context.Request.Path != "/api/v1/telemetry/ws")
    {
        var authorization = context.Request.Headers.Authorization.ToString();
        var supplied = authorization.StartsWith("Bearer ", StringComparison.Ordinal)
            ? Encoding.ASCII.GetBytes(authorization[7..]) : Array.Empty<byte>();
        if (!CryptographicOperations.FixedTimeEquals(supplied, tokenBytes))
        { context.Response.StatusCode = 401; return; }
    }
    await next();
});
app.UseDefaultFiles();
app.UseStaticFiles();
app.MapGet("/api/v1/telemetry", (Telemetry telemetry) => Results.Json(telemetry.Latest, json));
app.MapGet("/api/v1/telemetry/ws", (HttpContext context, Telemetry telemetry, IHostApplicationLifetime lifetime) =>
    telemetrySocket.HandleAsync(context, telemetry, lifetime));
Console.WriteLine($"Local dashboard: http://127.0.0.1:47860/#token={token}");
if (!string.IsNullOrWhiteSpace(lan)) Console.WriteLine($"LAN dashboard: https://{lan}:47861/#token={token}");
if (!managed)
{
    await app.RunAsync();
    return;
}

// The owning desktop process retains stdin. EOF also stops an orphaned child.
await app.StartAsync();
_ = Task.Run(async () =>
{
    try { await Console.In.ReadLineAsync(); }
    finally { app.Lifetime.StopApplication(); }
});
await app.WaitForShutdownAsync();
