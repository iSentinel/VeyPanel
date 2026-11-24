using VeyPanel.Host;
using System.Net;

if (args.Length == 2 && args[0] == "--persistent-smoke")
    return await PersistentHostSmoke.RunAsync(args[1]);

if (args.Length == 2 && args[0] == "--device-smoke")
    return await DeviceTests.SmokeAsync(args[1]);

if (args.Length == 2 && args[0] == "--ws-smoke")
    return await WebSocketSmoke.RunAsync(args[1]);

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
failed += TouchMappingTests.Run();
failed += TouchBindingTests.Run();
var ratePass = RateMath.Calculate(100, 300, 2) == 100
    && RateMath.Calculate(200, 100, 1) is null
    && RateMath.Calculate(null, 100, 1) is null
    && RateMath.Calculate(0, 100, 0) is null
    && RateMath.Calculate(100, 100, 1) == 0;
Console.WriteLine($"{(ratePass ? "PASS" : "FAIL")} Network rate math and reset");
if (!ratePass) failed++;
var pdhPass = DiskIoSampler.LayoutValid() && DiskIoSampler.Normalize(0, 123) == 123
    && DiskIoSampler.Normalize(1, 0) == 0 && DiskIoSampler.Normalize(2, 100) is null
    && DiskIoSampler.Normalize(0, double.NaN) is null && DiskIoSampler.Normalize(0, -1) is null;
Console.WriteLine($"{(pdhPass ? "PASS" : "FAIL")} PDH ABI and status normalization");
if (!pdhPass) failed++;
failed += GpuTests.Run();
var disks = PhysicalDiskSampler.Merge([
    [("0 C:", 100), ("1 D:", 200), ("_Total", 300)],
    [("0 C:", 20), ("1 D:", null)],
    [("0 C:", 0), ("1 D:", 3), ("1 D:", 4)],
    [("0 C:", 5)]
]);
var diskMerge = disks.Status == "partial" && disks.Disks.Length == 2
    && disks.Disks[0].ReadBytesPerSecond == 100 && disks.Disks[0].ReadsPerSecond == 0
    && disks.Disks[1].WriteBytesPerSecond is null && disks.Disks[1].ReadsPerSecond is null
    && PhysicalDiskSampler.Merge([[], [], [], [("_Total", 5)]]).Status == "unavailable";
Console.WriteLine($"{(diskMerge ? "PASS" : "FAIL")} Physical disk instance merge and missing values");
if (!diskMerge) failed++;
var healthNow = DateTimeOffset.UtcNow;
var healthJson = System.Text.Json.JsonSerializer.Serialize(new {
    schemaVersion = 1, timestampUtc = healthNow, source = "Windows Storage Provider", status = "partial",
    disks = new[] { new { name = "Fixture", counterStatus = "partial", temperatureC = 37, wearPercent = 0 } }
});
var health = StorageHealthWorker.Parse(healthJson, healthNow);
var healthPass = health.Status == "partial" && health.Disks.Length == 1
    && health.Disks[0].TemperatureC == 37 && health.Disks[0].WearPercent == 0
    && health.Disks[0].PowerOnHours is null
    && StorageHealthWorker.Fresh(health, healthNow.AddMinutes(3)).Status == "stale"
    && StorageHealthWorker.Parse(healthJson.Replace("\"temperatureC\":37", "\"temperatureC\":255"), healthNow).Status == "unavailable"
    && StorageHealthWorker.Parse("invalid", healthNow).Disks.Length == 0;
Console.WriteLine($"{(healthPass ? "PASS" : "FAIL")} Storage worker schema, nulls, bounds and freshness");
if (!healthPass) failed++;
failed += await ThermalTests.RunAsync();
failed += DeviceTests.Run();
failed += InvitationTests.Run();
failed += GrantStoreTests.Run();
failed += ProtectedStoreTests.Run();
failed += HistoryTests.Run();
failed += HistoryCsvTests.Run();
var wsSizePass = !TelemetrySocket.PayloadAllowed(-1) && !TelemetrySocket.PayloadAllowed(0)
    && TelemetrySocket.PayloadAllowed(1) && TelemetrySocket.PayloadAllowed(1024 * 1024)
    && !TelemetrySocket.PayloadAllowed(1024 * 1024 + 1);
Console.WriteLine($"{(wsSizePass ? "PASS" : "FAIL")} WebSocket outbound UTF-8 byte limit");
if (!wsSizePass) failed++;
return failed == 0 ? 0 : 1;
