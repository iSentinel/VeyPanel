package com.veypanel.client;

/** Accept only an uninterrupted, single-pointer tap in the local diagnostic. */
final class LocalTapGate {
    private boolean active;
    private int pointer;
    private float startX;
    private float startY;
    private int slop;

    void down(int id, float x, float y, int pointers, int touchSlop) {
        reset();
        if (pointers != 1 || id < 0 || !Float.isFinite(x) || !Float.isFinite(y)
                || touchSlop < 0) return;
        pointer = id;
        startX = x;
        startY = y;
        slop = touchSlop;
        active = true;
    }

    void move(int id, float x, float y, int pointers) {
        if (!active || id != pointer || pointers != 1
                || !Float.isFinite(x) || !Float.isFinite(y)
                || Math.hypot((double)x - startX, (double)y - startY) > slop)
            reset();
    }

    boolean up(int id, float x, float y, int pointers) {
        move(id, x, y, pointers);
        boolean accepted = active;
        reset();
        return accepted;
    }

    void reset() { active = false; }
}
