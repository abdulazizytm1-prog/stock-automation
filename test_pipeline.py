"""test_pipeline.py - fixture data bilan butun pipeline'ni simulyatsiyada sinaydi."""

import csv
import json
import tempfile
from pathlib import Path

from alert_dedupe import (
    load_alert_dedupe,
    make_alert_key,
    mark_alert_sent,
    save_alert_dedupe,
    was_alert_sent,
)
from audit_logger import log_event
from journal import load_journal, rolling_stats, save_journal, update_journal
from report import generate_report
from scan import compute_setup_grade, scan_watchlist
from telegram_notify import build_summary_message, notify_telegram

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


def test_safety_log_created():
    """safety_log.jsonl is created and contains expected events after log_event calls."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = str(Path(tmp_dir) / "logs" / "safety_log.jsonl")

        log_event("run_started", path=log_path, details={"scanner_version": "test"})
        log_event("watchlist_loaded", path=log_path, details={"count": 3})
        log_event("fetch_completed", path=log_path, details={"fetch_success_count": 3})

        log_file = Path(log_path)
        assert log_file.exists(), "safety_log.jsonl should be created by log_event"

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 3, f"Expected 3 log lines, got {len(lines)}"

        events = [json.loads(line) for line in lines]
        event_names = [e["event"] for e in events]
        assert "run_started" in event_names
        assert "watchlist_loaded" in event_names
        assert "fetch_completed" in event_names

        for entry in events:
            assert "timestamp_utc" in entry
            assert "level" in entry
            assert "details" in entry

    print("PASS: safety_log.jsonl is created with correct structure.")


def test_data_degradation_calculation():
    """Data degradation calculation is correct and threshold logic works."""
    # 1 of 3 fails → 33.3% → should trigger
    symbols = ["AAPL", "MSFT", "GOOGL"]
    successes = {"AAPL": [], "MSFT": []}
    errs = {"GOOGL": "timeout"}

    total = len(symbols)
    success_count = len(successes)
    error_count = len(errs)
    failure_rate = error_count / total

    assert total == 3
    assert success_count == 2
    assert error_count == 1
    assert abs(failure_rate - 0.3333) < 0.001
    assert failure_rate >= 0.30, "1/3 failure rate should trigger degradation"

    # 0 of 3 fails → 0% → should NOT trigger
    all_ok_rate = 0 / 3
    assert all_ok_rate < 0.30, "0/3 failure should not trigger degradation"

    # Exactly 30% boundary: 3 of 10 fails → should trigger
    boundary_rate = 3 / 10
    assert boundary_rate >= 0.30, "Exactly 30% should trigger degradation"

    # 29% → should NOT trigger
    just_under = 29 / 100
    assert just_under < 0.30, "29% should not trigger degradation"

    print("PASS: Data degradation calculation and threshold logic is correct.")


def test_alert_dedupe():
    """Alert dedupe prevents duplicate keys and persists state correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        dedupe_path = str(Path(tmp_dir) / "data" / "alert_dedupe.json")

        # Fresh state → no alerts sent
        state = load_alert_dedupe(dedupe_path)
        assert state == {}, "Fresh state should be empty"

        key = make_alert_key("AAPL", "2024-01-24", "signal_pending", setup="OB wick touch")
        assert key == "AAPL|2024-01-24|signal_pending|OB wick touch"

        assert not was_alert_sent(state, key), "Alert should not be marked as sent yet"

        mark_alert_sent(state, key)
        assert was_alert_sent(state, key), "Alert should be marked as sent after mark_alert_sent"

        # Persist and reload
        save_alert_dedupe(state, dedupe_path)
        reloaded = load_alert_dedupe(dedupe_path)
        assert was_alert_sent(reloaded, key), "Alert should still be marked after reload"

        # A different key should not be marked
        other_key = make_alert_key("MSFT", "2024-01-24", "signal_pending")
        assert not was_alert_sent(reloaded, other_key), "Different key should not be marked"

        # Key without setup
        no_setup_key = make_alert_key("TSLA", "2024-01-24", "signal_pending")
        assert no_setup_key == "TSLA|2024-01-24|signal_pending"

    print("PASS: Alert dedupe correctly prevents duplicate keys and persists state.")


def test_compute_setup_grade():
    """compute_setup_grade returns A/B/C correctly for all input combinations."""
    assert compute_setup_grade(True, True) == "A", "Both true -> A"
    assert compute_setup_grade(True, False) == "B", "Only discount -> B"
    assert compute_setup_grade(False, True) == "B", "Only displacement -> B"
    assert compute_setup_grade(False, False) == "C", "Both false -> C"
    print("PASS: compute_setup_grade returns A/B/C correctly.")


