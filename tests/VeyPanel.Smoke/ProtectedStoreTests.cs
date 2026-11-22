using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Text;
using VeyPanel.Host;

internal static class ProtectedStoreTests
{
    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) { Console.WriteLine("SKIP DPAPI: Windows required"); return 0; }
        return RunWindows();
    }

    [SupportedOSPlatform("windows")]
    private static int RunWindows()
    {
        var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "VeyPanel-store-test-" + Guid.NewGuid().ToString("N"));
        try
        {
            var now = DateTimeOffset.UtcNow;
            var hash = Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(new string('A', 64))));
            var row = new StoredGrant(new DeviceInfo(Guid.NewGuid(), "Fixture", now.AddHours(1)), hash);
            using (var store = new ProtectedGrantStore(dir))
            {
                Check(store.Load(now).Length == 0, "New protected store empty");
                store.Save([row], now);
                Check(Reject(() => { using var second = new ProtectedGrantStore(dir); }), "Exclusive store lock");
                Check(!Encoding.UTF8.GetString(File.ReadAllBytes(Path.Combine(dir, "grants.dpapi"))).Contains(hash), "DPAPI ciphertext");
            }
            using (var store = new ProtectedGrantStore(dir))
            {
                Check(store.Load(now).SequenceEqual(new[] { row }), "DPAPI reopen");
                store.Save([], now);
            }
            using (var store = new ProtectedGrantStore(dir))
                Check(store.Load(now).Length == 0, "Empty replacement survives reopen");
            File.WriteAllBytes(Path.Combine(dir, "grants.dpapi"), [1, 2, 3]);
            using (var store = new ProtectedGrantStore(dir))
                Check(Reject(() => store.Load(now)), "Corrupted protected data rejected");
            File.WriteAllBytes(Path.Combine(dir, "transaction.pending"), [1]);
            Check(Reject(() => { using var store = new ProtectedGrantStore(dir); }), "Interrupted transaction rejected");
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine($"FAIL: protected grant store ({ex.GetType().Name})"); return 1; }
        finally { if (Directory.Exists(dir)) Directory.Delete(dir, true); }
    }

    private static bool Reject(Action action)
    {
        try { action(); return false; }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or CryptographicException) { return true; }
    }
    private static void Check(bool valid, string name)
    {
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} {name}");
        if (!valid) throw new InvalidOperationException(name);
    }
}
