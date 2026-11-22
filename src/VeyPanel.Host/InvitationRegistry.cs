using System.Security.Cryptography;
using System.Text;

namespace VeyPanel.Host;

internal sealed record InvitationInfo(Guid Id, string Name, DateTimeOffset ExpiresUtc, string State, string? Code);
internal sealed record InvitationIssued(InvitationInfo Invitation, string Secret);
internal sealed record InvitationClaim(Guid Id, string Secret, string Code, DateTimeOffset ExpiresUtc);
internal sealed record Redemption(string State, IssuedDevice? Device);

internal sealed class InvitationRegistry(DeviceRegistry devices)
{
    private sealed record Entry(InvitationInfo Info, byte[] Hash);
    private readonly object gate = new();
    private readonly Dictionary<Guid, Entry> entries = new();
    internal const int Capacity = 8;

    internal InvitationIssued? Create(string name, DateTimeOffset now)
    {
        if (!DeviceRegistry.ValidName(name)) return null;
        lock (gate)
        {
            Purge(now);
            if (entries.Count >= Capacity) return null;
            var secret = NewSecret();
            var info = new InvitationInfo(Guid.NewGuid(), name, now.AddMinutes(2), "invited", null);
            entries.Add(info.Id, new(info, Hash(secret)));
            return new(info, secret);
        }
    }

    internal InvitationClaim? Claim(Guid id, string secret, DateTimeOffset now)
    {
        lock (gate)
        {
            Purge(now);
            if (!entries.TryGetValue(id, out var entry) || entry.Info.State != "invited"
                || !Matches(entry, secret)) return null;
            var claim = NewSecret();
            var code = RandomNumberGenerator.GetInt32(0, 1000000).ToString("D6", System.Globalization.CultureInfo.InvariantCulture);
            entries[id] = new(entry.Info with { State = "pending", Code = code }, Hash(claim));
            return new(id, claim, code, entry.Info.ExpiresUtc);
        }
    }

    internal bool Approve(Guid id, string code, DateTimeOffset now)
    {
        lock (gate)
        {
            Purge(now);
            if (!entries.TryGetValue(id, out var entry) || entry.Info.State != "pending"
                || code != entry.Info.Code) return false;
            entries[id] = entry with { Info = entry.Info with { State = "approved" } };
            return true;
        }
    }

    internal Redemption Finish(Guid id, string secret, DateTimeOffset now)
    {
        lock (gate)
        {
            Purge(now);
            if (!entries.TryGetValue(id, out var entry) || entry.Info.State == "invited"
                || !Matches(entry, secret)) return new("unavailable", null);
            if (entry.Info.State != "approved") return new("pending", null);
            var issued = devices.Issue(entry.Info.Name, now);
            if (issued is null) return new("capacity", null);
            entries.Remove(id);
            return new("issued", issued);
        }
    }

    internal InvitationInfo[] List(DateTimeOffset now)
    {
        lock (gate) { Purge(now); return entries.Values.Select(e => e.Info).ToArray(); }
    }

    internal bool Cancel(Guid id)
    {
        lock (gate) return entries.Remove(id);
    }

    private void Purge(DateTimeOffset now)
    {
        foreach (var id in entries.Where(e => e.Value.Info.ExpiresUtc <= now).Select(e => e.Key).ToArray())
            entries.Remove(id);
    }

    private static string NewSecret() => Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
    private static byte[] Hash(string secret) => SHA256.HashData(Encoding.ASCII.GetBytes(secret));
    private static bool Matches(Entry entry, string secret) =>
        secret.Length == 64 && secret.All(c => c is >= '0' and <= '9' or >= 'A' and <= 'F')
        && CryptographicOperations.FixedTimeEquals(entry.Hash, Hash(secret));
}