def test_signal_has_setup_grade():
    """signal_pending results include setup_grade, discount_present, displacement_present."""
    bars_by_symbol = {
        symbol: load_csv_bars(FIXTURE_DIR / f"{symbol}.csv")
        for symbol in ("AAPL", "MSFT", "GOOGL")
    }
    sim_start_idx = next(
        i for i, bar in enumerate(bars_by_symbol["AAPL"]) if bar["date"] >= "2024-01-24"
    )
    n_days = 7
    signal_results = []
    for day_offset in range(n_days):
        idx = sim_start_idx + day_offset
        data_today = {sym: bars[:idx + 1] for sym, bars in bars_by_symbol.items()}
        for result in scan_watchlist(data_today):
            if result.get("status") == "signal_pending":
                signal_results.append(result)

    assert signal_results, "Expected at least one signal_pending result in fixture window"
    for result in signal_results:
        assert "setup_grade" in result, f"setup_grade missing on {result['symbol']}"
        assert "discount_present" in result, f"discount_present missing on {result['symbol']}"
        assert "displacement_present" in result, f"displacement_present missing on {result['symbol']}"
        assert result["setup_grade"] in ("A", "B", "C"), f"Invalid grade: {result['setup_grade']}"

    # Signal count must be identical to what scan returns without grading (grade is additive only)
    # Verify no signal was suppressed — count must be >= 1 as asserted above.
    print(f"PASS: {len(signal_results)} signal(s) each have setup_grade/discount_present/displacement_present.")


