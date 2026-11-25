using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Principal;
using VeyPanel.Shared;

internal static class MaintenanceLeaseAclSmoke
{
    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) return 1;
        try
        {
            Exercise();
            Console.WriteLine("PASS: isolated owner-only lease ACL");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: lease ACL fixture (" + error.GetType().Name + ")");
            return 1;
        }
    }

    [SupportedOSPlatform("windows")]
    private static void Exercise()
    {
        using var identity = WindowsIdentity.GetCurrent();
        var owner = identity.User ?? throw new InvalidOperationException("Fixture owner unavailable.");
        var root = new DirectoryInfo(Path.Combine(Path.GetTempPath(), "veypanel-acl-" + Guid.NewGuid().ToString("N")));
        if (root.Exists || File.Exists(root.FullName)) throw new IOException("Fixture root exists.");
        var directoryAcl = new DirectorySecurity();
        Configure(directoryAcl, owner, true);
        root.Create(directoryAcl);
        var file = new FileInfo(Path.Combine(root.FullName, "lease.fixture"));
        try
        {
            using (var stream = new FileStream(file.FullName, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                stream.Write([0x56, 0x50]);
            var fileAcl = new FileSecurity();
            Configure(fileAcl, owner, false);
            file.SetAccessControl(fileAcl);
            Check(root, file, owner);
            Console.WriteLine("PASS: protected owner-only directory and held lease DACL");
            CheckUnexpectedRule(root, file, owner, false);
            CheckUnexpectedRule(root, file, owner, true);
            CheckInheritance(root, file, owner);
            Check(root, file, owner);
            if (!File.ReadAllBytes(file.FullName).SequenceEqual(new byte[] { 0x56, 0x50 }))
                throw new IOException("Fixture bytes changed.");
            Console.WriteLine("PASS: restored fixture ACL and unchanged bytes");
        }
        finally
        {
            file.Delete();
            root.Delete();
        }
    }

    [SupportedOSPlatform("windows")]
    private static void Configure(FileSystemSecurity acl, SecurityIdentifier owner, bool directory)
    {
        acl.SetOwner(owner);
        acl.SetAccessRuleProtection(true, false);
        acl.AddAccessRule(new FileSystemAccessRule(owner, FileSystemRights.FullControl,
            directory ? InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit : InheritanceFlags.None,
            PropagationFlags.None, AccessControlType.Allow));
    }

    [SupportedOSPlatform("windows")]
    private static void Check(DirectoryInfo root, FileInfo file, SecurityIdentifier owner)
    {
        MaintenanceLeaseAcl.RequireOwnerOnly(root.GetAccessControl(AccessControlSections.Owner | AccessControlSections.Access),
            owner, true);
        using var lease = MaintenanceLease.TryOpen(file.FullName, false)
            ?? throw new IOException("ACL fixture lease busy.");
        MaintenanceLeaseAcl.RequireOwnerOnly(lease.GetAccessControl(), owner, false);
    }

    [SupportedOSPlatform("windows")]
    private static void CheckUnexpectedRule(DirectoryInfo root, FileInfo file, SecurityIdentifier owner, bool directory)
    {
        var world = new SecurityIdentifier(WellKnownSidType.WorldSid, null);
        var rule = new FileSystemAccessRule(world, FileSystemRights.ReadData, AccessControlType.Allow);
        var acl = directory ? (FileSystemSecurity)root.GetAccessControl() : file.GetAccessControl();
        acl.AddAccessRule(rule);
        if (directory) root.SetAccessControl((DirectorySecurity)acl);
        else file.SetAccessControl((FileSecurity)acl);
        try
        {
            RequireRefused(() => Check(root, file, owner));
            Console.WriteLine(directory ? "PASS: unexpected directory ACE refused" : "PASS: unexpected held-file ACE refused");
        }
        finally
        {
            acl.RemoveAccessRuleSpecific(rule);
            if (directory) root.SetAccessControl((DirectorySecurity)acl);
            else file.SetAccessControl((FileSecurity)acl);
        }
    }

    [SupportedOSPlatform("windows")]
    private static void CheckInheritance(DirectoryInfo root, FileInfo file, SecurityIdentifier owner)
    {
        var original = file.GetAccessControl();
        var modified = file.GetAccessControl();
        modified.SetAccessRuleProtection(false, false);
        file.SetAccessControl(modified);
        try
        {
            RequireRefused(() => Check(root, file, owner));
            Console.WriteLine("PASS: unprotected lease DACL refused");
        }
        finally
        {
            // Build a new descriptor so the Access section is marked modified.
            var restored = new FileSecurity();
            restored.SetSecurityDescriptorBinaryForm(original.GetSecurityDescriptorBinaryForm(),
                AccessControlSections.Access);
            file.SetAccessControl(restored);
        }
    }

    private static void RequireRefused(Action action)
    {
        try { action(); }
        catch (UnauthorizedAccessException) { return; }
        throw new InvalidOperationException("Unsafe fixture ACL admitted.");
    }
}
