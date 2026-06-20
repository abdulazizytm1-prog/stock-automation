"""
Backtest Engine - Swing / FVG / OB tizimini Python'da walk-forward tarzda sinash.
"""

import csv


def load_bars(path):
    bars = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bars.append(
                {
                    "date": row["Date"],
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                }
            )
    bars.sort(key=lambda b: b["date"])
    return bars


def load_bars_grouped(path):
    """Merged multi-ticker CSV (Date,Open,High,Low,Close,Volume,Name) -> {symbol: bars}."""
    by_symbol = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if "Name" not in (reader.fieldnames or []):
            raise ValueError("Missing required column: Name")
        for row in reader:
            try:
                bar = {
                    "date": row["Date"],
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                }
            except (ValueError, KeyError):
                continue
            by_symbol.setdefault(row["Name"], []).append(bar)
    for sym in by_symbol:
        by_symbol[sym].sort(key=lambda b: b["date"])
    return by_symbol


def slice_window(bars, start_date, end_date):
    return [b for b in bars if start_date <= b["date"] <= end_date]


def detect_swings(bars, lookback=2):
    swings = []
    n = len(bars)
    for i in range(lookback, n - lookback):
        left = bars[i - lookback : i]
        right = bars[i + 1 : i + 1 + lookback]
        is_high = all(bars[i]["high"] > b["high"] for b in left) and all(
            bars[i]["high"] > b["high"] for b in right
        )
        is_low = all(bars[i]["low"] < b["low"] for b in left) and all(
            bars[i]["low"] < b["low"] for b in right
        )
        if is_high:
            swings.append({"index": i, "type": "high", "price": bars[i]["high"]})
        if is_low:
            swings.append({"index": i, "type": "low", "price": bars[i]["low"]})
    return swings


def determine_trend(swings):
    highs = [s for s in swings if s["type"] == "high"][-2:]
    lows = [s for s in swings if s["type"] == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "RANGE"
    higher_high = highs[1]["price"] > highs[0]["price"]
    higher_low = lows[1]["price"] > lows[0]["price"]
    lower_high = highs[1]["price"] < highs[0]["price"]
    lower_low = lows[1]["price"] < lows[0]["price"]
    if higher_high and higher_low:
        return "BULLISH"
    if lower_high and lower_low:
        return "BEARISH"
    return "RANGE"


def detect_fvg(bars):
    zones = []
    n = len(bars)
    for i in range(1, n - 1):
        c1, c3 = bars[i - 1], bars[i + 1]
        if c1["high"] < c3["low"]:
            zones.append({"index": i, "type": "bullish", "top": c3["low"], "bottom": c1["high"]})
        elif c1["low"] > c3["high"]:
            zones.append({"index": i, "type": "bearish", "top": c1["low"], "bottom": c3["high"]})
    for zone in zones:
        after = bars[zone["index"] + 1 :]
        zone["filled"] = any(
            b["low"] <= zone["top"] and b["high"] >= zone["bottom"] for b in after
        )
    return zones


def detect_order_blocks(bars, swings):
    def candle_open(bar):
        return bar["open"]

    obs = []
    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]

    for sh in highs:
        for j in range(sh["index"] + 1, len(bars)):
            if bars[j]["close"] > sh["price"]:
                for k in range(j - 1, sh["index"] - 1, -1):
                    if bars[k]["close"] < candle_open(bars[k]):
                        obs.append(
                            {
                                "index": k,
                                "type": "bullish",
                                "top": bars[k]["high"],
                                "bottom": bars[k]["low"],
                                "bos_index": j,
                            }
                        )
                        break
                break

    for sl in lows:
        for j in range(sl["index"] + 1, len(bars)):
            if bars[j]["close"] < sl["price"]:
                for k in range(j - 1, sl["index"] - 1, -1):
                    if bars[k]["close"] > candle_open(bars[k]):
                        obs.append(
                            {
                                "index": k,
                                "type": "bearish",
                                "top": bars[k]["high"],
                                "bottom": bars[k]["low"],
                                "bos_index": j,
                            }
                        )
                        break
                break

    obs.sort(key=lambda o: o["index"])
    return obs
