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
        "Standalone opt-in Windows grant persistence: VEYPANEL_PERSIST_GRANTS=1.\n" +
        "Apollo inventory: --apollo-inspect <verified-certificate-sha256>\n" +
        "Apollo pairing: --apollo-pair <verified-certificate-sha256>\n" +
        "Desktop source inventory: --display-inventory\n" +
        "Active display topology: --display-topology\n" +
        "Validate current topology without applying: --display-validate");
    return;
}
var managed = args.Length == 1 && args[0] == "--managed-local";
var builder = WebApplication.CreateBuilder(managed ? [] : args);
// Framework request/exception messages can contain untrusted paths, queries
// or other private values before authorization. Do not publish them through
// default console/debug/event providers, including configuration overrides.
builder.Logging.ClearProviders();
var lan = managed ? null : Environment.GetEnvironmentVariable("VEYPANEL_LAN_IP");
var pfx = Environment.GetEnvironmentVariable("VEYPANEL_PFX");
var password = Environment.GetEnvironmentVariable("VEYPANEL_PFX_PASSWORD");
var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
IGrantStore? persisted = null;
DeviceRegistry registry;
try
{
    // Managed Desktop remains ephemeral; standalone persistence is an explicit operator opt-in.
    if (!managed && Environment.GetEnvironmentVariable("VEYPANEL_PERSIST_GRANTS") == "1")
    {
        if (!OperatingSystem.IsWindows()) throw new PlatformNotSupportedException();
        persisted = ProtectedGrantStore.OpenDefault();
    }
    registry = new DeviceRegistry(token, persisted);
}
catch (Exception ex) when (ex is IOException or InvalidDataException or UnauthorizedAccessException or CryptographicException
    or InvalidOperationException or PlatformNotSupportedException or System.ComponentModel.Win32Exception)
{
    persisted?.Dispose();
    Console.Error.WriteLine("Protected reader store cannot be opened. Host not started; inspect the local store. No automatic recovery.");
    Environment.ExitCode = 1;
    return;
}
using var storeLifetime = persisted;
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
builder.Services.AddSingleton<StorageHealthWorker>();
builder.Services.AddHostedService<StorageHealthWorker>(services => services.GetRequiredService<StorageHealthWorker>());
builder.Services.AddSingleton<ThermalWorker>();
builder.Services.AddHostedService<ThermalWorker>(services => services.GetRequiredService<ThermalWorker>());
builder.Services.AddSingleton<Telemetry>();
builder.Services.AddHostedService<Telemetry>(services => services.GetRequiredService<Telemetry>());
var app = builder.Build();
var telemetrySocket = new TelemetrySocket(registry, lan, json);
var enroll = new InvitationEndpoints(new InvitationRegistry(registry), lan);
app.UseWebSockets(new WebSocketOptions { KeepAliveInterval = TimeSpan.FromSeconds(15) });
app.Use(async (context, next) =>
{
    context.Response.Headers.CacheControl = "no-store";
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    var connect = context.Request.IsHttps && lan is not null ? $"wss://{lan}:47861" : "ws://127.0.0.1:47860";
    context.Response.Headers["Content-Security-Policy"] = $"default-src 'self'; connect-src 'self' {connect}; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    if (!context.Request.IsHttps && !IPAddress.IsLoopback(context.Connection.RemoteIpAddress ?? IPAddress.None))
    { context.Response.StatusCode = 403; return; }
    if (InvitationEndpoints.IsPublic(context))
    {
        if (!enroll.Allowed(context)) { context.Response.StatusCode = 403; return; }
    }
    else if (context.Request.Path.StartsWithSegments("/api") && context.Request.Path != "/api/v1/telemetry/ws")
    {
        var authorization = context.Request.Headers.Authorization.ToString();
        var supplied = authorization.StartsWith("Bearer ", StringComparison.Ordinal)
            ? Encoding.ASCII.GetBytes(authorization[7..]) : Array.Empty<byte>();
        var local = DeviceRegistry.LocalOwner(context);
        var grant = registry.Authenticate(supplied, local, DateTimeOffset.UtcNow);
        CryptographicOperations.ZeroMemory(supplied);
        if (grant is null) { context.Response.StatusCode = 401; return; }
        if (context.Request.Path.StartsWithSegments("/api/v1/devices"))
        {
            var origin = context.Request.Headers.Origin;
            if (!local || !grant.Owner || context.Request.Host.Value != "127.0.0.1:47860"
                || context.Request.QueryString.HasValue || origin.Count > 1
                || (origin.Count == 1 && origin[0] != "http://127.0.0.1:47860"))
            { context.Response.StatusCode = 403; return; }
        }
        else if ((context.Request.Path != "/api/v1/telemetry" && context.Request.Path != "/api/v1/history" && context.Request.Path != "/api/v1/history.csv")
            || !HttpMethods.IsGet(context.Request.Method) || context.Request.QueryString.HasValue)
        { context.Response.StatusCode = 403; return; }
    }
    try { await next(); }
    catch (GrantStoreUnavailableException)
    {
        if (!context.Response.HasStarted) { context.Response.StatusCode = 503; }
        else context.Abort();
    }
});
app.UseDefaultFiles();
app.UseStaticFiles();
app.MapGet("/api/v1/telemetry", (Telemetry telemetry) => Results.Json(telemetry.Latest, json));
app.MapGet("/api/v1/history", (Telemetry telemetry) => Results.Json(telemetry.History, json));
app.MapGet("/api/v1/history.csv", (Telemetry telemetry) =>
    Results.File(Encoding.UTF8.GetBytes(HistoryCsv.Format(telemetry.History)),
        "text/csv; charset=utf-8", "veypanel-history.csv"));
app.MapGet("/api/v1/telemetry/ws", (HttpContext context, Telemetry telemetry, IHostApplicationLifetime lifetime) =>
    telemetrySocket.HandleAsync(context, telemetry, lifetime));
DeviceEndpoints.Map(app, registry, lan);
enroll.Map(app);
Console.WriteLine($"Local dashboard: http://127.0.0.1:47860/#token={token}");
if (!string.IsNullOrWhiteSpace(lan) && persisted is not null)
    Console.WriteLine("LAN reader enrollment: use the local owner dashboard (protected grants enabled).");
else if (!string.IsNullOrWhiteSpace(lan))
{
    var initial = registry.Issue("Initial LAN access", DateTimeOffset.UtcNow)!;
    Console.WriteLine($"LAN dashboard: https://{lan}:47861/#token={initial.Token}");
}
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
