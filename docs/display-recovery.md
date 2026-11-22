# Display recovery design (no writes implemented)

Stage 1: QueryDisplayConfig active path/mode snapshot using QDC_ONLY_ACTIVE_PATHS, QDC_VIRTUAL_MODE_AWARE and QDC_VIRTUAL_REFRESH_RATE_AWARE. Retry buffer-size races, cap allocations, decode virtual mode bitfields, validate mode references and report incomplete evidence. Do not apply a partial snapshot. Adapter LUIDs and IDs are not durable across reboot/adapter changes. Snapshot is diagnostic only; not a restorable backup.

Stage 2 (planned): collect persistent target identity via DisplayConfigGetDeviceInfo, correlate with current paths, and define explicit same-session recovery eligibility. Validate candidate paths with SetDisplayConfig SDC_VALIDATE only, no topology change. Reject ambiguous IDs, missing physical displays, unsupported flags and incomplete modes.

Stage 3 (planned): require explicit operator consent, live rollback watchdog independent of UI, capture baseline immediately before any mutation, and non-persistent candidate apply. Preserve at least one known physical display. Revalidate paths and allow a local confirmation timeout; restore only the exact eligible baseline. Never replay arbitrary JSON as native buffers. Do not persist until hardware acceptance. Stop on mismatch rather than use permissive flags.

References:
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-querydisplayconfig
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/relationship-of-mode-information-to-path-information
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setdisplayconfig

Physical acceptance: single monitor, multiple monitors, cloned paths, SudoVDA connection/disconnection, dynamic refresh, sleep/wake and rollback on failed apply. All pending.
