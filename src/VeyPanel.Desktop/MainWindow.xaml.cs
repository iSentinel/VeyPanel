using System.Threading.Tasks;
using System.Diagnostics;
using System.IO;
using System.ComponentModel;
using System.Windows.Threading;
using VeyPanel.Shared;
using System.Windows;
using System.Drawing;
using VeyPanel.Host;
using Forms = System.Windows.Forms;

namespace VeyPanel.Desktop;

public partial class MainWindow : Window
{
    private readonly Forms.NotifyIcon tray;
    private bool busy;
    private bool hostBusy, closing, mayClose, apolloBusy;
    private Task? apolloOperation;
    private readonly HostController host = new(Path.Combine(AppContext.BaseDirectory, "host"));
    private readonly DispatcherTimer hostTimer = new() { Interval = TimeSpan.FromSeconds(2) };

    public MainWindow()
    {
        InitializeComponent();
        var menu = new Forms.ContextMenuStrip();
        menu.Items.Add("Open VeyPanel", null, (_, _) => Dispatcher.Invoke(ShowWindow));
        menu.Items.Add("Exit", null, (_, _) => Dispatcher.Invoke(Close));
        tray = new Forms.NotifyIcon {
            Icon = SystemIcons.Application,
            Text = "VeyPanel Desktop Alpha",
            ContextMenuStrip = menu,
            Visible = true
        };
        tray.DoubleClick += (_, _) => Dispatcher.Invoke(ShowWindow);
        StateChanged += (_, _) => { if (WindowState == WindowState.Minimized) Hide(); };
        Closed += (_, _) => { tray.Visible = false; tray.Dispose(); menu.Dispose(); };
        Loaded += async (_, _) => await RefreshAsync();
        Closing += CloseAsync;
        hostTimer.Tick += async (_, _) => await UpdateHostAsync();
        hostTimer.Start();
    }

    private async void StartHost_Click(object sender, RoutedEventArgs e) =>
        await RunHostAsync(host.StartAsync);

    private async void StopHost_Click(object sender, RoutedEventArgs e) =>
        await RunHostAsync(host.StopAsync);

