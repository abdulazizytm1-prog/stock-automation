"""alert_dedupe.py - Alert deduplication state (foundation for future Telegram integration)."""

import json
import os


def load_alert_dedupe(path):
    """Load dedup state from JSON file; returns empty dict if file does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_alert_dedupe(state, path):
    """Persist dedup state to JSON file."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def make_alert_key(symbol, date, status, setup=None):
    """Build a stable dedup key from signal attributes."""
    parts = [symbol, date, status]
    if setup:
        parts.append(setup)
    return "|".join(parts)


def was_alert_sent(state, key):
    """Return True if this key was already sent."""
    return key in state


def mark_alert_sent(state, key):
    """Record that this alert has been sent (mutates state in-place)."""
    state[key] = True
