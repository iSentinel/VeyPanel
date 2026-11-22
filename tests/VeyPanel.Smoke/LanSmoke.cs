using System.Diagnostics;
using System.Net.WebSockets;
using System.Text;
using System.Net;
using System.Net.Http.Headers;
using System.Net.NetworkInformation;
using System.Net.Security;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text.Json;
using System.Text.RegularExpressions;
using VeyPanel.Host;

internal static class LanSmoke
{
    internal static async Task<int> RunAsync(string publishDirectory)
    {
        var directory = Path.Combine(Path.GetTempPath(), "veypanel-lan-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(directory);
            var ip = FindAddress();
            using var cert = CreateCertificate(ip);
            var password = Convert.ToHexString(RandomNumberGenerator.GetBytes(24));
            var pfx = Path.Combine(directory, "test.pfx");
            await File.WriteAllBytesAsync(pfx, cert.Export(X509ContentType.Pfx, password));
            await VerifyAsync(Path.GetFullPath(publishDirectory), ip, pfx, password, SHA256.HashData(cert.RawData));
            Console.WriteLine("PASS: HTTPS LAN integration");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FAIL: HTTPS LAN integration ({ex.GetType().Name})");
            return 1;
        }
        finally
        {
            if (Directory.Exists(directory)) Directory.Delete(directory, true);
        }
    }

    private static IPAddress FindAddress() =>
        NetworkInterface.GetAllNetworkInterfaces().Where(n => n.OperationalStatus == OperationalStatus.Up)
            .SelectMany(n => n.GetIPProperties().UnicastAddresses)
            .Select(a => a.Address).FirstOrDefault(LanAddressPolicy.IsPrivateIpv4)
        ?? throw new InvalidOperationException("No private IPv4 on runner.");

    private static X509Certificate2 CreateCertificate(IPAddress ip)
    {
        using var key = RSA.Create(2048);
        var request = new CertificateRequest("CN=VeyPanel CI test only", key, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        var san = new SubjectAlternativeNameBuilder();
        san.AddIpAddress(ip);
        request.CertificateExtensions.Add(san.Build());
        request.CertificateExtensions.Add(new X509BasicConstraintsExtension(false, false, 0, true));
        request.CertificateExtensions.Add(new X509KeyUsageExtension(X509KeyUsageFlags.DigitalSignature | X509KeyUsageFlags.KeyEncipherment, true));
        request.CertificateExtensions.Add(new X509EnhancedKeyUsageExtension(new OidCollection { new("1.3.6.1.5.5.7.3.1") }, false));
        return request.CreateSelfSigned(DateTimeOffset.UtcNow.AddMinutes(-2), DateTimeOffset.UtcNow.AddHours(1));
    }

    private static Process StartHost(string directory, IPAddress ip, string pfx, string password,
        TaskCompletionSource<string> token)
    {
        var start = new ProcessStartInfo(Path.Combine(directory, "VeyPanel.Host.exe")) {
            WorkingDirectory = directory, UseShellExecute = false,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        start.Environment["VEYPANEL_LAN_IP"] = ip.ToString();
        start.Environment["VEYPANEL_PFX"] = pfx;
        start.Environment["VEYPANEL_PFX_PASSWORD"] = password;
        var process = Process.Start(start) ?? throw new InvalidOperationException("Host start failed.");
        process.OutputDataReceived += (_, e) =>
        {
            var match = Regex.Match(e.Data ?? "", @"^LAN dashboard: https://[^/]+/#token=([A-F0-9]{64})$");
            if (match.Success) token.TrySetResult(match.Groups[1].Value);
        };
        process.ErrorDataReceived += (_, _) => { };
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
        return process;
    }

    private static async Task VerifyAsync(string directory, IPAddress ip, string pfx, string password, byte[] pin)
    {
        var tokenSource = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
        using var process = StartHost(directory, ip, pfx, password, tokenSource);
        try
        {
            var root = new Uri($"https://{ip}:47861/");
            var accessToken = await tokenSource.Task.WaitAsync(TimeSpan.FromSeconds(30));
            using var client = CreateClient(root, pin);
            await WaitReadyAsync(client, process);
            await VerifyApiAsync(client, accessToken);
            await VerifyWssAsync(ip, accessToken, pin);
            using var wrongPin = CreateClient(root, new byte[32]);
            await RequireRejectedTlsAsync(wrongPin, "Wrong certificate pin");
            using var defaultTrust = new HttpClient(new HttpClientHandler { UseProxy = false, AllowAutoRedirect = false })
                { BaseAddress = root, Timeout = TimeSpan.FromSeconds(5) };
            await RequireRejectedTlsAsync(defaultTrust, "Untrusted test certificate");
        }
        finally
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(10));
        }
    }

