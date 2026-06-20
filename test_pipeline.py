"""test_pipeline.py - fixture data bilan butun pipeline'ni simulyatsiyada sinaydi."""

import csv
import tempfile
from pathlib import Path

from journal import load_journal, rolling_stats, save_journal, update_journal
from report import generate_report
from scan import scan_watchlist

BASE_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = BASE_DIR / "tests" / "data"


def load_csv_bars(path):
    bars = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
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


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        journal_path = Path(tmp_dir) / "journal.json"
        symbols = {"AAPL": "AAPL.csv", "MSFT": "MSFT.csv", "GOOGL": "GOOGL.csv"}
        full_bars = {
            symbol: load_csv_bars(FIXTURE_DIR / filename) for symbol, filename in symbols.items()
        }

        sim_start_idx = next(
            i for i, bar in enumerate(full_bars["AAPL"]) if bar["date"] >= "2024-01-24"
        )
        n_days_to_simulate = 7

        journal = load_journal(journal_path)
        total_signals, total_confirmed, total_closed = 0, 0, 0
        last_report = None

        for day_offset in range(n_days_to_simulate):
            idx = sim_start_idx + day_offset
            data_today = {symbol: full_bars[symbol][: idx + 1] for symbol in symbols}
            if any(len(bars) < 20 for bars in data_today.values()):
                continue

            run_meta = {
                "scan_date": data_today["AAPL"][-1]["date"],
                "scanner_version": "test-fixture",
                "halal_filter_mode": "static_watchlist",
                "final_watchlist": list(symbols),
                "market_data_status": "fresh",
            }
            scan_results = scan_watchlist(data_today)
            journal, events = update_journal(journal, data_today, scan_results, run_meta=run_meta)
            save_journal(journal, journal_path)

            total_signals += len([result for result in scan_results if result["status"] == "signal_pending"])
            total_confirmed += len(events["confirmed"])
            total_closed += len(events["closed"])

            rolling = rolling_stats(journal)
            today_date = data_today["AAPL"][-1]["date"]
            last_report = generate_report(
                scan_results, events, rolling, {}, today_date, run_meta=run_meta
            )

        print(f"=== {n_days_to_simulate} kunlik simulyatsiya yakunlandi (fixture data) ===")
        print(f"Jami yangi signal: {total_signals}")
        print(f"Jami tasdiqlangan (open bo'lgan): {total_confirmed}")
        print(f"Jami yopilgan trade: {total_closed}")
        print(
            f"Journal holati: pending={len(journal['pending_confirmation'])}, "
            f"open={len(journal['open_positions'])}, closed={len(journal['closed_trades'])}"
        )

        final_stats = rolling_stats(journal)
        print(f"\nFinal rolling stats: {final_stats}")

        assert total_signals >= 1, "Hech qanday signal topilmadi - OB retest logikasi buzilgan."
        assert total_confirmed >= 1, "Hech qanday signal tasdiqlanmadi - pipeline buzilgan."
        assert total_closed >= 1, "Hech qanday trade yopilmadi - journal lifecycle buzilgan."
        assert journal["meta"]["halal_filter_mode"] == "static_watchlist"
        print("\nPASS: pending -> confirmed -> closed hayot sikli kamida bir marta ishladi.")

        print("\n=== OXIRGI KUNLIK HISOBOT NAMUNASI ===\n")
        print(last_report)


if __name__ == "__main__":
    main()
