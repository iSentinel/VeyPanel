using System.Runtime.InteropServices;

namespace VeyPanel.Host;

public sealed record Snapshot(DateTimeOffset TimestampUtc, double? CpuPercent,
    ulong? MemoryTotalBytes, ulong? MemoryAvailableBytes,
    double? MemoryUsedPercent, string Status)
{
    public ResourceSnapshot? Resources { get; init; }
    public DiskIoMetric? DiskIo { get; init; }
    public PhysicalDiskSnapshot? PhysicalDisks { get; init; }
    public GpuMetric? Gpu { get; init; }
}

public static class CpuMath
{
    public static double? Calculate(ulong idle, ulong kernel, ulong user,
        ulong oldIdle, ulong oldKernel, ulong oldUser)
    {
        if (idle < oldIdle || kernel < oldKernel || user < oldUser) return null;
        var total = (double)(kernel - oldKernel) + (user - oldUser);
        var idleDelta = (double)(idle - oldIdle);
        return total <= 0 || idleDelta > total ? null : 100 * (1 - idleDelta / total);
    }
}

public sealed class Telemetry : BackgroundService
{
    private Snapshot _latest = new(DateTimeOffset.UtcNow, null, null, null, null, "warming-up");
    private (ulong Idle, ulong Kernel, ulong User)? _previous;
    private readonly ResourceInventory resources = new();
    private readonly DiskIoSampler diskIo = new();
    private readonly PhysicalDiskSampler physicalDisks = new();
    private readonly GpuEngineSampler gpu = new();
    private readonly GpuAdapterInventory gpuInventory = new();
    public Snapshot Latest => Volatile.Read(ref _latest);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var sampler = diskIo;
        using var physicalSampler = physicalDisks;
        using var gpuSampler = gpu;
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(1));
        do
        {
            Volatile.Write(ref _latest, Collect());
        } while (await timer.WaitForNextTickAsync(stoppingToken));
    }

    private Snapshot Collect()
    {
        var now = DateTimeOffset.UtcNow;
        if (!OperatingSystem.IsWindows())
            return new(now, null, null, null, null, "unsupported-platform");
        double? cpu = null;
        if (GetSystemTimes(out var idle, out var kernel, out var user))
        {
            var current = (Idle: idle.Value, Kernel: kernel.Value, User: user.Value);
            if (_previous is { } previous)
                cpu = CpuMath.Calculate(current.Idle, current.Kernel, current.User,
                    previous.Idle, previous.Kernel, previous.User);
            _previous = current;
        }
        else _previous = null;
        var memory = new MemoryStatus { Length = (uint)Marshal.SizeOf<MemoryStatus>() };
        var valid = GlobalMemoryStatusEx(ref memory) && memory.TotalPhysical > 0
            && memory.AvailablePhysical <= memory.TotalPhysical;
        return new(now, cpu, valid ? memory.TotalPhysical : null,
            valid ? memory.AvailablePhysical : null,
            valid ? 100.0 * (memory.TotalPhysical - memory.AvailablePhysical) / memory.TotalPhysical : null,
            cpu.HasValue && valid ? "ok" : "partial") { Resources = resources.Capture(), DiskIo = diskIo.Capture(), PhysicalDisks = physicalDisks.Capture(), Gpu = gpuInventory.Attach(gpu.Capture()) };
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime
    {
        public uint Low, High;
        public readonly ulong Value => ((ulong)High << 32) | Low;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MemoryStatus
    {
        public uint Length, MemoryLoad;
        public ulong TotalPhysical, AvailablePhysical, TotalPageFile, AvailablePageFile,
            TotalVirtual, AvailableVirtual, AvailableExtendedVirtual;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetSystemTimes(out FileTime idle, out FileTime kernel, out FileTime user);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
}
