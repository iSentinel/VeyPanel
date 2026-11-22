using VeyPanel.Host;
using System.Net;

if (args.Length == 2 && args[0] == "--lifecycle-smoke")
    return await LifecycleSmoke.RunAsync(args[1]);

if (args.Length == 2 && args[0] == "--lan-smoke")
    return await LanSmoke.RunAsync(args[1]);

var checks = new (string Name, double? Actual, double? Expected)[]
{
    ("50 percent", CpuMath.Calculate(50, 75, 25, 0, 0, 0), 50),
    ("idle", CpuMath.Calculate(100, 100, 0, 0, 0, 0), 0),
    ("busy", CpuMath.Calculate(0, 50, 50, 0, 0, 0), 100),
    ("zero delta", CpuMath.Calculate(1, 1, 1, 1, 1, 1), null),
    ("reset", CpuMath.Calculate(0, 0, 0, 1, 1, 1), null),
    ("75 percent", CpuMath.Calculate(25, 70, 30, 0, 0, 0), 75),
    ("nonzero baseline", CpuMath.Calculate(125, 570, 330, 100, 500, 300), 75),
    ("invalid idle", CpuMath.Calculate(101, 100, 0, 0, 0, 0), null),
};
var failed = 0;
foreach (var check in checks)
{
    var pass = check.Actual == check.Expected;
    Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {check.Name}");
    if (!pass) failed++;
}
Console.WriteLine($"{checks.Length - failed}/{checks.Length} passed");
failed += await ApolloTests.RunAsync();
var layoutPass = DisplayInventory.LayoutIsValid();
Console.WriteLine($"{(layoutPass ? "PASS" : "FAIL")} Win32 display structure layouts");
if (!layoutPass) failed++;
if (OperatingSystem.IsWindows() && layoutPass)
{
    var inventory = DisplayInventory.Capture();
    var valid = inventory.Status is "ok" or "partial" or "no-desktop-sources";
    Console.WriteLine($"{(valid ? "PASS" : "FAIL")} Win32 source inventory ({inventory.Status}; {inventory.Sources.Length} sources)");
    if (!valid) failed++;
}
var privatePass = new[] { "10.1.2.3", "172.16.0.2", "172.31.1.2", "192.168.1.2" }
    .All(ip => LanAddressPolicy.IsPrivateIpv4(IPAddress.Parse(ip)))
    && new[] { "0.0.0.0", "127.0.0.1", "8.8.8.8", "172.32.1.2", "100.64.1.2", "::1", "224.0.0.1" }
    .All(ip => !LanAddressPolicy.IsPrivateIpv4(IPAddress.Parse(ip)));
Console.WriteLine($"{(privatePass ? "PASS" : "FAIL")} RFC1918 LAN address policy");
if (!privatePass) failed++;
failed += TopologyTests.Run();
return failed == 0 ? 0 : 1;
