"""audit_logger.py - Structured JSONL audit log for every daily run."""

import json
import os
from datetime import datetime, timezone

LOG_PATH = "logs/safety_log.jsonl"


def _now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event, level="INFO", details=None, path=LOG_PATH):
    """Append one JSONL line to the audit log."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    entry = {
        "timestamp_utc": _now_utc(),
        "event": event,
        "level": level,
        "details": details or {},
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