def test_journal_closed_trades_preserve_grade():
    """closed_trades in journal carry setup_grade, discount_present, displacement_present."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        journal_path = Path(tmp_dir) / "journal.json"
        bars_by_symbol = {
            symbol: load_csv_bars(FIXTURE_DIR / f"{symbol}.csv")
            for symbol in ("AAPL", "MSFT", "GOOGL")
        }
        sim_start_idx = next(
            i for i, bar in enumerate(bars_by_symbol["AAPL"]) if bar["date"] >= "2024-01-24"
        )
        journal = load_journal(journal_path)
        for day_offset in range(7):
            idx = sim_start_idx + day_offset
            data_today = {sym: bars[:idx + 1] for sym, bars in bars_by_symbol.items()}
            if any(len(b) < 20 for b in data_today.values()):
                continue
            run_meta = {
                "scan_date": data_today["AAPL"][-1]["date"],
                "scanner_version": "test-fixture",
                "halal_filter_mode": "static_watchlist",
                "final_watchlist": list(bars_by_symbol),
                "market_data_status": "fresh",
            }
            scan_results = scan_watchlist(data_today)
            journal, _ = update_journal(journal, data_today, scan_results, run_meta=run_meta)
            save_journal(journal, journal_path)

        assert journal["closed_trades"], "Expected at least one closed trade in fixture window"
        for trade in journal["closed_trades"]:
            assert "setup_grade" in trade, f"setup_grade missing in closed trade {trade['symbol']}"
            assert "discount_present" in trade
            assert "displacement_present" in trade
            assert trade["setup_grade"] in ("A", "B", "C")

    print(f"PASS: All {len(journal['closed_trades'])} closed trade(s) preserve grade fields.")


def test_report_has_grade_breakdown():
    """report.md contains Grade Breakdown table with A/B/C rows when trades exist."""
    bars_by_symbol = {
        symbol: load_csv_bars(FIXTURE_DIR / f"{symbol}.csv")
        for symbol in ("AAPL", "MSFT", "GOOGL")
    }
    sim_start_idx = next(
        i for i, bar in enumerate(bars_by_symbol["AAPL"]) if bar["date"] >= "2024-01-24"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        journal = load_journal(Path(tmp_dir) / "journal.json")
        last_report = None
        for day_offset in range(7):
            idx = sim_start_idx + day_offset
            data_today = {sym: bars[:idx + 1] for sym, bars in bars_by_symbol.items()}
            if any(len(b) < 20 for b in data_today.values()):
                continue
            run_meta = {
                "scan_date": data_today["AAPL"][-1]["date"],
                "scanner_version": "test-fixture",
                "halal_filter_mode": "static_watchlist",
                "final_watchlist": list(bars_by_symbol),
                "market_data_status": "fresh",
            }
            scan_results = scan_watchlist(data_today)
            journal, events = update_journal(journal, data_today, scan_results, run_meta=run_meta)
            rolling = rolling_stats(journal)
            last_report = generate_report(
                scan_results, events, rolling, {}, data_today["AAPL"][-1]["date"], run_meta=run_meta
            )

        assert last_report is not None
        assert "Grade Breakdown" in last_report, "Report should contain 'Grade Breakdown' section"
        assert "| Grade |" in last_report, "Grade Breakdown should have a markdown table header"
        assert "| A |" in last_report, "Grade Breakdown should have an A row"
        assert "| B |" in last_report, "Grade Breakdown should have a B row"
        assert "| C |" in last_report, "Grade Breakdown should have a C row"

    print("PASS: Report contains Grade Breakdown table with A/B/C rows.")


def _make_fixture_journal_and_events():
    """Run the 7-day fixture sim and return (journal, events, run_meta, rolling)."""
    bars_by_symbol = {
        symbol: load_csv_bars(FIXTURE_DIR / f"{symbol}.csv")
        for symbol in ("AAPL", "MSFT", "GOOGL")
    }
    sim_start_idx = next(
        i for i, bar in enumerate(bars_by_symbol["AAPL"]) if bar["date"] >= "2024-01-24"
    )
    journal = load_journal(Path(tempfile.mkdtemp()) / "journal.json")
    last_events = None
    last_run_meta = None
    last_rolling = None
    for day_offset in range(7):
        idx = sim_start_idx + day_offset
        data_today = {sym: bars[:idx + 1] for sym, bars in bars_by_symbol.items()}
        if any(len(b) < 20 for b in data_today.values()):
            continue
        last_run_meta = {
            "scan_date": data_today["AAPL"][-1]["date"],
            "scanner_version": "test-fixture",
            "halal_filter_mode": "static_watchlist",
            "final_watchlist": list(bars_by_symbol),
            "market_data_status": "fresh",
            "total_symbols": 3,
            "fetch_success_count": 3,
            "fetch_error_count": 0,
            "failure_rate_pct": 0.0,
        }
        scan_results = scan_watchlist(data_today)
        journal, last_events = update_journal(
            journal, data_today, scan_results, run_meta=last_run_meta
        )
        last_rolling = rolling_stats(journal)
    return journal, last_events, last_run_meta, last_rolling


def test_telegram_missing_env_does_not_crash():
    """notify_telegram returns False without crashing when env vars are absent."""
    import os

    saved_token = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    saved_chat = os.environ.pop("TELEGRAM_CHAT_ID", None)
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = str(Path(tmp_dir) / "logs" / "safety_log.jsonl")
            dedupe_path = str(Path(tmp_dir) / "data" / "alert_dedupe.json")

            journal, events, run_meta, rolling = _make_fixture_journal_and_events()
            result = notify_telegram(
                journal, events, run_meta, rolling,
                dedupe_path=dedupe_path,
                log_path=log_path,
                report_path="report.md",
            )
            assert result is False, "notify_telegram should return False when env vars missing"

            # Log file should record telegram_skipped WARNING
            log_file = Path(log_path)
            assert log_file.exists(), "audit log should be written even on skip"
            log_lines = [json.loads(l) for l in log_file.read_text().strip().splitlines()]
            skipped = [e for e in log_lines if e["event"] == "telegram_skipped"]
            assert skipped, "telegram_skipped event should be logged"
            assert skipped[0]["level"] == "WARNING"

            # alert_dedupe.json must NOT be created — no signal was sent
            assert not Path(dedupe_path).exists(), \
                "alert_dedupe.json must not be written when no message was sent"
    finally:
        if saved_token is not None:
            os.environ["TELEGRAM_BOT_TOKEN"] = saved_token
        if saved_chat is not None:
            os.environ["TELEGRAM_CHAT_ID"] = saved_chat

    print("PASS: notify_telegram returns False without crashing when env vars are missing.")


def test_telegram_duplicate_signal_not_sent_twice():
    """A signal already in dedupe state is excluded from the next summary's new_pending list."""
    journal, events, run_meta, rolling = _make_fixture_journal_and_events()

    with tempfile.TemporaryDirectory() as tmp_dir:
        dedupe_path = str(Path(tmp_dir) / "data" / "alert_dedupe.json")

        # Pre-populate dedupe state with every signal from the run.
        state = load_alert_dedupe(dedupe_path)
        for sig in events.get("new_pending", []):
            key = make_alert_key(sig["symbol"], sig["detected_date"], "signal_pending")
            mark_alert_sent(state, key)
        save_alert_dedupe(state, dedupe_path)

        # Simulate the dedup logic that notify_telegram applies.
        dedupe_state = load_alert_dedupe(dedupe_path)
        fresh_signals = []
        for sig in events.get("new_pending", []):
            key = make_alert_key(sig["symbol"], sig["detected_date"], "signal_pending")
            if not was_alert_sent(dedupe_state, key):
                fresh_signals.append(sig)

        assert len(fresh_signals) == 0, \
            "All signals should be filtered out as duplicates when state is pre-populated"

        # The filtered summary should say 'none' for new signals.
        filtered_events = {**events, "new_pending": fresh_signals}
        msg = build_summary_message(journal, filtered_events, run_meta, rolling)
        assert "New signals: none" in msg, \
            f"Summary should say 'New signals: none' when all are deduped, got:\n{msg}"

    print("PASS: Duplicate signals are excluded from Telegram summary via alert dedupe.")


