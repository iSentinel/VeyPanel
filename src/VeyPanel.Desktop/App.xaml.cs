using System;
using System.Windows;
using VeyPanel.Shared;

namespace VeyPanel.Desktop;

public partial class App : System.Windows.Application
{
    private DesktopSessionAdmission? admission;

    protected override void OnStartup(StartupEventArgs e)
    {
        try
        {
            admission = DesktopSessionAdmission.TryAcquire();
            if (admission is null)
            {
                Shutdown(2);
                return;
            }
            base.OnStartup(e);
            MainWindow = new MainWindow();
            MainWindow.Show();
        }
        catch
        {
            // Keep any acquired lease until the application's exit handler.
            Shutdown(1);
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        try { base.OnExit(e); }
        finally
        {
            admission?.Dispose();
            admission = null;
        }
    }
}
