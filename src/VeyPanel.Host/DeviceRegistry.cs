using System.Net;
using System.Security.Cryptography;
using System.Text;

namespace VeyPanel.Host;

internal sealed record DeviceInfo(Guid Id, string Name, DateTimeOffset ExpiresUtc);
internal sealed record IssuedDevice(DeviceInfo Device, string Token);
internal sealed record DeviceGrant(Guid Id, bool Owner);
internal sealed class DeviceRegistry
{
    private const int Capacity = 32;
    private readonly byte[] ownerHash;
    private readonly object gate = new();
    private readonly Dictionary<Guid, (DeviceInfo Info, byte[] Hash)> entries = new();

    internal DeviceRegistry(string ownerToken) => ownerHash = SHA256.HashData(Encoding.ASCII.GetBytes(ownerToken));

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
            Purge(now);
            if (entries.Count >= Capacity) return null;
            var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
            var info = new DeviceInfo(Guid.NewGuid(), name, now.AddHours(24));
            entries.Add(info.Id, (info, SHA256.HashData(Encoding.ASCII.GetBytes(token))));
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
            Purge(now);
            foreach (var (id, entry) in entries)
                if (CryptographicOperations.FixedTimeEquals(hash, entry.Hash)) return new(id, false);
        }
        return null;
    }

    internal bool Active(DeviceGrant grant, DateTimeOffset now)
    {
        if (grant.Owner) return true;
        lock (gate) return entries.TryGetValue(grant.Id, out var entry) && entry.Info.ExpiresUtc > now;
    }

    internal DeviceInfo[] List(DateTimeOffset now)
    {
        lock (gate) { Purge(now); return entries.Values.Select(e => e.Info).OrderBy(e => e.ExpiresUtc).ToArray(); }
    }

    internal bool Revoke(Guid id)
    {
        lock (gate) return entries.Remove(id);
    }

    private void Purge(DateTimeOffset now)
    {
        foreach (var id in entries.Where(e => e.Value.Info.ExpiresUtc <= now).Select(e => e.Key).ToArray())
            entries.Remove(id);
    }
}
