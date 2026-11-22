using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Principal;
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
            RegistryRestart(dir, now);
            FailureClosesReaders(now);
            File.WriteAllBytes(Path.Combine(dir, "grants.dpapi"), [1, 2, 3]);
            using (var store = new ProtectedGrantStore(dir))
                Check(Reject(() => store.Load(now)), "Corrupted protected data rejected");
            File.WriteAllBytes(Path.Combine(dir, "transaction.pending"), [1]);
            Check(Reject(() => { using var store = new ProtectedGrantStore(dir); }), "Interrupted transaction rejected");
            File.Delete(Path.Combine(dir, "transaction.pending"));
            UnsafeFileAcl(dir);
            UnsafeDirectoryAcl(dir);
            ReparseDirectory(dir);
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine($"FAIL: protected grant store ({ex.GetType().Name})"); return 1; }
        finally { if (Directory.Exists(dir)) Directory.Delete(dir, true); }
    }

    [SupportedOSPlatform("windows")]
    private static void RegistryRestart(string dir, DateTimeOffset now)
    {
        IssuedDevice issued;
        using (var store = new ProtectedGrantStore(dir))
        {
            var registry = new DeviceRegistry(new string('B', 64), store);
            issued = registry.Issue("Tablet", now)!;
        }
        var token = Encoding.ASCII.GetBytes(issued.Token);
        using (var store = new ProtectedGrantStore(dir))
        {
            var registry = new DeviceRegistry(new string('C', 64), store);
            Check(registry.Authenticate(token, false, now) is { Owner: false }, "Reader survives registry reopen");
            Check(registry.Authenticate(Encoding.ASCII.GetBytes(new string('B', 64)), true, now) is null, "Old owner not persisted");
            Check(registry.Revoke(issued.Device.Id), "Protected revocation committed");
        }
        using (var store = new ProtectedGrantStore(dir))
        {
            var registry = new DeviceRegistry(new string('D', 64), store);
            Check(registry.Authenticate(token, false, now) is null && registry.List(now).Length == 0, "Revocation survives reopen");
            registry.Issue("One", now);
            registry.Issue("Two", now);
            registry.RevokeAll();
        }
        using (var store = new ProtectedGrantStore(dir))
            Check(store.Load(now).Length == 0, "Revoke-all survives reopen");
    }

    private static void FailureClosesReaders(DateTimeOffset now)
    {
        using var store = new FailingStore();
        var registry = new DeviceRegistry(new string('B', 64), store);
        var issued = registry.Issue("Fixture", now)!;
        var token = Encoding.ASCII.GetBytes(issued.Token);
        var grant = registry.Authenticate(token, false, now)!;
        store.Fail = true;
        bool rejected = false;
        try { registry.Revoke(issued.Device.Id); } catch (GrantStoreUnavailableException) { rejected = true; }
        Check(rejected && registry.StorageStatus == "unavailable" && !registry.Active(grant, now)
            && registry.Authenticate(token, false, now) is null, "Write failure disables active reader grants");
    }

    private sealed class FailingStore : IGrantStore
    {
        public bool Fail;
        public StoredGrant[] Load(DateTimeOffset now) => [];
        public void Save(StoredGrant[] grants, DateTimeOffset now)
        { if (Fail) throw new IOException("Fixture write failure"); }
        public void Dispose() { }
    }

    [SupportedOSPlatform("windows")]
    private static void UnsafeFileAcl(string dir)
    {
        var file = new FileInfo(Path.Combine(dir, "grants.dpapi"));
        var security = file.GetAccessControl();
        var world = new SecurityIdentifier(WellKnownSidType.WorldSid, null);
        var rule = new FileSystemAccessRule(world, FileSystemRights.ReadData, AccessControlType.Allow);
        security.AddAccessRule(rule);
        file.SetAccessControl(security);
        try { Check(Reject(() => { using var store = new ProtectedGrantStore(dir); }), "Unexpected file ACL rejected"); }
        finally { security.RemoveAccessRuleSpecific(rule); file.SetAccessControl(security); }
    }

    [SupportedOSPlatform("windows")]
    private static void UnsafeDirectoryAcl(string dir)
    {
        var info = new DirectoryInfo(dir);
        var security = info.GetAccessControl();
        var world = new SecurityIdentifier(WellKnownSidType.WorldSid, null);
        var rule = new FileSystemAccessRule(world, FileSystemRights.ListDirectory, AccessControlType.Allow);
        security.AddAccessRule(rule);
        info.SetAccessControl(security);
        try { Check(Reject(() => { using var store = new ProtectedGrantStore(dir); }), "Unexpected directory ACL rejected"); }
        finally { security.RemoveAccessRuleSpecific(rule); info.SetAccessControl(security); }
    }

    [SupportedOSPlatform("windows")]
    private static void ReparseDirectory(string dir)
    {
        var link = dir + "-link";
        try { Directory.CreateSymbolicLink(link, dir); }
        catch (Exception ex) when (ex is UnauthorizedAccessException or IOException or PlatformNotSupportedException)
        { Console.WriteLine("SKIP: symlink creation unavailable"); return; }
        try { Check(Reject(() => { using var store = new ProtectedGrantStore(link); }), "Reparse store directory rejected"); }
        finally { Directory.Delete(link); }
    }

    private static bool Reject(Action action)
    {
        try { action(); return false; }
        catch (Exception ex) when (ex is IOException or InvalidDataException or UnauthorizedAccessException or CryptographicException) { return true; }
    }
    private static void Check(bool valid, string name)
    {
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} {name}");
        if (!valid) throw new InvalidOperationException(name);
    }
}
