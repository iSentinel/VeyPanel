namespace VeyPanel.Host;

// Geometry only. Never receives a device token and never injects OS input.
internal sealed record TouchViewport(int Width, int Height, int FrameWidth, int FrameHeight,
    int FrameClockwiseDegrees);
internal sealed record DesktopTouchPoint(int X, int Y);

internal static class TouchMapping
{
    internal static DesktopTouchPoint? Map(double x, double y, TouchViewport viewport, DisplayRect desktop)
    {
        if (!Valid(viewport, desktop) || !double.IsFinite(x) || !double.IsFinite(y)) return null;
        var scale = Math.Min((double)viewport.Width / viewport.FrameWidth,
            (double)viewport.Height / viewport.FrameHeight);
        var shownWidth = viewport.FrameWidth * scale;
        var shownHeight = viewport.FrameHeight * scale;
        var left = (viewport.Width - shownWidth) / 2;
        var top = (viewport.Height - shownHeight) / 2;
        var u = (x - left) / shownWidth;
        var v = (y - top) / shownHeight;
        if (u < 0 || u > 1 || v < 0 || v > 1) return null;
        var (dx, dy) = Unrotate(u, v, viewport.FrameClockwiseDegrees);
        var width = (long)desktop.Right - desktop.Left;
        var height = (long)desktop.Bottom - desktop.Top;
        var px = desktop.Left + (long)Math.Round(dx * (width - 1), MidpointRounding.AwayFromZero);
        var py = desktop.Top + (long)Math.Round(dy * (height - 1), MidpointRounding.AwayFromZero);
        if (px is < int.MinValue or > int.MaxValue || py is < int.MinValue or > int.MaxValue)
            return null;
        return new((int)px, (int)py);
    }

    private static (double X, double Y) Unrotate(double u, double v, int clockwise) =>
        clockwise switch
        {
            0 => (u, v),
            90 => (v, 1 - u),
            180 => (1 - u, 1 - v),
            270 => (1 - v, u),
            _ => throw new ArgumentOutOfRangeException(nameof(clockwise))
        };

    private static bool Valid(TouchViewport v, DisplayRect d)
    {
        var width = (long)d.Right - d.Left;
        var height = (long)d.Bottom - d.Top;
        return v.Width is > 0 and <= 32768 && v.Height is > 0 and <= 32768
            && v.FrameWidth is > 0 and <= 32768 && v.FrameHeight is > 0 and <= 32768
            && v.FrameClockwiseDegrees is 0 or 90 or 180 or 270
            && width is > 0 and <= 32768 && height is > 0 and <= 32768;
    }
}
