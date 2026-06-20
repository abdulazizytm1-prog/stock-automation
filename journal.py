"""journal.py - Pending signal -> open position -> closed trade hayot sikli."""

import json
import os

BUFFER_PCT = 0.003
TARGET_R = 2.0
TIME_STOP_DAYS = 20


def load_journal(path):
    if not os.path.exists(path):
        return {
            "meta": {},
            "pending_confirmation": [],
            "open_positions": [],
            "closed_trades": [],
        }
    with open(path) as f:
        journal = json.load(f)
    journal.setdefault("meta", {})
    journal.setdefault("pending_confirmation", [])
    journal.setdefault("open_positions", [])
    journal.setdefault("closed_trades", [])
    return journal


def save_journal(journal, path):
    with open(path, "w") as f:
        json.dump(journal, f, indent=2)


def update_journal(journal, data_by_symbol, scan_results, run_meta=None):
    """
    Bitta kunlik yangilanish.
    data_by_symbol: {symbol: bars}
    scan_results: scan_watchlist() natijasi
    """
    events = {
        "confirmed": [],
        "closed": [],
        "new_pending": [],
        "rejected": [],
        "ambiguity_count": 0,
    }
    if run_meta:
        journal["meta"] = run_meta

    still_pending = []
    for pending in journal["pending_confirmation"]:
        bars = data_by_symbol.get(pending["symbol"])
        if not bars:
            still_pending.append(pending)
            continue

        future_bars = [bar for bar in bars if bar["date"] > pending["detected_date"]]
        if not future_bars:
            still_pending.append(pending)
            continue

        entry_bar = future_bars[0]
        entry_price = entry_bar["open"]
        buffer = entry_price * BUFFER_PCT
        if pending["direction"] == "long":
            stop = pending["zone_bottom"] - buffer
            risk = entry_price - stop
            target = entry_price + TARGET_R * risk
        else:
            stop = pending["zone_top"] + buffer
            risk = stop - entry_price
            target = entry_price - TARGET_R * risk

        if risk <= 0:
            events["rejected"].append(
                {
                    "symbol": pending["symbol"],
                    "detected_date": pending["detected_date"],
                    "entry_date": entry_bar["date"],
                    "reason": "invalid_risk",
                }
            )
            continue

        position = {
            "symbol": pending["symbol"],
            "direction": pending["direction"],
            "entry_date": entry_bar["date"],
            "entry_price": entry_price,
            "stop": stop,
            "target": target,
            "risk": risk,
            "zone_type": "OB",
            "days_held": 0,
        }
        journal["open_positions"].append(position)
        events["confirmed"].append(position)
    journal["pending_confirmation"] = still_pending

    still_open = []
    for position in journal["open_positions"]:
        bars = data_by_symbol.get(position["symbol"])
        if not bars:
            still_open.append(position)
            continue

        future_bars = [bar for bar in bars if bar["date"] > position["entry_date"]]
        closed = False
        for bar in future_bars:
            position["days_held"] += 1
            exit_price, exit_reason = None, None
            if position["direction"] == "long":
                stop_hit = bar["low"] <= position["stop"]
                target_hit = bar["high"] >= position["target"]
                if stop_hit and target_hit:
                    # Conservative policy: intrabar path noma'lum bo'lsa, stop first.
                    events["ambiguity_count"] += 1
                    exit_price, exit_reason = position["stop"], "stop"
                elif stop_hit:
                    exit_price, exit_reason = position["stop"], "stop"
                elif target_hit:
                    exit_price, exit_reason = position["target"], "target"
            else:
                stop_hit = bar["high"] >= position["stop"]
                target_hit = bar["low"] <= position["target"]
                if stop_hit and target_hit:
                    events["ambiguity_count"] += 1
                    exit_price, exit_reason = position["stop"], "stop"
                elif stop_hit:
                    exit_price, exit_reason = position["stop"], "stop"
                elif target_hit:
                    exit_price, exit_reason = position["target"], "target"

            if exit_price is None and position["days_held"] >= TIME_STOP_DAYS:
                exit_price, exit_reason = bar["close"], "time_stop"

            if exit_price is not None:
                if position["direction"] == "long":
                    r_multiple = (exit_price - position["entry_price"]) / position["risk"]
                else:
                    r_multiple = (position["entry_price"] - exit_price) / position["risk"]
                trade = {
                    **position,
                    "exit_date": bar["date"],
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "r_multiple": r_multiple,
                }
                journal["closed_trades"].append(trade)
                events["closed"].append(trade)
                closed = True
                break

        if not closed:
            still_open.append(position)
    journal["open_positions"] = still_open

    tracked_symbols = {p["symbol"] for p in journal["pending_confirmation"]} | {
        p["symbol"] for p in journal["open_positions"]
    }
    for result in scan_results:
        if result.get("status") == "signal_pending" and result["symbol"] not in tracked_symbols:
            entry = {
                "symbol": result["symbol"],
                "direction": result["direction"],
                "zone_top": result["zone_top"],
                "zone_bottom": result["zone_bottom"],
                "detected_date": result["date"],
                "zone_status_before_signal": result.get("zone_status_before_signal"),
                "zone_status_after_signal": result.get("zone_status_after_signal"),
            }
            journal["pending_confirmation"].append(entry)
            events["new_pending"].append(entry)

    return journal, events


def rolling_stats(journal, last_n=None):
    trades = journal["closed_trades"]
    if last_n:
        trades = trades[-last_n:]
    if not trades:
        return {"n": 0}

    wins = [trade for trade in trades if trade["r_multiple"] > 0]
    losses = [trade for trade in trades if trade["r_multiple"] <= 0]
    total_r = sum(trade["r_multiple"] for trade in trades)
    gross_win = sum(trade["r_multiple"] for trade in wins)
    gross_loss = abs(sum(trade["r_multiple"] for trade in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")

    by_symbol = {}
    for trade in trades:
        by_symbol.setdefault(trade["symbol"], []).append(trade["r_multiple"])
    by_symbol_total = {symbol: sum(values) for symbol, values in by_symbol.items()}
    best = sorted(by_symbol_total.items(), key=lambda item: -item[1])[:3]
    worst = sorted(by_symbol_total.items(), key=lambda item: item[1])[:3]
    return {
        "n": len(trades),
        "win_rate": len(wins) / len(trades) * 100,
        "avg_r": total_r / len(trades),
        "total_r": total_r,
        "profit_factor": profit_factor,
        "best_tickers": best,
        "worst_tickers": worst,
    }
