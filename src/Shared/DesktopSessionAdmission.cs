using System;
using System.Threading;

namespace VeyPanel.Shared;

// A cooperative, thread-affine lease in the current Windows session.
internal sealed class DesktopSessionAdmission : IDisposable
{
    internal const string Name = @"Local\VeyPanel.Desktop.Interactive.v1";
    private readonly Mutex mutex;
    private readonly int ownerThread;
    private bool disposed;

    private DesktopSessionAdmission(Mutex mutex)
    {
        this.mutex = mutex;
        ownerThread = Environment.CurrentManagedThreadId;
    }

    internal static DesktopSessionAdmission? TryAcquire(string name = Name)
    {
        var mutex = new Mutex(false, name);
        try
        {
            bool acquired;
            try { acquired = mutex.WaitOne(0); }
            catch (AbandonedMutexException) { acquired = true; }
            if (acquired) return new DesktopSessionAdmission(mutex);
            mutex.Dispose();
            return null;
        }
        catch
        {
            mutex.Dispose();
            throw;
        }
    }

    public void Dispose()
    {
        if (disposed) return;
        if (ownerThread != Environment.CurrentManagedThreadId)
            throw new InvalidOperationException("Desktop admission must be released by its owner thread.");
        mutex.ReleaseMutex();
        mutex.Dispose();
        disposed = true;
    }
}
