using VeyPanel.Shared;

internal static class DesktopAdmissionSmoke
{
    internal static int Run()
    {
        if (!OperatingSystem.IsWindows()) return 1;
        var name = @"Local\VeyPanel.Desktop.Fixture." + Guid.NewGuid().ToString("N");
        try
        {
            using (var owner = DesktopSessionAdmission.TryAcquire(name)
                ?? throw new InvalidOperationException("Initial admission refused."))
            {
                Require(!AcquireOnOtherThread(name), "Competing thread refused");
                var wrongThread = Task.Run(() =>
                {
                    try { owner.Dispose(); return false; }
                    catch (InvalidOperationException) { return true; }
                });
                Require(wrongThread.WaitAsync(TimeSpan.FromSeconds(5)).GetAwaiter().GetResult(),
                    "Nonowner release refused");
                Require(!AcquireOnOtherThread(name), "Owner remains admitted");
            }
            Require(AcquireOnOtherThread(name), "Admission after owner release");
            Console.WriteLine("PASS: Desktop session admission");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("FAIL: Desktop session admission (" + error.GetType().Name + ")");
            return 1;
        }
    }

    private static bool AcquireOnOtherThread(string name)
    {
        return Task.Run(() =>
        {
            using var contender = DesktopSessionAdmission.TryAcquire(name);
            return contender is not null;
        }).WaitAsync(TimeSpan.FromSeconds(5)).GetAwaiter().GetResult();
    }

    private static void Require(bool value, string label)
    {
        if (!value) throw new InvalidOperationException(label);
        Console.WriteLine("PASS: " + label);
    }
}
