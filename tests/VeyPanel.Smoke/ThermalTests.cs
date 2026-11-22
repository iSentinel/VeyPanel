using System.Text.Json;
using System.Net;
using VeyPanel.Host;

internal static class ThermalTests
{
    internal static async Task<int> RunAsync()
    {
        var now = DateTimeOffset.UtcNow;
        var fixture = """
            {"Text":"Sensor","Children":[
              {"Text":"Intel CPU","HardwareId":"/intelcpu/0","Children":[
                {"Text":"CPU Package","Type":"Temperature","SensorId":"/intelcpu/0/temperature/0","RawValue":"42,5 °C","Value":"108.5 °F"},
                {"Text":"Core","Type":"Temperature","SensorId":"/intelcpu/0/temperature/1","RawValue":" °C"},
                {"Text":"Wrong unit","Type":"Temperature","SensorId":"/intelcpu/0/temperature/2","RawValue":"90.0 °F"}]},
              {"Text":"Intel GPU","HardwareId":"/gpu-intel-integrated/0","Children":[
                {"Text":"GPU Core","Type":"Temperature","SensorId":"/gpu-intel-integrated/0/temperature/0","RawValue":"39.0 °C"}]},
              {"Text":"Board","HardwareId":"/lpc/0","Children":[
                {"Text":"Board","Type":"Temperature","SensorId":"/lpc/0/temperature/0","RawValue":"30.0 °C"}]}]}
            """;
        var result = ThermalProvider.Parse(fixture, now);
        var checks = new (string, bool)[] {
            ("Thermal Celsius and culture", result.Status == "partial" && result.Sensors.Length == 4
                && result.Sensors[0].Celsius == 42.5 && result.Sensors[3].Celsius == 39),
            ("Thermal null and wrong unit", result.Sensors.Length == 4 && result.Sensors[1].Celsius is null && result.Sensors[2].Celsius is null),
            ("Thermal schema rejection", ThermalProvider.Parse("{}", now).Status == "invalid-schema"),
            ("Thermal stale", ThermalWorker.Fresh(result, now.AddSeconds(21)).Sensors.Length == 0),
            ("Thermal privacy", !JsonSerializer.Serialize(result).Contains("/intelcpu/")),
            ("Thermal numeric schema not assumed", ThermalProvider.Parse(fixture.Replace("\"42,5 °C\"", "42.5"), now).Sensors.FirstOrDefault()?.Celsius is null)
        };
        var failed = 0;
        foreach (var (name, pass) in checks) { Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {name}"); if (!pass) failed++; }
        using var client = new HttpClient(new FakeHandler(fixture));
        var actual = await ThermalWorker.CollectAsync(client, CancellationToken.None);
        var valid = actual.Sensors.Length == 4 && actual.Status == "partial";
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} Thermal fixed loopback GET");
        return failed + (valid ? 0 : 1);
    }
    private sealed class FakeHandler(string fixture) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct)
        {
            if (request.Method != HttpMethod.Get || request.RequestUri?.AbsoluteUri != "http://127.0.0.1:8085/data.json")
                throw new InvalidOperationException("Unexpected provider request");
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(fixture) });
        }
    }
}
