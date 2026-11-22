using Net.Codecrete.QrCodeGenerator;

namespace VeyPanel.Host;

internal static class InvitationQr
{
    internal static string Render(string url)
    {
        if (url.Length > 256 || !Uri.TryCreate(url, UriKind.Absolute, out var uri)
            || uri.Scheme != "https" || uri.AbsolutePath != "/enroll.html")
            throw new ArgumentException("Invalid enrollment URL");
        var qr = QrCode.EncodeText(url, QrCode.Ecc.Medium);
        var png = qr.ToPngBitmap(border: 4, scale: 6);
        if (png.Length > 256 * 1024) throw new InvalidOperationException("QR size limit");
        return Convert.ToBase64String(png);
    }
}
