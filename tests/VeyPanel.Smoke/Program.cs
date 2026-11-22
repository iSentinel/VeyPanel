using VeyPanel.Host;

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
return failed == 0 ? 0 : 1;
