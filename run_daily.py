"""run_daily.py - Kunlik pipeline'ning bosh fayli."""

import os
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from fetch_data import fetch_all
from journal import load_journal, rolling_stats, save_journal, update_journal
from report import generate_report
from scan import scan_watchlist

WATCHLIST_PATH = "watchlist.txt"
JOURNAL_PATH = "journal.json"
REPORT_PATH = "report.md"
LOOKBACK_DAYS = 180
SCANNER_VERSION = "2026.06.20"


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

    symbols = load_watchlist(WATCHLIST_PATH)
    print(f"Watchlist (statik): {len(symbols)} ticker -> {symbols}")

    symbols, halal_filter_mode = apply_dynamic_halal_filter(symbols)
    print(f"Watchlist (filtrdan keyin): {len(symbols)} ticker -> {symbols}")

    data, errors = fetch_all(symbols, LOOKBACK_DAYS)
    print(f"Fetch natija: {len(data)} muvaffaqiyatli, {len(errors)} xato")
    for symbol, error in errors.items():
        print(f"  XATO {symbol}: {error}")

    if data:
        today_date = max(bars[-1]["date"] for bars in data.values() if bars)
    else:
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    market_data_status = "fresh"
    utc_today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not data:
        market_data_status = "fetch_failed"
        print("Hech qanday ma'lumot olinmadi - report warning bilan yoziladi.")
    elif today_date < utc_today:
        market_data_status = "no fresh market data / market holiday"

    run_meta = {
        "scan_date": today_date,
        "scanner_version": SCANNER_VERSION,
        "halal_filter_mode": halal_filter_mode,
        "final_watchlist": symbols,
        "market_data_status": market_data_status,
    }

    scan_results = scan_watchlist(data) if data else []
    journal = load_journal(JOURNAL_PATH)
    journal, events = update_journal(journal, data, scan_results, run_meta=run_meta)
    save_journal(journal, JOURNAL_PATH)

    rolling = rolling_stats(journal)
    report_md = generate_report(scan_results, events, rolling, errors, today_date, run_meta=run_meta)
    with open(REPORT_PATH, "w") as f:
        f.write(report_md)

    print(f"\nHisobot yozildi: {REPORT_PATH}")
    print(
        f"Journal yangilandi: {JOURNAL_PATH} "
        f"(pending={len(journal['pending_confirmation'])}, "
        f"open={len(journal['open_positions'])}, "
        f"closed={len(journal['closed_trades'])})"
    )


if __name__ == "__main__":
    main()
