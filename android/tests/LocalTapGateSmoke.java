package com.veypanel.client;

/** Deterministic synthetic gestures; no device or host input injection. */
public final class LocalTapGateSmoke {
    private LocalTapGateSmoke() { }

    /** Exercise valid tap, missing down, drag, pointer changes and cancellation. */
    public static void main(String[] args) {
        LocalTapGate gate = new LocalTapGate();
        check(!gate.up(1, 10, 10, 1), "Unpaired up");
        gate.down(1, 10, 10, 1, 8);
        check(gate.up(1, 12, 10, 1), "Valid tap");
        check(!gate.up(1, 12, 10, 1), "Duplicate up");
        gate.down(1, 10, 10, 1, 8);
        gate.move(1, 50, 10, 1);
        check(!gate.up(1, 10, 10, 1), "Drag returned to origin");
        gate.down(1, 10, 10, 1, 8);
        check(!gate.up(2, 10, 10, 1), "Wrong pointer");
        gate.down(1, 10, 10, 1, 8);
        gate.move(1, 10, 10, 2);
        check(!gate.up(1, 10, 10, 1), "Multiple pointers");
        gate.down(1, 10, 10, 1, 8);
        gate.reset();
        check(!gate.up(1, 10, 10, 1), "Cancelled or lost preview");
        gate.down(1, Float.NaN, 10, 1, 8);
        check(!gate.up(1, 10, 10, 1), "Nonfinite down");
        gate.down(1, 10, 10, 1, 8);
        check(!gate.up(1, Float.POSITIVE_INFINITY, 10, 1), "Nonfinite up");
        System.out.println("PASS: local diagnostic single tap admission");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new IllegalStateException(label);
    }
}
