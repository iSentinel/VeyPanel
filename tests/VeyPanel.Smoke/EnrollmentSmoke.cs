using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

internal static class EnrollmentSmoke
{
    internal static async Task RunAsync(HttpClient lan, string ownerToken, Uri root)
    {
        using var owner = new HttpClient(new HttpClientHandler { UseProxy = false })
        { BaseAddress = new Uri("http://127.0.0.1:47860/"), Timeout = TimeSpan.FromSeconds(5) };
        owner.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", ownerToken);
        lan.DefaultRequestHeaders.Authorization = null;
        using var created = await Post(owner, "api/v1/devices/invitations", new { name = "Enrollment fixture" });
        Check(created.StatusCode == HttpStatusCode.Created, "Owner invitation created");
        using var issue = JsonDocument.Parse(await created.Content.ReadAsByteArrayAsync());
        var url = new Uri(issue.RootElement.GetProperty("url").GetString()!);
        Check(url.GetLeftPart(UriPartial.Authority) == root.GetLeftPart(UriPartial.Authority)
            && url.AbsolutePath == "/enroll.html", "Invitation bound to LAN origin");
        var png = Convert.FromBase64String(issue.RootElement.GetProperty("qrPng").GetString()!);
        Check(png.Length > 32 && png.Take(8).SequenceEqual(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 })
            && System.Buffers.Binary.BinaryPrimitives.ReadInt32BigEndian(png.AsSpan(16, 4))
                == System.Buffers.Binary.BinaryPrimitives.ReadInt32BigEndian(png.AsSpan(20, 4)), "Local QR PNG generated");
        var id = issue.RootElement.GetProperty("invitation").GetProperty("id").GetGuid();
        var secret = url.Fragment.Split("&secret=")[1];
        using var page = await lan.GetAsync("enroll.html");
        Check(page.IsSuccessStatusCode, "Enrollment page packaged");
        using var local = await Post(owner, "api/v1/enroll/claim", new { id, secret });
        Check(local.StatusCode == HttpStatusCode.Forbidden, "HTTP enrollment denied");
        using var claim = await Post(lan, "api/v1/enroll/claim", new { id, secret });
        Check(claim.StatusCode == HttpStatusCode.OK, "HTTPS invitation claimed");
        using var body = JsonDocument.Parse(await claim.Content.ReadAsByteArrayAsync());
        var claimSecret = body.RootElement.GetProperty("secret").GetString();
        var code = body.RootElement.GetProperty("code").GetString();
        using var replay = await Post(lan, "api/v1/enroll/claim", new { id, secret });
        Check(replay.StatusCode == HttpStatusCode.NotFound, "Invitation replay denied");
        await FinishAsync(owner, lan, id, claimSecret!, code!);
    }

    private static async Task FinishAsync(HttpClient owner, HttpClient lan, Guid id, string secret, string code)
    {
        using var pending = await Post(lan, "api/v1/enroll/finish", new { id, secret });
        Check(pending.StatusCode == HttpStatusCode.Accepted, "No grant before approval");
        using var wrong = await Post(owner, $"api/v1/devices/invitations/{id}/approve", new { code = "wrong" });
        Check(wrong.StatusCode == HttpStatusCode.Conflict, "Wrong comparison code rejected");
        using var approved = await Post(owner, $"api/v1/devices/invitations/{id}/approve", new { code });
        Check(approved.StatusCode == HttpStatusCode.NoContent, "Owner approved");
        using var finished = await Post(lan, "api/v1/enroll/finish", new { id, secret });
        Check(finished.StatusCode == HttpStatusCode.Created, "Reader grant redeemed");
        using var grant = JsonDocument.Parse(await finished.Content.ReadAsByteArrayAsync());
        using var replay = await Post(lan, "api/v1/enroll/finish", new { id, secret });
        Check(replay.StatusCode == HttpStatusCode.NotFound, "Grant replay denied");
        lan.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", grant.RootElement.GetProperty("token").GetString());
        using var telemetry = await lan.GetAsync("api/v1/telemetry");
        Check(telemetry.IsSuccessStatusCode, "New reader receives telemetry");
        using var admin = await lan.GetAsync("api/v1/devices/invitations");
        Check(admin.StatusCode == HttpStatusCode.Forbidden, "New reader cannot administer");
    }

    private static async Task<HttpResponseMessage> Post(HttpClient client, string path, object body)
    {
        using var content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
        return await client.PostAsync(path, content);
    }
    private static void Check(bool valid, string label)
    {
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")}: {label}");
        if (!valid) throw new InvalidOperationException(label);
    }
}
