"""Closed, opt-in operational events for the offline QA runner."""

from datetime import datetime, timezone
import json
import math
from typing import TextIO

STAGES = frozenset({"audit", "tests", "report", "run"})
OUTCOMES = frozenset({"PASS", "FAIL", "ERROR"})
REASONS = {
    "audit": {"PASS": "AUDIT_MATCH", "FAIL": "AUDIT_DELTA"},
    "tests": {"PASS": "TESTS_PASS", "FAIL": "TESTS_FAILED"},
    "report": {"PASS": "REPORT_WRITTEN"},
    "run": {"PASS": "RUN_PASS", "FAIL": "RUN_FAILED", "ERROR": "EXECUTION_ERROR"},
}
MAX_DURATION = 86400


def event(stage: str, status: str, duration: float) -> dict[str, str | int | float]:
    """Construct an event from exact stage/status pairs and a bounded duration."""
    if (not isinstance(stage, str) or stage not in STAGES
            or not isinstance(status, str) or status not in OUTCOMES
            or status not in REASONS[stage]):
        raise ValueError("Invalid QA event stage/status")
    if (type(duration) not in (int, float) or not 0 <= duration <= MAX_DURATION
            or not math.isfinite(duration)):
        raise ValueError("Invalid QA event duration")
    return {"schema": 1, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "level": "INFO" if status == "PASS" else "ERROR",
            "event": "offline_qa_stage", "stage": stage, "status": status,
            "reason": REASONS[stage][status], "duration_seconds": round(duration, 6)}


def emit(sink: TextIO | None, stage: str, status: str, duration: float) -> None:
    """Write one validated JSONL event to the caller-owned sink, if enabled."""
    if sink is not None:
        data = event(stage, status, duration)
        sink.write(json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n")
        sink.flush()
