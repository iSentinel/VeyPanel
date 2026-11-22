using System.Security.Cryptography;
using System.Text;
using VeyPanel.Host;

internal static class GrantStoreTests
{
    internal static int Run()
    {
        var now = DateTimeOffset.UtcNow;
        var token = new string('A', 64);
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(token)));
        var device = new DeviceInfo(Guid.NewGuid(), "Lenovo test", now.AddHours(1));
        var row = new StoredGrant(device, hash);
        var bytes = GrantStoreCodec.Encode([row], now);
        var text = Encoding.UTF8.GetString(bytes);
        var ok = GrantStoreCodec.Decode(bytes, now).SequenceEqual(new[] { row })
            && !text.Contains(token) && text.Contains(hash)
            && GrantStoreCodec.Decode(bytes, now.AddHours(2)).Length == 0;
        ok &= Reject(() => GrantStoreCodec.Encode([row, row], now))
            && Reject(() => GrantStoreCodec.Encode([row with { Sha256 = "bad" }], now))
            && Reject(() => GrantStoreCodec.Encode([row with { Device = device with { Id = Guid.Empty } }], now))
            && Reject(() => GrantStoreCodec.Decode(Encoding.UTF8.GetBytes(text.Replace("\"schemaVersion\":1", "\"schemaVersion\":2")), now))
            && Reject(() => GrantStoreCodec.Decode(Encoding.UTF8.GetBytes(text.Replace("\"schemaVersion\":1", "\"schemaVersion\":1,\"schemaVersion\":1")), now))
            && Reject(() => GrantStoreCodec.Decode(Encoding.UTF8.GetBytes(text.Replace("\"sha256\":", "\"token\":")), now))
            && Reject(() => GrantStoreCodec.Decode(new byte[GrantStoreCodec.MaxBytes + 1], now))
            && Reject(() => GrantStoreCodec.Decode(Encoding.UTF8.GetBytes("{\"schemaVersion\":1,\"grants\":[null]}"), now));
        Console.WriteLine($"{(ok ? "PASS" : "FAIL")} Grant store schema, expiry, duplicates, privacy and corruption");
        return ok ? 0 : 1;
    }

    private static bool Reject(Action action)
    {
        try { action(); return false; }
        catch (InvalidDataException) { return true; }
    }
}
