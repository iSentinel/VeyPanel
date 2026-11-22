using N = VeyPanel.Host.DisplayConfigNative;

namespace VeyPanel.Host;

internal sealed record DisplayValidationResult(string Status, int? NativeError, string[] Issues);

internal static class DisplayValidation
{
    internal static DisplayValidationResult ValidateCurrent()
    {
        var baseline = DisplayTopology.Capture();
        var current = DisplayTopology.Capture(out var paths, out var modes);
        var issues = DisplayRecoveryPolicy.Check(baseline, current);
        if (issues.Length > 0) return new("blocked", current.NativeError, issues);
        if (!Equivalent(baseline, current)) return new("blocked", null, ["topology-changed-before-validation"]);
        var error = N.ValidateOnly(paths, modes);
        var after = DisplayTopology.Capture();
        if (!Equivalent(current, after)) return new("topology-changed", error, ["topology-changed-during-validation"]);
        return error == 0 ? new("validated", 0, []) : new("native-rejected", error, ["windows-validation-failed"]);
    }

    internal static bool Equivalent(TopologySnapshot left, TopologySnapshot right) =>
        left.Status == "ok" && right.Status == "ok"
        && left.SchemaVersion == right.SchemaVersion && left.QueryFlags == right.QueryFlags
        && left.Paths.SequenceEqual(right.Paths) && left.Modes.SequenceEqual(right.Modes);
}
