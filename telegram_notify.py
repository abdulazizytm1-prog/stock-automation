"""telegram_notify.py - Telegram notifications after daily scan with alert dedupe."""

import os

from alert_dedupe import (
    load_alert_dedupe,
    make_alert_key,
    mark_alert_sent,
    save_alert_dedupe,
    was_alert_sent,
)
from audit_logger import log_event

DEDUPE_PATH = "data/alert_dedupe.json"
LOG_PATH = "logs/safety_log.jsonl"
REPORT_PATH = "report.md"
_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _get_credentials():
    """Return (token, chat_id) from env vars or (None, None) if either is missing."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


def send_telegram_message(text, token=None, chat_id=None):
    """
    POST text to Telegram.  Returns True on success, False on any failure.
    If token/chat_id are None, reads from env vars.
    """
    import requests

    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        url = _API_BASE.format(token=token, method="sendMessage")
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"OGOHLANTIRISH: Telegram xabar yuborishda xato: {exc}")
        return False


def send_telegram_document(path, caption="", token=None, chat_id=None):
    """
    Upload a local file as a Telegram document.  Returns True on success, False on failure.
    """
    import requests

    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    if not os.path.exists(path):
        print(f"OGOHLANTIRISH: Telegram uchun hujjat topilmadi: {path}")
        return False
    try:
        url = _API_BASE.format(token=token, method="sendDocument")
        with open(path, "rb") as fh:
            resp = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"document": fh},
                timeout=30,
            )
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"OGOHLANTIRISH: Telegram hujjat yuborishda xato: {exc}")
        return False


def _pf_str(pf):
    if pf is None:
        return "n/a"
    return "inf" if pf == float("inf") else f"{pf:.2f}"


def build_summary_message(journal, events, run_meta, rolling):
    """
    Build a plain-text Telegram summary from the daily scan output.
    events["new_pending"] controls which new signals appear — callers may pass a
    filtered copy to implement dedupe before calling this function.
    """
    lines = []

    scan_date = run_meta.get("scan_date", "unknown")
    mds = run_meta.get("market_data_status", "unknown")
    lines.append(f"Daily Scan Report — {scan_date}")
    lines.append(f"Market data: {mds}")

    total = run_meta.get("total_symbols")
    if total is not None:
        ok = run_meta.get("fetch_success_count", 0)
        err = run_meta.get("fetch_error_count", 0)
        rate = run_meta.get("failure_rate_pct", 0.0)
        lines.append(f"Fetch: {ok}/{total} success ({err} errors, {rate:.1f}% failure)")

    lines.append("")

    new_pending = events.get("new_pending", [])
    if new_pending:
        lines.append(f"New signals ({len(new_pending)}):")
        for sig in new_pending:
            grade = sig.get("setup_grade", "C")
            discount = sig.get("discount_present", False)
            displacement = sig.get("displacement_present", False)
            lines.append(
                f"  {sig['symbol']} {sig['direction']} | Grade {grade} "
                f"| discount={discount} displacement={displacement} "
                f"| Zone {sig['zone_top']:.2f}-{sig['zone_bottom']:.2f}"
            )
    else:
        lines.append("New signals: none")

    lines.append("")
    lines.append("Journal events:")
    lines.append(f"  New pending:  {len(events.get('new_pending', []))}")
    lines.append(f"  Confirmed:    {len(events.get('confirmed', []))}")
    lines.append(f"  Closed:       {len(events.get('closed', []))}")
    lines.append(f"  Rejected:     {len(events.get('rejected', []))}")
    lines.append(f"  Ambiguity:    {events.get('ambiguity_count', 0)}")

    for trade in events.get("closed", []):
        lines.append(
            f"    Closed {trade['symbol']}: {trade['exit_reason']} R={trade['r_multiple']:.2f}"
        )

    if rolling.get("n", 0) > 0:
        lines.append("")
        lines.append(f"Rolling stats ({rolling['n']} trades):")
        lines.append(
            f"  WR={rolling['win_rate']:.1f}% | "
            f"Avg R={rolling['avg_r']:.2f} | "
            f"Total R={rolling['total_r']:.2f} | "
            f"PF={_pf_str(rolling['profit_factor'])}"
        )
        gb = rolling.get("grade_breakdown", {})
        if gb:
            lines.append("  Grade breakdown:")
            for grade in ("A", "B", "C"):
                gs = gb.get(grade, {})
                if gs.get("n", 0) > 0:
                    wr = f"{gs['win_rate']:.1f}%" if gs.get("win_rate") is not None else "n/a"
                    lines.append(
                        f"    Grade {grade}: n={gs['n']} | WR={wr} | "
                        f"R={gs['total_r']:+.2f} | PF={_pf_str(gs.get('profit_factor'))}"
                    )
                else:
                    lines.append(f"    Grade {grade}: n=0")

    return "\n".join(lines)


def notify_telegram(
    journal,
    events,
    run_meta,
    rolling,
    dedupe_path=DEDUPE_PATH,
    log_path=LOG_PATH,
    report_path=REPORT_PATH,
):
    """
    Send daily Telegram summary + report.md document.
    - Deduplicates individual signal mentions via alert_dedupe.
    - Never deduplicates the daily summary itself.
    - Silently returns False (with warning) if env vars are missing.
    - Does not crash on any API or file error.
    """
    token, chat_id = _get_credentials()
    if not token or not chat_id:
        msg = (
            "OGOHLANTIRISH: TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHAT_ID topilmadi — "
            "Telegram xabarnomasi o'chirib qo'yilgan."
        )
        print(msg)
        log_event(
            "telegram_skipped",
            level="WARNING",
            path=log_path,
            details={"reason": "missing_env_vars"},
        )
        return False

    # Load dedupe state and filter signals already sent.
    dedupe_state = load_alert_dedupe(dedupe_path)
    fresh_signals = []
    skipped = 0
    for sig in events.get("new_pending", []):
        key = make_alert_key(
            sig["symbol"],
            sig["detected_date"],
            "signal_pending",
        )
        if was_alert_sent(dedupe_state, key):
            skipped += 1
        else:
            fresh_signals.append(sig)
            mark_alert_sent(dedupe_state, key)

    # Build summary with only fresh (non-deduped) signals.
    filtered_events = {**events, "new_pending": fresh_signals}
    text = build_summary_message(journal, filtered_events, run_meta, rolling)

    # Send summary — not deduped.
    summary_ok = send_telegram_message(text, token=token, chat_id=chat_id)

    # Send report.md as document.
    doc_ok = False
    if summary_ok:
        doc_ok = send_telegram_document(
            report_path,
            caption=f"Full report — {run_meta.get('scan_date', '')}",
            token=token,
            chat_id=chat_id,
        )
        if not doc_ok:
            log_event(
                "telegram_document_failed",
                level="WARNING",
                path=log_path,
                details={"report_path": report_path},
            )

    # Persist dedupe state only after at least the summary was sent.
    if summary_ok:
        save_alert_dedupe(dedupe_state, dedupe_path)

    log_event(
        "telegram_sent" if summary_ok else "telegram_failed",
        level="INFO" if summary_ok else "WARNING",
        path=log_path,
        details={
            "summary_ok": summary_ok,
            "doc_ok": doc_ok,
            "fresh_signals": len(fresh_signals),
            "skipped_duplicate_signals": skipped,
        },
    )
    return summary_ok
