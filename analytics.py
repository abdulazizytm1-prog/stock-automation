"""
analytics.py - Outcome analytics and edge validation for closed journal trades.

Read-only: this module never writes to journal or scan state.
All functions are tolerant of missing fields (old records without grade/days_held/etc.)
and will never crash on incomplete data.
"""


def grade_stats(trades):
    """
    Per-grade (A/B/C) performance metrics.
    Trades missing setup_grade default to "C" (conservative).

    Returns:
        {"A": {total, wins, losses, win_rate}, "B": {...}, "C": {...}}
    """
    result = {}
    for grade in ("A", "B", "C"):
        g = [t for t in trades if t.get("setup_grade", "C") == grade]
        n = len(g)
        wins = [t for t in g if (t.get("r_multiple") or 0) > 0]
        losses = [t for t in g if (t.get("r_multiple") or 0) <= 0]
        result[grade] = {
            "total": n,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / n * 100) if n > 0 else None,
        }
    return result


def symbol_stats(trades, min_trades=3):
    """
    Per-symbol performance metrics, filtered to symbols with at least min_trades
    completed trades.

    Returns:
        {symbol: {total, win_rate}} for symbols meeting the threshold.
    """
    by_sym = {}
    for t in trades:
        sym = t.get("symbol")
        if not sym:
            continue
        by_sym.setdefault(sym, []).append(t)

    result = {}
    for sym, sym_trades in sorted(by_sym.items()):
        if len(sym_trades) < min_trades:
            continue
        wins = [t for t in sym_trades if (t.get("r_multiple") or 0) > 0]
        result[sym] = {
            "total": len(sym_trades),
            "win_rate": len(wins) / len(sym_trades) * 100,
        }
    return result


def holding_stats(trades):
    """
    Average and median holding duration in days across all closed trades.
    Trades missing days_held are silently skipped.

    Returns:
        {"avg": float | None, "median": float | None}
    """
    durations = [
        t["days_held"]
        for t in trades
        if isinstance(t.get("days_held"), (int, float))
    ]
    if not durations:
        return {"avg": None, "median": None}

    avg = sum(durations) / len(durations)
    s = sorted(durations)
    n = len(s)
    median = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"avg": avg, "median": median}


def outcome_distribution(trades):
    """
    Count of each exit outcome across all closed trades.
    exit_reason "target" → TARGET_HIT
    exit_reason "stop"   → STOP_LOSS
    anything else        → other

    Returns:
        {"TARGET_HIT": int, "STOP_LOSS": int, "other": int}
    """
    counts = {"TARGET_HIT": 0, "STOP_LOSS": 0, "other": 0}
    for t in trades:
        reason = t.get("exit_reason", "")
        if reason == "target":
            counts["TARGET_HIT"] += 1
        elif reason == "stop":
            counts["STOP_LOSS"] += 1
        else:
            counts["other"] += 1
    return counts


def compute_edge_analytics(journal):
    """
    Top-level entry point: derives all edge analytics from the journal.
    Safe to call with an empty or legacy journal.

    Returns:
        {
          "total_closed": int,
          "grade_stats": {...},
          "symbol_stats": {...},
          "holding_stats": {...},
          "outcome_distribution": {...},
        }
    """
    trades = journal.get("closed_trades", [])
    return {
        "total_closed": len(trades),
        "grade_stats": grade_stats(trades),
        "symbol_stats": symbol_stats(trades),
        "holding_stats": holding_stats(trades),
        "outcome_distribution": outcome_distribution(trades),
    }
