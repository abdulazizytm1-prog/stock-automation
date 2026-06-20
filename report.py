"""report.py - Kunlik hisobotni markdown formatda yig'adi."""


def generate_report(scan_results, journal_events, rolling, errors, today_date, run_meta=None):
    run_meta = run_meta or {}
    lines = []
    lines.append("# DAILY TRADING RESEARCH REPORT")
    lines.append("")
    lines.append(f"**Date:** {today_date}")
    lines.append("")
    lines.append(
        "> Bu BOT TRADE QILMAYDI. Faqat kuzatadi va yozib boradi. "
        "OB = Research Candidate (PF=1.03 costsiz, cost bilan FAIL). "
        "FVG = DISABLED (3 testda 0 trade)."
    )
    lines.append("")
    lines.append(f"- Halal filter mode: {run_meta.get('halal_filter_mode', 'unknown')}")
    lines.append(f"- Scanner version: {run_meta.get('scanner_version', 'unknown')}")
    lines.append(f"- Market data status: {run_meta.get('market_data_status', 'unknown')}")
    lines.append(
        f"- Final scanned watchlist: {', '.join(run_meta.get('final_watchlist', [])) or 'none'}"
    )
    lines.append("")

    signals = [result for result in scan_results if result.get("status") == "signal_pending"]
    no_setups = [result for result in scan_results if result.get("status") == "no_setup"]
    errs = [result for result in scan_results if result.get("status") == "error"] + [
        {"symbol": symbol, "reason": reason} for symbol, reason in errors.items()
    ]

    lines.append(f"## Signals found: {len(signals)}")
    lines.append("")
    n = 1
    for result in signals:
        lines.append(f"### {n}) {result['symbol']}")
        lines.append(f"- Setup: {result['setup']}")
        lines.append(f"- Trend: {result['trend'].capitalize()}")
        lines.append(f"- Reason: {result['reason']}")
        lines.append("- Entry: next day open")
        lines.append(f"- SL: zone {'low' if result['direction'] == 'long' else 'high'} +/- 0.3%")
        lines.append("- TP: 2R")
        lines.append("- Status: pending")
        lines.append(
            f"- Zone status: {result.get('zone_status_before_signal')} -> "
            f"{result.get('zone_status_after_signal')}"
        )
        lines.append(f"- Note: {result['note']}")
        lines.append("")
        n += 1

    for result in no_setups:
        lines.append(f"### {n}) {result['symbol']}")
        lines.append(
            "- No valid setup"
            if "RANGE" in result.get("reason", "") or "OB zona" in result.get("reason", "")
            else "- No trade"
        )
        lines.append(f"- Reason: {result['reason']}")
        lines.append("")
        n += 1

    if errs:
        lines.append("## Xatolar")
        for err in errs:
            lines.append(f"- {err['symbol']}: {err['reason']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Bugungi journal hodisalari")
    lines.append(f"- Yangi pending signal: {len(journal_events['new_pending'])}")
    lines.append(f"- Tasdiqlangan (open position bo'ldi): {len(journal_events['confirmed'])}")
    lines.append(f"- Yopilgan trade: {len(journal_events['closed'])}")
    lines.append(f"- Rejected signal: {len(journal_events['rejected'])}")
    lines.append(f"- Intrabar ambiguity count: {journal_events['ambiguity_count']}")
    for trade in journal_events["closed"]:
        lines.append(f"- Closed {trade['symbol']}: {trade['exit_reason']}, R={trade['r_multiple']:.2f}")
    for rejected in journal_events["rejected"]:
        lines.append(
            f"- Rejected {rejected['symbol']}: {rejected['reason']} ({rejected['entry_date']})"
        )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Rolling Statistika (jami yopilgan trade'lar)")
    if rolling["n"] == 0:
        lines.append("Hali yopilgan trade yo'q.")
    else:
        profit_factor = (
            f"{rolling['profit_factor']:.2f}"
            if rolling["profit_factor"] != float("inf")
            else "inf"
        )
        lines.append(f"- Jami trade: {rolling['n']}")
        lines.append(f"- Win rate: {rolling['win_rate']:.1f}%")
        lines.append(f"- Avg R: {rolling['avg_r']:.2f}")
        lines.append(f"- Total R: {rolling['total_r']:.2f}")
        lines.append(f"- PF: {profit_factor}")
        lines.append(
            "- Eng yaxshi tickerlar: "
            + ", ".join(f"{symbol} ({value:+.2f}R)" for symbol, value in rolling["best_tickers"])
        )
        lines.append(
            "- Eng yomon tickerlar: "
            + ", ".join(f"{symbol} ({value:+.2f}R)" for symbol, value in rolling["worst_tickers"])
        )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Hypothesis holati")
    lines.append("| Hypothesis | Status | Dalil |")
    lines.append("|---|---|---|")
    lines.append("| OB wick-touch | RESEARCH CANDIDATE | n=427, PF=1.03 costsiz, cost bilan FAIL |")
    lines.append("| FVG | DISABLED | 3 testda (n=3, n=26, n=427) 0 trade |")
    lines.append("")

    return "\n".join(lines)
