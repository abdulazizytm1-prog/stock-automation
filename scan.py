"""
scan.py - Bugungi kun uchun har bir ticker holatini aniqlaydi.

QAROR:
- FVG moduli o'chirilgan. Bu yerda umuman tekshirilmaydi.
- OB "Research Candidate" sifatida ishlatiladi.
- Signal faqat latest candle fresh zonaga birinchi valid retest qilganda chiqadi.
"""

from engine import detect_order_blocks, detect_swings, determine_trend

BUFFER_PCT = 0.003
TARGET_R = 2.0


def compute_setup_grade(discount_present: bool, displacement_present: bool) -> str:
    """A if both true, B if exactly one true, C if both false."""
    count = int(discount_present) + int(displacement_present)
    if count == 2:
        return "A"
    if count == 1:
        return "B"
    return "C"


def _discount_present(bars, zone) -> bool:
    # observational placeholder; does not affect signal generation
    return False


def _displacement_present(bars, zone) -> bool:
    # observational placeholder; does not affect signal generation
    return False


def _bar_touches_zone(bar, zone):
    return bar["high"] >= zone["bottom"] and bar["low"] <= zone["top"]


def _zone_invalidated(zone, bars, upto_index):
    history = bars[zone["bos_index"] + 1 : upto_index + 1]
    if zone["type"] == "bullish":
        return any(bar["close"] < zone["bottom"] for bar in history)
    return any(bar["close"] > zone["top"] for bar in history)


def _zone_status(zone, bars, upto_index, expiry_bars=60):
    if upto_index <= zone["bos_index"]:
        return "fresh"
    if upto_index - zone["bos_index"] > expiry_bars:
        return "expired"
    if _zone_invalidated(zone, bars, upto_index):
        return "invalidated"
    history = bars[zone["bos_index"] + 1 : upto_index + 1]
    if any(_bar_touches_zone(bar, zone) for bar in history):
        return "touched"
    return "fresh"


def scan_symbol(symbol, bars):
    """Bitta ticker uchun bugungi holatni qaytaradi."""
    if len(bars) < 20:
        return {"symbol": symbol, "status": "error", "reason": "yetarli tarixiy bar yo'q"}

    swings = detect_swings(bars, lookback=2)
    trend = determine_trend(swings)
    result = {"symbol": symbol, "trend": trend, "date": bars[-1]["date"]}

    if trend == "RANGE":
        result.update({"status": "no_setup", "reason": "trend filter failed (RANGE)"})
        return result

    direction_needed = "bullish" if trend == "BULLISH" else "bearish"
    latest_index = len(bars) - 1
    prior_index = latest_index - 1
    today = bars[latest_index]

    ob_zones = []
    for zone in detect_order_blocks(bars, swings):
        if zone["type"] != direction_needed:
            continue
        if zone["bos_index"] >= latest_index:
            continue
        zone["status_before_today"] = _zone_status(zone, bars, prior_index)
        ob_zones.append(zone)

    if not ob_zones:
        result.update({"status": "no_setup", "reason": f"faol OB zona yo'q ({trend} trendda)"})
        return result

    touched = None
    for zone in sorted(ob_zones, key=lambda item: item["index"], reverse=True):
        if zone["status_before_today"] != "fresh":
            continue
        if _bar_touches_zone(today, zone):
            touched = zone
            break

    if touched is None:
        result.update(
            {
                "status": "no_setup",
                "reason": "latest candle fresh OB zonega birinchi valid retest qilmadi",
            }
        )
        return result

    ref_price = today["close"]
    buffer = ref_price * BUFFER_PCT
    if direction_needed == "bullish":
        approx_stop = touched["bottom"] - buffer
        direction = "long"
    else:
        approx_stop = touched["top"] + buffer
        direction = "short"

    discount = _discount_present(bars, touched)
    displacement = _displacement_present(bars, touched)

    result.update(
        {
            "status": "signal_pending",
            "setup": "OB wick touch (Research Candidate)",
            "direction": direction,
            "zone_type": "OB",
            "zone_top": touched["top"],
            "zone_bottom": touched["bottom"],
            "approx_stop": approx_stop,
            "zone_status_before_signal": touched["status_before_today"],
            "zone_status_after_signal": "touched",
            "reason": f"price returned to fresh {direction_needed} OB",
            "note": "PF=1.03 (costsiz), cost bilan FAIL - faqat kuzatish uchun, trade tavsiyasi emas",
            "discount_present": discount,
            "displacement_present": displacement,
            "setup_grade": compute_setup_grade(discount, displacement),
        }
    )
    return result


def scan_watchlist(data_by_symbol):
    """data_by_symbol: {symbol: bars}. Har bir ticker uchun scan_symbol chaqiradi."""
    return [scan_symbol(sym, bars) for sym, bars in data_by_symbol.items()]
