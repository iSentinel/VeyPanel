using System.Net;
using System.Security.Cryptography;
using System.Text;

namespace VeyPanel.Host;

internal sealed record DeviceInfo(Guid Id, string Name, DateTimeOffset ExpiresUtc);
internal sealed record IssuedDevice(DeviceInfo Device, string Token);
internal sealed record DeviceGrant(Guid Id, bool Owner);
internal sealed class GrantStoreUnavailableException : Exception
{
    internal GrantStoreUnavailableException() : base("Reader grant store unavailable") { }
}
internal sealed class DeviceRegistry
{
    private const int Capacity = 32;
    private readonly byte[] ownerHash;
    private readonly object gate = new();
    private readonly Dictionary<Guid, (DeviceInfo Info, byte[] Hash)> entries = new();

    private readonly IGrantStore? store;
    private bool storeFailed;

    internal DeviceRegistry(string ownerToken, IGrantStore? store = null)
    {
        ownerHash = SHA256.HashData(Encoding.ASCII.GetBytes(ownerToken));
        this.store = store;
        if (store is null) return;
        foreach (var grant in store.Load(DateTimeOffset.UtcNow))
            entries.Add(grant.Device.Id, (grant.Device, Convert.FromHexString(grant.Sha256)));
    }

    internal string StorageStatus
    {
        get { lock (gate) return storeFailed ? "unavailable" : store is null ? "ephemeral" : "protected"; }
    }

    private void EnsureStore()
    {
        if (storeFailed) throw new GrantStoreUnavailableException();
    }

    private void Commit(DateTimeOffset now)
    {
        if (store is null) return;
        try
        {
            store.Save(entries.Values.Select(e => new StoredGrant(e.Info, Convert.ToHexString(e.Hash))).ToArray(), now);
        }
        catch (Exception)
        {
            // A failed write must not acknowledge issuance/revocation or leave live readers active.
            storeFailed = true;
            entries.Clear();
            throw new GrantStoreUnavailableException();
        }
    }

    internal static bool LocalOwner(HttpContext context) =>
        !context.Request.IsHttps && context.Connection.LocalPort == 47860
        && IPAddress.IsLoopback(context.Connection.LocalIpAddress ?? IPAddress.None)
        && IPAddress.IsLoopback(context.Connection.RemoteIpAddress ?? IPAddress.None);

    internal static bool ValidName(string? name) => name is { Length: >= 1 and <= 64 }
        && name == name.Trim() && !name.Any(char.IsControl);

    internal IssuedDevice? Issue(string name, DateTimeOffset now)
    {
        if (!ValidName(name)) throw new ArgumentException("Invalid device name");
        lock (gate)
        {
            EnsureStore();
            Purge(now);
            if (entries.Count >= Capacity) return null;
            var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
            var info = new DeviceInfo(Guid.NewGuid(), name, now.AddHours(24));
            entries.Add(info.Id, (info, SHA256.HashData(Encoding.ASCII.GetBytes(token))));
            Commit(now);
            return new(info, token);
        }
    }

    internal DeviceGrant? Authenticate(ReadOnlySpan<byte> token, bool local, DateTimeOffset now)
    {
        if (token.Length != 64) return null;
        foreach (var c in token) if (!(c is >= 48 and <= 57 or >= 65 and <= 70)) return null;
        var hash = SHA256.HashData(token);
        if (local && CryptographicOperations.FixedTimeEquals(hash, ownerHash)) return new(Guid.Empty, true);
        lock (gate)
        {
            if (storeFailed) return null;
            Purge(now);
            foreach (var (id, entry) in entries)
                if (CryptographicOperations.FixedTimeEquals(hash, entry.Hash)) return new(id, false);
        }
        return null;
    }

    internal bool Active(DeviceGrant grant, DateTimeOffset now)
    {
        if (grant.Owner) return true;
        lock (gate) return !storeFailed && entries.TryGetValue(grant.Id, out var entry) && entry.Info.ExpiresUtc > now;
    }

    internal DeviceInfo[] List(DateTimeOffset now)
    {
        lock (gate) { EnsureStore(); Purge(now); return entries.Values.Select(e => e.Info).OrderBy(e => e.ExpiresUtc).ToArray(); }
    }

    internal bool Revoke(Guid id)
    {
        lock (gate)
        {
            EnsureStore();
            var now = DateTimeOffset.UtcNow;
            Purge(now);
            if (!entries.Remove(id)) return false;
            Commit(now);
            return true;
        }
    }

    internal void RevokeAll()
    {
        lock (gate)
        {
            EnsureStore();
            entries.Clear();
            Commit(DateTimeOffset.UtcNow);
        }
    }

    private void Purge(DateTimeOffset now)
    {
        foreach (var id in entries.Where(e => e.Value.Info.ExpiresUtc <= now).Select(e => e.Key).ToArray())
            entries.Remove(id);
    }
}
