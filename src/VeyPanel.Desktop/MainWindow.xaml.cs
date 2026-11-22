using System.Threading.Tasks;
using System.Windows;
using System.Drawing;
using VeyPanel.Host;
using Forms = System.Windows.Forms;

namespace VeyPanel.Desktop;

public partial class MainWindow : Window
{
    private readonly Forms.NotifyIcon tray;
    private bool busy;

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
