using System.Net;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using VeyPanel.Host;

internal static class ApolloTests
{
    internal static async Task<int> RunAsync()
    {
        var failed = 0;
        foreach (var (name, check) in new (string Name, Func<Task<bool>> Check)[] {
            ("Apollo certificate exact pin/expiry", CertificateCheck),
            ("Apollo invalid fingerprint", InvalidFingerprint),
            ("Apollo successful inventory", Inventory),
            ("Apollo unauthenticated query blocked", BeforeLogin),
            ("Apollo login rejected", FailedLogin),
            ("Apollo missing cookie rejected", MissingCookie),
            ("Apollo redirect rejected", RedirectRejected),
            ("Apollo malformed inventory rejected", MalformedInventory),
            ("Apollo expired session rejected", ExpiredSession),
            ("Apollo PIN accepted and payload verified", PairAccepted),
            ("Apollo PIN rejected", PairRejected),
            ("Apollo invalid PIN/name blocked", PairInvalid),
            ("Apollo pairing requires login", PairUnauthenticated),
            ("Apollo malformed pairing status rejected", PairMalformed)
        })
        {
            bool pass;
            try { pass = await check(); } catch { pass = false; }
            Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {name}");
            if (!pass) failed++;
        }
        Console.WriteLine($"{14 - failed}/14 Apollo tests passed");
        return failed;
    }

