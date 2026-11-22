using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text.Json;

namespace VeyPanel.Host;

internal sealed record ApolloInventory(string? HostName, string[] Apps, int PairedClients);

internal sealed class ApolloClient : IDisposable
{
    private static readonly Uri Endpoint = new("https://127.0.0.1:47990/");
    private readonly HttpClient _http;
    private bool _authenticated;

    private ApolloClient(HttpMessageHandler handler)
    {
        _http = new HttpClient(handler) {
            BaseAddress = Endpoint,
            Timeout = TimeSpan.FromSeconds(5),
            MaxResponseContentBufferSize = 1024 * 1024
        };
    }

    internal static ApolloClient Create(string fingerprint)
    {
        var expected = ParseFingerprint(fingerprint);
        var handler = new HttpClientHandler {
            AllowAutoRedirect = false, UseProxy = false,
            UseCookies = true, CookieContainer = new CookieContainer(),
            ServerCertificateCustomValidationCallback = (_, certificate, _, _) =>
                MatchesCertificate(certificate, expected, DateTime.UtcNow)
        };
        return new ApolloClient(handler);
    }

    internal static ApolloClient ForTest(HttpMessageHandler handler) => new(handler);

    internal static byte[] ParseFingerprint(string input)
    {
        var normalized = input.Replace(":", "").Replace(" ", "");
        if (normalized.Length != 64) throw new FormatException("Expected SHA-256 certificate fingerprint.");
        return Convert.FromHexString(normalized);
    }

    internal static bool MatchesCertificate(X509Certificate2? certificate, byte[] expected, DateTime nowUtc)
    {
        if (certificate is null || expected.Length != 32
            || nowUtc < certificate.NotBefore.ToUniversalTime()
            || nowUtc > certificate.NotAfter.ToUniversalTime()) return false;
        return CryptographicOperations.FixedTimeEquals(SHA256.HashData(certificate.RawData), expected);
    }

    internal async Task LoginAsync(string username, string password, CancellationToken ct = default)
    {
        _authenticated = false;
        using var result = await _http.PostAsJsonAsync("api/login", new { username, password }, ct);
        if (result.StatusCode != HttpStatusCode.OK)
            throw new HttpRequestException("Apollo login failed.", null, result.StatusCode);
        if (!result.Headers.TryGetValues("Set-Cookie", out var cookies)
            || !cookies.Any(value => value.StartsWith("auth=", StringComparison.Ordinal)
                && value.Length > 5 && value[5] != ';'))
            throw new InvalidDataException("Apollo login did not return an auth cookie.");
        _authenticated = true;
    }

    internal async Task<ApolloInventory> InspectAsync(CancellationToken ct = default)
    {
        if (!_authenticated) throw new InvalidOperationException("Login required.");
        using var apps = await GetJsonAsync("api/apps", ct);
        using var clients = await GetJsonAsync("api/clients/list", ct);
        var root = apps.RootElement;
        if (!root.TryGetProperty("apps", out var list) || list.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Unexpected Apollo application list.");
        var clientRoot = clients.RootElement;
        if (!clientRoot.TryGetProperty("status", out var status) || status.ValueKind != JsonValueKind.True
            || !clientRoot.TryGetProperty("named_certs", out var paired) || paired.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Unexpected Apollo client list.");
        var names = list.EnumerateArray().Select(app => ReadString(app, "name") ?? "(unnamed)").ToArray();
        return new ApolloInventory(ReadString(root, "host_name"), names, paired.GetArrayLength());
    }

    internal static bool ValidPairingInput(string pin, string name) =>
        pin.Length == 4 && pin.All(char.IsAsciiDigit)
        && name.Length is >= 1 and <= 64 && name == name.Trim()
        && !name.Any(char.IsControl);

    internal async Task<bool> PairAsync(string pin, string name, CancellationToken ct = default)
    {
        if (!_authenticated) throw new InvalidOperationException("Login required.");
        if (!ValidPairingInput(pin, name)) throw new FormatException("Invalid pairing input.");
        using var response = await _http.PostAsJsonAsync("api/pin", new { pin, name }, ct);
        if (response.StatusCode != HttpStatusCode.OK)
        {
            if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
                _authenticated = false;
            throw new HttpRequestException("Apollo pairing request failed.", null, response.StatusCode);
        }
        using var json = JsonDocument.Parse(await response.Content.ReadAsByteArrayAsync(ct));
        if (json.RootElement.ValueKind != JsonValueKind.Object
            || !json.RootElement.TryGetProperty("status", out var status)
            || status.ValueKind is not (JsonValueKind.True or JsonValueKind.False))
            throw new InvalidDataException("Unexpected pairing response.");
        return status.GetBoolean();
    }

    private async Task<JsonDocument> GetJsonAsync(string path, CancellationToken ct)
    {
        using var response = await _http.GetAsync(path, ct);
        if (response.StatusCode != HttpStatusCode.OK)
        {
            if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
                _authenticated = false;
            throw new HttpRequestException("Apollo query failed.", null, response.StatusCode);
        }
        return JsonDocument.Parse(await response.Content.ReadAsByteArrayAsync(ct));
    }

    private static string? ReadString(JsonElement value, string key) =>
        value.ValueKind == JsonValueKind.Object && value.TryGetProperty(key, out var field)
            && field.ValueKind == JsonValueKind.String ? field.GetString() : null;

    public void Dispose() => _http.Dispose();
}
