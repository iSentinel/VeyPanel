using System.Text;
using VeyPanel.Host;

internal static class InvitationTests
{
    internal static int Run()
    {
        var now = DateTimeOffset.UtcNow;
        var devices = new DeviceRegistry(new string('A', 64));
        var registry = new InvitationRegistry(devices);
        var invite = registry.Create("Tablet", now)!;
        var id = invite.Invitation.Id;
        var claims = Enumerable.Range(0, 16).AsParallel().Select(_ => registry.Claim(id, invite.Secret, now))
            .OfType<InvitationClaim>().ToArray();
        var claim = claims.Single();
        var valid = registry.Claim(id, invite.Secret, now) is null
            && registry.Finish(id, invite.Secret, now).State == "unavailable"
            && registry.Finish(id, claim.Secret, now).State == "pending"
            && devices.List(now).Length == 0
            && !registry.Approve(id, "wrong", now) && registry.Approve(id, claim.Code, now);
        var redemptions = Enumerable.Range(0, 16).AsParallel().Select(_ => registry.Finish(id, claim.Secret, now))
            .Where(x => x.State == "issued").ToArray();
        valid &= redemptions.Length == 1 && devices.List(now).Length == 1
            && devices.Authenticate(Encoding.ASCII.GetBytes(redemptions.Single().Device!.Token), false, now) is { Owner: false };
        var expired = registry.Create("Expiry", now)!;
        valid &= registry.Claim(expired.Invitation.Id, expired.Secret, now.AddMinutes(2)) is null;
        var canceled = registry.Create("Cancelled", now)!;
        valid &= registry.Cancel(canceled.Invitation.Id)
            && registry.Claim(canceled.Invitation.Id, canceled.Secret, now) is null;
        for (var i = 0; i < InvitationRegistry.Capacity; i++) valid &= registry.Create("Fixture", now) is not null;
        valid &= registry.Create("Overflow", now) is null;
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} Invitation replay, approval, expiry, cancellation and parallel redemption");
        return valid ? 0 : 1;
    }
}