    private static Task<bool> CertificateCheck()
    {
        using var key = RSA.Create(2048);
        var request = new CertificateRequest("CN=localhost", key, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        var now = DateTime.UtcNow;
        using var cert = request.CreateSelfSigned(now.AddHours(-1), now.AddHours(1));
        var pin = SHA256.HashData(cert.RawData);
        return Task.FromResult(ApolloClient.MatchesCertificate(cert, pin, now)
            && !ApolloClient.MatchesCertificate(cert, new byte[32], now)
            && !ApolloClient.MatchesCertificate(cert, pin, now.AddHours(2))
            && !ApolloClient.MatchesCertificate(null, pin, now)
            && ApolloClient.ParseFingerprint(Convert.ToHexString(pin)).SequenceEqual(pin));
    }

    private static Task<bool> InvalidFingerprint()
    {
        try { ApolloClient.ParseFingerprint("bad"); return Task.FromResult(false); }
        catch (FormatException) { return Task.FromResult(true); }
    }

    private static async Task<bool> Inventory()
    {
        using var handler = new FakeHandler(Login(), Apps(), Clients());
        using var client = ApolloClient.ForTest(handler);
        await client.LoginAsync("test", "example");
        var data = await client.InspectAsync();
        return data.HostName == "PC" && data.Apps.SequenceEqual(new[] { "Desktop" })
            && data.PairedClients == 1 && handler.Paths.SequenceEqual(new[] {
                "POST /api/login", "GET /api/apps", "GET /api/clients/list" });
    }

    private static async Task<bool> BeforeLogin()
    {
        using var handler = new FakeHandler();
        using var client = ApolloClient.ForTest(handler);
        return await Reject<InvalidOperationException>(() => client.InspectAsync()) && handler.Paths.Count == 0;
    }

    private static async Task<bool> FailedLogin()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(new HttpResponseMessage(HttpStatusCode.Unauthorized)));
        return await Reject<HttpRequestException>(() => client.LoginAsync("test", "example"));
    }

    private static async Task<bool> MissingCookie()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(new HttpResponseMessage(HttpStatusCode.OK)));
        return await Reject<InvalidDataException>(() => client.LoginAsync("test", "example"));
    }

    private static async Task<bool> RedirectRejected()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(new HttpResponseMessage(HttpStatusCode.Found)));
        return await Reject<HttpRequestException>(() => client.LoginAsync("test", "example"));
    }

    private static async Task<bool> MalformedInventory()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(Login(), Json(new { apps = false }), Clients()));
        await client.LoginAsync("test", "example");
        return await Reject<InvalidDataException>(() => client.InspectAsync());
    }

    private static async Task<bool> ExpiredSession()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(Login(), new HttpResponseMessage(HttpStatusCode.Unauthorized)));
        await client.LoginAsync("test", "example");
        return await Reject<HttpRequestException>(() => client.InspectAsync())
            && await Reject<InvalidOperationException>(() => client.InspectAsync());
    }

    private static async Task<bool> PairAccepted()
    {
        using var handler = new FakeHandler(Login(), Json(new { status = true }));
        using var client = ApolloClient.ForTest(handler);
        await client.LoginAsync("test", "example");
        return await client.PairAsync("0123", "Test Tablet")
            && handler.Paths.SequenceEqual(new[] { "POST /api/login", "POST /api/pin" })
            && handler.PairPayloadVerified;
    }

    private static async Task<bool> PairRejected()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(Login(), Json(new { status = false })));
        await client.LoginAsync("test", "example");
        return !await client.PairAsync("0123", "Test Tablet");
    }

    private static async Task<bool> PairInvalid()
    {
        using var handler = new FakeHandler(Login());
        using var client = ApolloClient.ForTest(handler);
        await client.LoginAsync("test", "example");
        return await Reject<FormatException>(() => client.PairAsync("٠١٢٣", "Tablet"))
            && await Reject<FormatException>(() => client.PairAsync("0123", ""))
            && await Reject<FormatException>(() => client.PairAsync("0123", "x\n"))
            && !ApolloClient.ValidPairingInput("12345", "Tablet")
            && handler.Paths.Count == 1;
    }

    private static async Task<bool> PairUnauthenticated()
    {
        using var handler = new FakeHandler();
        using var client = ApolloClient.ForTest(handler);
        return await Reject<InvalidOperationException>(() => client.PairAsync("0123", "Tablet"))
            && handler.Paths.Count == 0;
    }

    private static async Task<bool> PairMalformed()
    {
        using var client = ApolloClient.ForTest(new FakeHandler(Login(), Json(new { status = "true" })));
        await client.LoginAsync("test", "example");
        return await Reject<InvalidDataException>(() => client.PairAsync("0123", "Test Tablet"));
    }

    private static async Task<bool> Reject<T>(Func<Task> command) where T : Exception
    {
        try { await command(); return false; } catch (T) { return true; }
    }

    private static HttpResponseMessage Login()
    {
        var response = new HttpResponseMessage(HttpStatusCode.OK);
        response.Headers.TryAddWithoutValidation("Set-Cookie", "auth=mock; Secure; SameSite=Strict; Path=/");
        return response;
    }

    private static HttpResponseMessage Json<T>(T value) => new(HttpStatusCode.OK) { Content = JsonContent.Create(value) };
    private static HttpResponseMessage Apps() => Json(new { host_name = "PC", apps = new[] { new { name = "Desktop" } } });
    private static HttpResponseMessage Clients() => Json(new { status = true, named_certs = new[] { new { name = "Tablet" } } });

    private sealed class FakeHandler(params HttpResponseMessage[] responses) : HttpMessageHandler
    {
        private readonly Queue<HttpResponseMessage> _responses = new(responses);
        public List<string> Paths { get; } = [];
        public bool PairPayloadVerified { get; private set; }
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct)
        {
            if (request.RequestUri?.Host != "127.0.0.1" || request.RequestUri.Scheme != "https")
                throw new InvalidOperationException("Unexpected target");
            Paths.Add($"{request.Method} {request.RequestUri.AbsolutePath}");
            if (request.RequestUri.AbsolutePath == "/api/pin" && request.Content is not null)
            {
                using var json = System.Text.Json.JsonDocument.Parse(await request.Content.ReadAsByteArrayAsync(ct));
                PairPayloadVerified = json.RootElement.GetProperty("pin").GetString() == "0123"
                    && json.RootElement.GetProperty("name").GetString() == "Test Tablet";
            }
            return _responses.Dequeue();
        }
    }
}