    private async void Dashboard_Click(object sender, RoutedEventArgs e) =>
        await RunHostAsync(async () =>
        {
            var url = await host.DashboardUrlAsync();
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true })?.Dispose();
        });

    private async Task RunHostAsync(Func<Task> action)
    {
        if (hostBusy || closing) return;
        hostBusy = true;
        StartHostButton.IsEnabled = StopHostButton.IsEnabled = DashboardButton.IsEnabled = false;
        HostStatus.Text = "Working…";
        string? error = null;
        try { await action(); }
        catch (Exception ex) { error = $"Host operation failed ({ex.GetType().Name})."; }
        finally { hostBusy = false; }
        if (!closing)
        {
            await UpdateHostAsync();
            if (error is not null) HostStatus.Text = error;
        }
    }

    private async Task UpdateHostAsync()
    {
        if (hostBusy || closing) return;
        var state = await host.GetStateAsync();
        if (hostBusy || closing) return;
        StartHostButton.IsEnabled = state == HostLifecycleState.Stopped;
        StopHostButton.IsEnabled = state != HostLifecycleState.Stopped;
        DashboardButton.IsEnabled = state == HostLifecycleState.Ready;
        HostStatus.Text = state switch
        {
            HostLifecycleState.Ready => "Running • 127.0.0.1:47860",
            HostLifecycleState.CleanupRequired => "Owned Host cleanup required • Stop Host",
            _ => "Stopped"
        };
    }

    private async void CloseAsync(object? sender, CancelEventArgs e)
    {
        if (mayClose) return;
        e.Cancel = true;
        if (closing) return;
        closing = true;
        hostTimer.Stop();
        try
        {
            if (apolloOperation is not null) await apolloOperation;
            await host.DisposeAsync();
        }
        catch (Exception ex)
        {
            closing = false;
            await UpdateHostAsync();
            HostStatus.Text = $"Shutdown failed ({ex.GetType().Name}); retry Stop Host.";
            hostTimer.Start();
            return;
        }
        mayClose = true;
        Close();
    }

    private async void ApolloInspect_Click(object sender, RoutedEventArgs e) =>
        await BeginApolloAsync(false);

    private async void ApolloPair_Click(object sender, RoutedEventArgs e) =>
        await BeginApolloAsync(true);

    private async Task BeginApolloAsync(bool pair)
    {
        if (apolloBusy || closing) return;
        var pin = ApolloDevicePin.Password;
        var name = ApolloDeviceName.Text.Trim();
        if (pair && !ApolloClient.ValidPairingInput(pin, name))
        {
            ApolloStatus.Text = "Enter a valid device name and four ASCII digits.";
            ApolloDevicePin.Clear();
            return;
        }
        var message = pair
            ? "Send one pairing request to local Apollo? First-time clients may receive broad permissions. Review permissions after pairing."
            : "Inspect local Apollo? Login may replace an existing Web UI session.";
        if (System.Windows.MessageBox.Show(this, message, "VeyPanel Apollo",
            MessageBoxButton.YesNo, MessageBoxImage.Warning, MessageBoxResult.No) != MessageBoxResult.Yes)
        {
            ApolloPassword.Clear();
            ApolloDevicePin.Clear();
            return;
        }
        var fingerprint = ApolloPinHash.Text.Trim();
        var username = ApolloUsername.Text.Trim();
        var password = ApolloPassword.Password;
        ApolloPassword.Clear();
        ApolloDevicePin.Clear();
        ApolloApps.ItemsSource = null;
        apolloBusy = true;
        ApolloInspectButton.IsEnabled = ApolloPairButton.IsEnabled = false;
        ApolloStatus.Text = "Connecting…";
        apolloOperation = ExecuteApolloAsync(pair, fingerprint, username, password, pin, name);
        try { await apolloOperation; }
        finally
        {
            apolloOperation = null;
            apolloBusy = false;
            ApolloInspectButton.IsEnabled = ApolloPairButton.IsEnabled = true;
        }
    }

    private async Task ExecuteApolloAsync(bool pair, string fingerprint, string username,
        string password, string pin, string name)
    {
        try
        {
            if (username.Length == 0 || password.Length == 0)
                throw new FormatException("Credentials required.");
            using var client = ApolloClient.Create(fingerprint);
            await client.LoginAsync(username, password);
            if (pair)
            {
                var accepted = await client.PairAsync(pin, name);
                ApolloStatus.Text = accepted
                    ? "PIN accepted. Verify completed pairing and permissions on both devices."
                    : "PIN rejected. Check the current tablet request.";
                return;
            }
            var info = await client.InspectAsync();
            ApolloApps.ItemsSource = info.Apps;
            ApolloStatus.Text = $"{info.HostName ?? "Unknown host"} • {info.PairedClients} paired client(s)";
        }
        catch (Exception ex)
        {
            ApolloStatus.Text = $"Apollo operation failed ({ex.GetType().Name}). Check service, certificate, credentials and device before retrying.";
        }
    }

    private void ShowWindow()
    {
        Show();
        WindowState = WindowState.Normal;
        Activate();
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e) => await RefreshAsync();
    private async void Validate_Click(object sender, RoutedEventArgs e)
    {
        await RunBusyAsync(async () =>
        {
            var result = await Task.Run(DisplayValidation.ValidateCurrent);
            StatusText.Text = $"Validation: {result.Status}; native: {result.NativeError?.ToString() ?? "N/A"}"
                + (result.Issues.Length == 0 ? "" : $" • {string.Join(", ", result.Issues)}");
        });
    }

    private async Task RefreshAsync()
    {
        await RunBusyAsync(async () =>
        {
            var result = await Task.Run(() => (Sources: DisplayInventory.Capture(), Topology: DisplayTopology.Capture()));
            SourcesGrid.ItemsSource = result.Sources.Sources.Select(SourceRow.From).ToArray();
            PathsGrid.ItemsSource = result.Topology.Paths.Select(p => PathRow.From(p, result.Topology.Modes)).ToArray();
            StatusText.Text = $"Sources: {result.Sources.Status} ({result.Sources.Sources.Length}) • "
                + $"Topology: {result.Topology.Status} ({result.Topology.Paths.Length})"
                + (result.Topology.NativeError is int error ? $" • Native error: {error}" : "");
        });
    }

    private async Task RunBusyAsync(Func<Task> operation)
    {
        if (busy) return;
        busy = true;
        RefreshButton.IsEnabled = ValidateButton.IsEnabled = false;
        StatusText.Text = "Working…";
        try { await operation(); }
        catch (Exception ex) { StatusText.Text = $"Diagnostic failed ({ex.GetType().Name})."; }
        finally
        {
            busy = false;
            RefreshButton.IsEnabled = ValidateButton.IsEnabled = true;
        }
    }
}

internal sealed record SourceRow(string Source, string Adapter, string Resolution, string Refresh,
    string Position, string Primary)
{
    internal static SourceRow From(DisplaySource s) => new(s.DeviceName, s.AdapterName,
        s.Width is uint w && s.Height is uint h ? $"{w} × {h}" : "N/A",
        s.Hz is uint hz ? $"{hz} Hz" : "N/A",
        s.X is int x && s.Y is int y ? $"{x}, {y}" : "N/A", s.Primary ? "Yes" : "No");
}

internal sealed record PathRow(string Source, string Monitor, string Target, string Resolution,
    string Rotation, string Identity)
{
    internal static PathRow From(TopologyPath p, TopologyMode[] modes)
    {
        var source = p.SourceMode is uint index && index < modes.Length ? modes[index].Source : null;
        return new(p.Identity?.GdiName ?? $"Source {p.SourceId}", p.Identity?.FriendlyName ?? "N/A",
            p.TargetId.ToString(), source is null ? "N/A" : $"{source.Width} × {source.Height}",
            p.Rotation switch { 1 => "0°", 2 => "90°", 3 => "180°", 4 => "270°", _ => "N/A" },
            p.Identity is { SourceError: 0, TargetError: 0, MonitorDevicePath: not null } ? "Available" : "N/A");
    }
}
