using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using VeyPanel.Host;

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

if (args.Contains("--apollo-inspect"))
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
        "Desktop source inventory: --display-inventory");
    return;
}
var builder = WebApplication.CreateBuilder(args);
var lan = Environment.GetEnvironmentVariable("VEYPANEL_LAN_IP");
var pfx = Environment.GetEnvironmentVariable("VEYPANEL_PFX");
var password = Environment.GetEnvironmentVariable("VEYPANEL_PFX_PASSWORD");
var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
var tokenBytes = Encoding.ASCII.GetBytes(token);
var json = new JsonSerializerOptions(JsonSerializerDefaults.Web);

builder.WebHost.ConfigureKestrel(kestrel =>
{
    kestrel.Listen(IPAddress.Loopback, 47860);
    if (string.IsNullOrWhiteSpace(lan)) return;
    if (!IPAddress.TryParse(lan, out var address) || address.AddressFamily != System.Net.Sockets.AddressFamily.InterNetwork
        || IPAddress.IsLoopback(address) || address.Equals(IPAddress.Any)
        || string.IsNullOrWhiteSpace(pfx) || !File.Exists(pfx))
        throw new InvalidOperationException("LAN requires a specific IPv4 address and an existing TLS PFX.");
    kestrel.Listen(address, 47861, options => options.UseHttps(pfx, password));
});
builder.Services.AddSingleton<Telemetry>();
builder.Services.AddHostedService<Telemetry>(services => services.GetRequiredService<Telemetry>());
var app = builder.Build();
app.Use(async (context, next) =>
{
    context.Response.Headers.CacheControl = "no-store";
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    if (!context.Request.IsHttps && !IPAddress.IsLoopback(context.Connection.RemoteIpAddress ?? IPAddress.None))
    { context.Response.StatusCode = 403; return; }
    if (context.Request.Path.StartsWithSegments("/api"))
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
Console.WriteLine($"Local dashboard: http://127.0.0.1:47860/#token={token}");
if (!string.IsNullOrWhiteSpace(lan)) Console.WriteLine($"LAN dashboard: https://{lan}:47861/#token={token}");
await app.RunAsync();
