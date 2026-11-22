using VeyPanel.Host;

var checks = new (string Name, double? Actual, double? Expected)[]
{
    ("50 percent", CpuMath.Calculate(50, 75, 25, 0, 0, 0), 50),
    ("idle", CpuMath.Calculate(100, 100, 0, 0, 0, 0), 0),
    ("busy", CpuMath.Calculate(0, 50, 50, 0, 0, 0), 100),
    ("zero delta", CpuMath.Calculate(1, 1, 1, 1, 1, 1), null),
    ("reset", CpuMath.Calculate(0, 0, 0, 1, 1, 1), null),
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
return failed == 0 ? 0 : 1;
}
