using System.Text.Json;

namespace VeyPanel.Host;

// Serialization boundary for a future protected, atomic grant store.
// Not wired to the live registry; no files or raw tokens are persisted.
internal sealed record StoredGrant(DeviceInfo Device, string Sha256);

internal static class GrantStoreCodec
{
    internal const int MaxBytes = 32 * 1024;
    private const int Capacity = 32;
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);

    internal static byte[] Encode(StoredGrant[] grants, DateTimeOffset now)
    {
        if (!Validate(grants, now)) throw new InvalidDataException("Invalid grant store");
        var bytes = JsonSerializer.SerializeToUtf8Bytes(new { schemaVersion = 1, grants }, Json);
        if (bytes.Length > MaxBytes) throw new InvalidDataException("Grant store size");
        return bytes;
    }

    internal static StoredGrant[] Decode(ReadOnlyMemory<byte> bytes, DateTimeOffset now)
    {
        if (bytes.Length is < 1 or > MaxBytes) throw new InvalidDataException("Grant store size");
        try
        {
            using var json = JsonDocument.Parse(bytes, new JsonDocumentOptions { MaxDepth = 8 });
            var root = json.RootElement;
            if (!ExactKeys(root, "schemaVersion", "grants")
                || root.GetProperty("schemaVersion").GetInt32() != 1)
                throw new InvalidDataException("Invalid grant schema");
            var rows = root.GetProperty("grants");
            if (rows.ValueKind != JsonValueKind.Array || rows.GetArrayLength() > Capacity)
                throw new InvalidDataException("Grant count");
            foreach (var row in rows.EnumerateArray())
                if (!ExactKeys(row, "device", "sha256")
                    || !ExactKeys(row.GetProperty("device"), "id", "name", "expiresUtc"))
                    throw new InvalidDataException("Unexpected grant fields");
            var grants = rows.Deserialize<StoredGrant[]>(Json) ?? throw new InvalidDataException("Missing grants");
            if (!Validate(grants, now)) throw new InvalidDataException("Invalid grants");
            return grants.Where(g => g.Device.ExpiresUtc > now).ToArray();
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or FormatException)
        { throw new InvalidDataException("Invalid grant document", ex); }
    }

    private static bool Validate(StoredGrant[] grants, DateTimeOffset now)
    {
        if (grants.Length > Capacity) return false;
        var ids = new HashSet<Guid>();
        var hashes = new HashSet<string>(StringComparer.Ordinal);
        foreach (var grant in grants)
        {
            if (grant?.Device is not { } device || device.Id == Guid.Empty || !ids.Add(device.Id)
                || !DeviceRegistry.ValidName(device.Name) || device.ExpiresUtc > now.AddHours(24)
                || device.ExpiresUtc.Offset != TimeSpan.Zero
                || grant.Sha256 is not { Length: 64 } hash || !hash.All(c => c is >= '0' and <= '9' or >= 'A' and <= 'F')
                || !hashes.Add(hash)) return false;
        }
        return true;
    }

    private static bool ExactKeys(JsonElement value, params string[] keys)
    {
        if (value.ValueKind != JsonValueKind.Object) return false;
        var remaining = new HashSet<string>(keys, StringComparer.Ordinal);
        foreach (var property in value.EnumerateObject())
            if (!remaining.Remove(property.Name)) return false;
        return remaining.Count == 0;
    }
}
