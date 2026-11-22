using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;

namespace VeyPanel.Host;

internal interface IGrantStore : IDisposable
{
    StoredGrant[] Load(DateTimeOffset now);
    void Save(StoredGrant[] grants, DateTimeOffset now);
}

[SupportedOSPlatform("windows")]
internal sealed class ProtectedGrantStore : IGrantStore, IDisposable
{
    private const int MaxProtectedBytes = 64 * 1024;
    private static readonly byte[] Entropy = Encoding.UTF8.GetBytes("VeyPanel/reader-grants/v1");
    private readonly string directory, data, marker, temporary;
    private readonly FileStream processLock;
    private bool failed;

    internal static ProtectedGrantStore OpenDefault()
    {
        var root = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrWhiteSpace(root)) throw new IOException("Local profile unavailable");
        return new(Path.Combine(root, "VeyPanel-GrantStore-v1"));
    }

    // Internal path override is for isolated tests only; not a network or CLI setting.
    internal ProtectedGrantStore(string path)
    {
        directory = Path.GetFullPath(path);
        data = Path.Combine(directory, "grants.dpapi");
        marker = Path.Combine(directory, "transaction.pending");
        temporary = Path.Combine(directory, "grants.new");
        PrepareDirectory();
        var lockPath = Path.Combine(directory, "owner.lock");
        CheckFile(lockPath);
        processLock = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        try
        {
            CheckFile(data); CheckFile(marker); CheckFile(temporary);
            if (Exists(marker) || Exists(temporary)) throw new InvalidDataException("Interrupted grant transaction");
        }
        catch { processLock.Dispose(); throw; }
    }

    private void PrepareDirectory()
    {
        var dir = new DirectoryInfo(directory);
        for (var ancestor = dir.Parent; ancestor is not null; ancestor = ancestor.Parent)
            if ((File.GetAttributes(ancestor.FullName) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Reparse-point ancestor");
        using var identity = WindowsIdentity.GetCurrent();
        var user = identity.User ?? throw new InvalidOperationException("Windows identity unavailable");
        var security = new DirectorySecurity();
        security.SetOwner(user);
        security.SetAccessRuleProtection(true, false);
        security.AddAccessRule(new FileSystemAccessRule(user, FileSystemRights.FullControl,
            InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
        if (!Exists(directory)) dir.Create(security);
        if ((File.GetAttributes(directory) & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != FileAttributes.Directory)
            throw new IOException("Unsafe grant directory");
        var actual = dir.GetAccessControl(AccessControlSections.Owner | AccessControlSections.Access);
        if (!actual.AreAccessRulesProtected || !user.Equals(actual.GetOwner(typeof(SecurityIdentifier))))
            throw new UnauthorizedAccessException("Grant directory owner or inheritance");
        var rules = actual.GetAccessRules(true, true, typeof(SecurityIdentifier)).Cast<FileSystemAccessRule>().ToArray();
        if (rules.Length != 1 || !user.Equals(rules[0].IdentityReference) || rules[0].IsInherited
            || rules[0].AccessControlType != AccessControlType.Allow
            || rules[0].FileSystemRights != FileSystemRights.FullControl
            || rules[0].InheritanceFlags != (InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit)
            || rules[0].PropagationFlags != PropagationFlags.None)
            throw new UnauthorizedAccessException("Grant directory ACL");
    }

    public StoredGrant[] Load(DateTimeOffset now)
    {
        EnsureUsable();
        CheckFile(data);
        if (!Exists(data)) return [];
        using var stream = new FileStream(data, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (stream.Length is < 1 or > MaxProtectedBytes) throw new InvalidDataException("Protected grant size");
        var encrypted = new byte[(int)stream.Length];
        stream.ReadExactly(encrypted);
        if (stream.ReadByte() != -1) throw new InvalidDataException("Grant file changed");
        var plain = ProtectedData.Unprotect(encrypted, Entropy, DataProtectionScope.CurrentUser);
        try { return GrantStoreCodec.Decode(plain, now); }
        finally { CryptographicOperations.ZeroMemory(plain); }
    }

    public void Save(StoredGrant[] grants, DateTimeOffset now)
    {
        EnsureUsable();
        var plain = GrantStoreCodec.Encode(grants, now);
        try
        {
            // Mark the transaction before changing the authoritative data. An interrupted
            // transaction refuses recovery rather than choosing an older credential set.
            WriteNew(marker, [1]);
            var encrypted = ProtectedData.Protect(plain, Entropy, DataProtectionScope.CurrentUser);
            if (encrypted.Length > MaxProtectedBytes) throw new InvalidDataException("Protected grant size");
            WriteNew(temporary, encrypted);
            CheckFile(data);
            File.Move(temporary, data, overwrite: true);
            File.Delete(marker);
        }
        catch { failed = true; throw; }
        finally { CryptographicOperations.ZeroMemory(plain); }
    }

    private void EnsureUsable()
    {
        ObjectDisposedException.ThrowIf(processLock.SafeFileHandle.IsClosed, this);
        if (failed || Exists(marker) || Exists(temporary)) throw new InvalidDataException("Grant store not usable");
    }

    private static void WriteNew(string path, byte[] bytes)
    {
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough);
        stream.Write(bytes);
        stream.Flush(flushToDisk: true);
    }

    private static void CheckFile(string path)
    {
        if (!Exists(path)) return;
        if ((File.GetAttributes(path) & (FileAttributes.ReparsePoint | FileAttributes.Directory)) != 0)
            throw new IOException("Unsafe grant store file");
        using var identity = WindowsIdentity.GetCurrent();
        var user = identity.User ?? throw new UnauthorizedAccessException("Windows identity unavailable");
        var acl = new FileInfo(path).GetAccessControl(AccessControlSections.Access);
        var rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier)).Cast<FileSystemAccessRule>().ToArray();
        if (rules.Length == 0 || rules.Any(rule => !user.Equals(rule.IdentityReference)
            || rule.AccessControlType != AccessControlType.Allow)
            || !rules.Any(rule => (rule.FileSystemRights & FileSystemRights.FullControl) == FileSystemRights.FullControl))
            throw new UnauthorizedAccessException("Grant file ACL");
    }

    private static bool Exists(string path)
    {
        try { _ = File.GetAttributes(path); return true; }
        catch (FileNotFoundException) { return false; }
        catch (DirectoryNotFoundException) { return false; }
    }

    public void Dispose() => processLock.Dispose();
}
