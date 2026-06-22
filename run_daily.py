"""run_daily.py - Kunlik pipeline'ning bosh fayli."""

import os
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from analytics import compute_edge_analytics
from audit_logger import log_event
from fetch_data import fetch_all
from journal import load_journal, rolling_stats, save_journal, update_journal
from report import generate_report
from scan import scan_watchlist
from telegram_notify import notify_telegram

WATCHLIST_PATH = "watchlist.txt"
JOURNAL_PATH = "journal.json"
REPORT_PATH = "report.md"
LOG_PATH = "logs/safety_log.jsonl"
LOOKBACK_DAYS = 180
SCANNER_VERSION = "2026.06.20"
DEGRADATION_THRESHOLD = 0.30


def load_watchlist(path):
    symbols = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                symbols.append(line)
    return symbols


def apply_dynamic_halal_filter(symbols):
    client_id = os.environ.get("MUSAFFA_CLIENT_ID")
    secret_key = os.environ.get("MUSAFFA_SECRET_KEY")
    if not client_id or not secret_key:
        print("Dinamik halal filtr o'chiq - statik watchlist.txt ishlatilmoqda.")
        return symbols, "static_watchlist"

    from halal_filter import filter_watchlist

    print("Dinamik halal filtr YONIQ - Musaffa API orqali tekshirilmoqda...")
    try:
        passed, _statuses = filter_watchlist(symbols, client_id, secret_key, strict=True)
        dropped = [symbol for symbol in symbols if symbol not in passed]
        if dropped:
            print(f"Filtr tushirdi: {dropped}")
        return passed, "dynamic_musaffa"
    except Exception as exc:
        print(
            f"OGOHLANTIRISH: Musaffa API xato berdi ({exc}) - "
            "xavfsizlik uchun statik ro'yxatga qaytildi."
        )
        return symbols, "fallback_static"


def main():
    if load_dotenv is not None:
        load_dotenv()

    log_event("run_started", path=LOG_PATH, details={"scanner_version": SCANNER_VERSION})

    symbols = load_watchlist(WATCHLIST_PATH)
    print(f"Watchlist (statik): {len(symbols)} ticker -> {symbols}")
    log_event("watchlist_loaded", path=LOG_PATH, details={"count": len(symbols), "symbols": symbols})

    symbols, halal_filter_mode = apply_dynamic_halal_filter(symbols)
    print(f"Watchlist (filtrdan keyin): {len(symbols)} ticker -> {symbols}")
    log_event(
        "halal_filter_applied",
        path=LOG_PATH,
        details={"mode": halal_filter_mode, "count": len(symbols), "symbols": symbols},
    )

    data, errors = fetch_all(symbols, LOOKBACK_DAYS)
    print(f"Fetch natija: {len(data)} muvaffaqiyatli, {len(errors)} xato")
    for symbol, error in errors.items():
        print(f"  XATO {symbol}: {error}")

    total_symbols = len(symbols)
    fetch_success_count = len(data)
    fetch_error_count = len(errors)
    failure_rate = fetch_error_count / total_symbols if total_symbols > 0 else 0.0

    log_event(
        "fetch_completed",
        path=LOG_PATH,
        details={
            "total_symbols": total_symbols,
            "fetch_success_count": fetch_success_count,
            "fetch_error_count": fetch_error_count,
            "failure_rate_pct": round(failure_rate * 100, 1),
            "errors": errors,
        },
    )

    if data:
        today_date = max(bars[-1]["date"] for bars in data.values() if bars)
    else:
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    utc_today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    market_data_status = "fresh"
    if not data:
        market_data_status = "fetch_failed"
        print("Hech qanday ma'lumot olinmadi - report warning bilan yoziladi.")
    elif failure_rate >= DEGRADATION_THRESHOLD:
        market_data_status = "data_degradation"
        log_event(
            "data_degradation_alert",
            level="WARNING",
            path=LOG_PATH,
            details={
                "failure_rate_pct": round(failure_rate * 100, 1),
                "fetch_error_count": fetch_error_count,
                "total_symbols": total_symbols,
                "failed_symbols": list(errors.keys()),
            },
        )
        print(
            f"OGOHLANTIRISH: Ma'lumot degradatsiyasi - {fetch_error_count}/{total_symbols} "
            f"ticker ({failure_rate * 100:.1f}%) muvaffaqiyatsiz. Hisobot davom ettiriladi."
        )
    elif today_date < utc_today:
        market_data_status = "no fresh market data / market holiday"

    run_meta = {
        "scan_date": today_date,
        "scanner_version": SCANNER_VERSION,
        "halal_filter_mode": halal_filter_mode,
        "final_watchlist": symbols,
        "market_data_status": market_data_status,
        "total_symbols": total_symbols,
        "fetch_success_count": fetch_success_count,
        "fetch_error_count": fetch_error_count,
        "failure_rate_pct": round(failure_rate * 100, 1),
    }

    scan_results = scan_watchlist(data) if data else []
    log_event(
        "scan_completed",
        path=LOG_PATH,
        details={
            "total_scanned": len(scan_results),
            "signals": len([r for r in scan_results if r.get("status") == "signal_pending"]),
            "no_setup": len([r for r in scan_results if r.get("status") == "no_setup"]),
            "errors": len([r for r in scan_results if r.get("status") == "error"]),
        },
    )

    journal = load_journal(JOURNAL_PATH)
    journal, events = update_journal(journal, data, scan_results, run_meta=run_meta)
    save_journal(journal, JOURNAL_PATH)
    log_event(
        "journal_updated",
        path=LOG_PATH,
        details={
            "new_pending": len(events["new_pending"]),
            "confirmed": len(events["confirmed"]),
            "closed": len(events["closed"]),
            "rejected": len(events["rejected"]),
            "pending_total": len(journal["pending_confirmation"]),
            "open_total": len(journal["open_positions"]),
            "closed_total": len(journal["closed_trades"]),
        },
    )

    rolling = rolling_stats(journal)
    edge_analytics = compute_edge_analytics(journal)
    report_md = generate_report(
        scan_results, events, rolling, errors, today_date,
        run_meta=run_meta, edge_analytics=edge_analytics,
    )
    with open(REPORT_PATH, "w") as f:
        f.write(report_md)
    log_event("report_written", path=LOG_PATH, details={"path": REPORT_PATH})

    print(f"\nHisobot yozildi: {REPORT_PATH}")
    print(
        f"Journal yangilandi: {JOURNAL_PATH} "
        f"(pending={len(journal['pending_confirmation'])}, "
        f"open={len(journal['open_positions'])}, "
        f"closed={len(journal['closed_trades'])})"
    )

    log_event(
        "run_finished",
        path=LOG_PATH,
        details={
            "market_data_status": market_data_status,
            "scan_date": today_date,
        },
    )

    notify_telegram(journal, events, run_meta, rolling, log_path=LOG_PATH, report_path=REPORT_PATH)


if __name__ == "__main__":
    main()