    private static async Task VerifyWssAsync(IPAddress ip, string token, byte[] pin)
    {
        var uri = new Uri($"wss://{ip}:47861/api/v1/telemetry/ws");
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        using var socket = new ClientWebSocket();
        socket.Options.SetRequestHeader("Origin", $"https://{ip}:47861");
        socket.Options.RemoteCertificateValidationCallback = (_, certificate, _, errors) =>
        {
            if (certificate is null || (errors & (SslPolicyErrors.RemoteCertificateNameMismatch |
                SslPolicyErrors.RemoteCertificateNotAvailable)) != 0) return false;
            return CryptographicOperations.FixedTimeEquals(SHA256.HashData(certificate.GetRawCertData()), pin);
        };
        await socket.ConnectAsync(uri, deadline.Token);
        await socket.SendAsync(Encoding.ASCII.GetBytes(token).AsMemory(), WebSocketMessageType.Text, true, deadline.Token);
        var stamp = await WebSocketSmoke.ReadSample(socket, deadline.Token);
        Check(Math.Abs((DateTimeOffset.UtcNow - stamp).TotalSeconds) < 5, "WSS fresh authenticated telemetry");
        await socket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "", deadline.Token);

        using var untrusted = new ClientWebSocket();
        try { await untrusted.ConnectAsync(uri, deadline.Token); }
        catch (WebSocketException) { Console.WriteLine("PASS: WSS untrusted certificate rejected"); return; }
        throw new InvalidOperationException("Unexpected WSS trust.");
    }

    private static HttpClient CreateClient(Uri root, byte[] expected) =>
        new(new HttpClientHandler {
            UseProxy = false, AllowAutoRedirect = false,
            ServerCertificateCustomValidationCallback = (_, cert, _, errors) =>
                (errors & (SslPolicyErrors.RemoteCertificateNameMismatch | SslPolicyErrors.RemoteCertificateNotAvailable)) == 0
                && ApolloClient.MatchesCertificate(cert, expected, DateTime.UtcNow)
        }) { BaseAddress = root, Timeout = TimeSpan.FromSeconds(5) };

    private static async Task WaitReadyAsync(HttpClient client, Process process)
    {
        for (var i = 0; i < 30; i++)
        {
            if (process.HasExited) throw new InvalidOperationException("Host stopped.");
            try
            {
                using var response = await client.GetAsync("");
                if (response.IsSuccessStatusCode)
                {
                    Check((await response.Content.ReadAsStringAsync()).Contains("VeyPanel", StringComparison.Ordinal),
                        "Pinned HTTPS dashboard");
                    return;
                }
            }
            catch (HttpRequestException) { }
            await Task.Delay(500);
        }
        throw new TimeoutException("Host readiness timed out.");
    }

    private static async Task VerifyApiAsync(HttpClient client, string token)
    {
        using (var unauthorized = await client.GetAsync("api/v1/telemetry"))
            Check(unauthorized.StatusCode == HttpStatusCode.Unauthorized, "HTTPS missing token rejected");
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", "invalid");
        using (var rejected = await client.GetAsync("api/v1/telemetry"))
            Check(rejected.StatusCode == HttpStatusCode.Unauthorized, "HTTPS wrong token rejected");
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        using (var admin = await client.GetAsync("api/v1/devices"))
            Check(admin.StatusCode == HttpStatusCode.Forbidden, "LAN device administration denied");
        for (var i = 0; i < 10; i++)
        {
            using var result = await client.GetAsync("api/v1/telemetry");
            result.EnsureSuccessStatusCode();
            using var sample = JsonDocument.Parse(await result.Content.ReadAsByteArrayAsync());
            if (sample.RootElement.GetProperty("status").GetString() == "ok")
            {
                Check(Math.Abs((DateTimeOffset.UtcNow - sample.RootElement.GetProperty("timestampUtc").GetDateTimeOffset()).TotalSeconds) < 5,
                    "HTTPS authenticated fresh telemetry");
                return;
            }
            await Task.Delay(1000);
        }
        throw new InvalidOperationException("Native counters unavailable.");
    }

    private static async Task RequireRejectedTlsAsync(HttpClient client, string name)
    {
        try { using var response = await client.GetAsync(""); }
        catch (HttpRequestException ex) when (ex.HttpRequestError == HttpRequestError.SecureConnectionError)
        { Console.WriteLine($"PASS: {name} rejected"); return; }
        throw new InvalidOperationException("Unexpected TLS success.");
    }

    private static void Check(bool condition, string name)
    {
        if (!condition) throw new InvalidOperationException("Assertion failed.");
        Console.WriteLine($"PASS: {name}");
    }
}
