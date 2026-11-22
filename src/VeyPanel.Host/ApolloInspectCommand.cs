using System.Text;
using System.Text.Json;

namespace VeyPanel.Host;

internal static class ApolloInspectCommand
{
    internal static async Task<int> RunAsync(string[] args)
    {
        if (args.Length != 2 || args[0] != "--apollo-inspect" || Console.IsInputRedirected)
        {
            Console.Error.WriteLine("Usage: VeyPanel.Host --apollo-inspect <verified-certificate-sha256> (interactive).");
            return 2;
        }
        try
        {
            using var apollo = ApolloClient.Create(args[1]);
            Console.WriteLine("Apollo login may replace an existing Web UI session. No configuration or pairing changes.");
            Console.Write("Username: ");
            var username = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(username)) return 2;
            Console.Write("Password (hidden): ");
            var password = ReadPassword();
            if (password.Length == 0) return 2;
            await apollo.LoginAsync(username, password);
            var inventory = await apollo.InspectAsync();
            Console.WriteLine(JsonSerializer.Serialize(inventory, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
        catch (Exception ex) when (ex is FormatException or HttpRequestException or InvalidDataException
            or InvalidOperationException or JsonException or OperationCanceledException or IOException)
        {
            Console.Error.WriteLine($"Apollo inspection failed ({ex.GetType().Name}). Verify TLS pin, service, credentials and API version.");
            return 1;
        }
    }

    private static string ReadPassword()
    {
        var buffer = new StringBuilder();
        while (true)
        {
            var key = Console.ReadKey(intercept: true);
            if (key.Key == ConsoleKey.Enter) break;
            if (key.Key == ConsoleKey.Backspace && buffer.Length > 0) { buffer.Length--; continue; }
            if (!char.IsControl(key.KeyChar) && buffer.Length < 1024) buffer.Append(key.KeyChar);
        }
        Console.WriteLine();
        return buffer.ToString();
    }
}
