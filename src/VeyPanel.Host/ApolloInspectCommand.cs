using System.Text;
using System.Text.Json;

namespace VeyPanel.Host;

internal static class ApolloInspectCommand
{
    internal static async Task<int> RunAsync(string[] args)
    {
        if (args.Length != 2 || args[0] is not ("--apollo-inspect" or "--apollo-pair") || Console.IsInputRedirected)
        {
            Console.Error.WriteLine("Usage: VeyPanel.Host --apollo-inspect|--apollo-pair <verified-certificate-sha256> (interactive).");
            return 2;
        }
        try
        {
            using var apollo = ApolloClient.Create(args[1]);
            var pair = args[0] == "--apollo-pair";
            if (pair)
            {
                Console.WriteLine("Pair only a device physically under your control. Apollo may grant the first client full permissions. Review them after pairing.");
                Console.Write("Type PAIR to authorize a single pairing request: ");
                if (Console.ReadLine() != "PAIR")
                {
                    Console.WriteLine("Cancelled; no network request.");
                    return 2;
                }
            }
            Console.WriteLine("Apollo login may replace an existing Web UI session.");
            if (!pair) Console.WriteLine("No configuration or pairing changes.");
            Console.Write("Username: ");
            var username = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(username)) return 2;
            Console.Write("Password (hidden): ");
            var password = ReadPassword();
            if (password.Length == 0) return 2;
            await apollo.LoginAsync(username, password);
            if (pair) return await PairAsync(apollo);
            var inventory = await apollo.InspectAsync();
            Console.WriteLine(JsonSerializer.Serialize(inventory, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
        catch (Exception ex) when (ex is FormatException or HttpRequestException or InvalidDataException
            or InvalidOperationException or JsonException or OperationCanceledException or IOException)
        {
            Console.Error.WriteLine($"Apollo operation failed ({ex.GetType().Name}). Verify TLS pin, service, credentials and API version. If pairing was attempted, check both devices before retrying.");
            return 1;
        }
    }

    private static async Task<int> PairAsync(ApolloClient apollo)
    {
        Console.Write("Device name: ");
        var name = Console.ReadLine()?.Trim() ?? "";
        Console.Write("PIN shown on the tablet (hidden): ");
        var pin = ReadPassword();
        if (!ApolloClient.ValidPairingInput(pin, name))
        {
            Console.Error.WriteLine("Invalid device name or PIN; no pairing request.");
            return 2;
        }
        var accepted = await apollo.PairAsync(pin, name);
        Console.WriteLine(accepted
            ? "Apollo accepted PIN; verify completed pairing and permissions on both devices."
            : "Apollo rejected PIN; check the current tablet pairing request.");
        return accepted ? 0 : 1;
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