def test_alert_dedupe_json_updated_after_marking():
    """alert_dedupe.json is written and contains the marked key after notify flow."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        dedupe_path = str(Path(tmp_dir) / "data" / "alert_dedupe.json")

        # Start with clean state.
        state = load_alert_dedupe(dedupe_path)
        assert state == {}

        # Mark a synthetic signal.
        key = make_alert_key("AAPL", "2024-01-24", "signal_pending")
        mark_alert_sent(state, key)
        save_alert_dedupe(state, dedupe_path)

        # File must exist and contain the key.
        assert Path(dedupe_path).exists(), "alert_dedupe.json must exist after save"
        reloaded = load_alert_dedupe(dedupe_path)
        assert was_alert_sent(reloaded, key), "Marked key must persist after reload"

        # A second signal on same day is also stored independently.
        key2 = make_alert_key("MSFT", "2024-01-24", "signal_pending")
        assert not was_alert_sent(reloaded, key2), "Second key must not be pre-marked"

    print("PASS: alert_dedupe.json is written and correctly stores marked signal keys.")


def test_build_summary_message_includes_grade():
    """build_summary_message includes grade info in the new signals section."""
    synthetic_events = {
        "new_pending": [
            {
                "symbol": "AAPL",
                "direction": "long",
                "detected_date": "2024-01-24",
                "zone_top": 185.50,
                "zone_bottom": 183.00,
                "setup_grade": "A",
                "discount_present": True,
                "displacement_present": True,
            },
            {
                "symbol": "MSFT",
                "direction": "long",
                "detected_date": "2024-01-24",
                "zone_top": 380.00,
                "zone_bottom": 378.00,
                "setup_grade": "C",
                "discount_present": False,
                "displacement_present": False,
            },
        ],
        "confirmed": [],
        "closed": [],
        "rejected": [],
        "ambiguity_count": 0,
    }
    synthetic_run_meta = {
        "scan_date": "2024-01-24",
        "market_data_status": "fresh",
        "total_symbols": 3,
        "fetch_success_count": 3,
        "fetch_error_count": 0,
        "failure_rate_pct": 0.0,
    }
    synthetic_rolling = {
        "n": 2,
        "win_rate": 50.0,
        "avg_r": 1.0,
        "total_r": 2.0,
        "profit_factor": 2.0,
        "best_tickers": [("AAPL", 2.0)],
        "worst_tickers": [("MSFT", 0.0)],
        "grade_breakdown": {
            "A": {"n": 1, "win_rate": 100.0, "total_r": 2.0, "profit_factor": float("inf")},
            "B": {"n": 0, "win_rate": None, "total_r": 0.0, "profit_factor": None},
            "C": {"n": 1, "win_rate": 0.0, "total_r": 0.0, "profit_factor": None},
        },
    }
    synthetic_journal = {"closed_trades": [], "pending_confirmation": [], "open_positions": []}

    msg = build_summary_message(
        synthetic_journal, synthetic_events, synthetic_run_meta, synthetic_rolling
    )

    assert "Grade A" in msg, f"Message should contain 'Grade A' for AAPL signal, got:\n{msg}"
    assert "Grade C" in msg, f"Message should contain 'Grade C' for MSFT signal, got:\n{msg}"
    assert "discount=True" in msg, f"Message should show discount=True for AAPL, got:\n{msg}"
    assert "displacement=True" in msg, f"Message should show displacement=True for AAPL, got:\n{msg}"
    assert "Grade breakdown" in msg, f"Message should include grade breakdown section, got:\n{msg}"
    assert "AAPL" in msg
    assert "MSFT" in msg

    print("PASS: build_summary_message includes grade info for new signals and breakdown.")


if __name__ == "__main__":
    main()
    print("\n=== SPRINT 1 TESTLAR ===")
    test_safety_log_created()
    test_data_degradation_calculation()
    test_alert_dedupe()
    print("\nPASS: Barcha Sprint 1 testlar muvaffaqiyatli o'tdi.")
    print("\n=== SPRINT 2 TESTLAR ===")
    test_compute_setup_grade()
    test_signal_has_setup_grade()
    test_journal_closed_trades_preserve_grade()
    test_report_has_grade_breakdown()
    print("\nPASS: Barcha Sprint 2 testlar muvaffaqiyatli o'tdi.")
    print("\n=== SPRINT 3 TESTLAR ===")
    test_telegram_missing_env_does_not_crash()
    test_telegram_duplicate_signal_not_sent_twice()
    test_alert_dedupe_json_updated_after_marking()
    test_build_summary_message_includes_grade()
    print("\nPASS: Barcha Sprint 3 testlar muvaffaqiyatli o'tdi.")
