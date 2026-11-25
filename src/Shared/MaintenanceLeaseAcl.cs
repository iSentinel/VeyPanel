using System;
using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Principal;

namespace VeyPanel.Shared;

// Smoke-only policy observation; no repair or privilege changes.
[SupportedOSPlatform("windows")]
internal static class MaintenanceLeaseAcl
{
    internal static void RequireOwnerOnly(FileSystemSecurity security, SecurityIdentifier owner,
                                          bool directory)
    {
        var descriptor = new RawSecurityDescriptor(security.GetSecurityDescriptorBinaryForm(), 0);
        var flags = ControlFlags.DiscretionaryAclPresent | ControlFlags.DiscretionaryAclProtected;
        if ((descriptor.ControlFlags & flags) != flags || !owner.Equals(descriptor.Owner)
            || !security.AreAccessRulesCanonical || descriptor.DiscretionaryAcl is not { Count: 1 } acl)
            throw new UnauthorizedAccessException("Lease owner or DACL policy mismatch.");
        var expectedFlags = directory ? AceFlags.ContainerInherit | AceFlags.ObjectInherit : AceFlags.None;
        if (acl[0] is not CommonAce ace || ace.IsCallback || ace.AceQualifier != AceQualifier.AccessAllowed
            || !owner.Equals(ace.SecurityIdentifier) || ace.AceFlags != expectedFlags
            || ace.AccessMask != (int)FileSystemRights.FullControl)
            throw new UnauthorizedAccessException("Unexpected lease access rule.");
    }
}
