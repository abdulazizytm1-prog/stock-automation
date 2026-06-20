# Daily Stock Research Scanner

Daily scanner that tracks order-block retests for research. It does not place trades.

## Current Status

| Area | Status | Notes |
|---|---|---|
| `engine.py` | tested locally | Swing/FVG/OB detection runs locally |
| `scan.py` | tested locally | Fresh-zone retest logic added, still needs first live run |
| `journal.py` | tested locally | Conservative stop-first ambiguity policy added |
| `fetch_data.py` | not yet verified live | Needs first live Yahoo Finance run |
| GitHub Actions | configured, not yet verified | Workflow path fixed and test step added |
| Railway deploy | planned | Recommended as cron job, not always-on worker |
| Musaffa filter | optional | Falls back to static watchlist on missing key or API failure |

## Core Mode

Core mode uses `watchlist.txt`, fetches daily bars, scans for fresh OB retests, updates `journal.json`, and writes `report.md`.

## Optional Halal Screening Mode

If `MUSAFFA_CLIENT_ID` and `MUSAFFA_SECRET_KEY` are present, the scanner applies Musaffa screening before fetching bars.

Modes written into every run:

- `static_watchlist`
- `dynamic_musaffa`
- `fallback_static`

## Local Run

```bash
pip install -r requirements.txt
python test_pipeline.py
python run_daily.py
```

Expected artifacts:

- `report.md`
- `journal.json`

## GitHub Actions

Workflow file lives at `.github/workflows/daily_scan.yml`.

Current job order:

1. Install dependencies
2. Run `python test_pipeline.py`
3. Run `python run_daily.py`
4. Commit updated `journal.json` and `report.md`

## Railway Deploy

Recommended model:

1. Deploy this repo as a service
2. Set env vars in Railway
3. Run `python run_daily.py` from a Railway cron job
4. Persist or export `journal.json` and `report.md` if needed

This repository does not include a permanent worker config because the scanner is intended to run on a schedule, not as a long-lived process.

## Reproducibility

Each run stores these fields in `journal.json` metadata and report output:

- `scan_date`
- `scanner_version`
- `halal_filter_mode`
- `final_watchlist`
- `market_data_status`

## Known Limitations

- First live `yfinance` run is still required.
- First live GitHub Actions run is still required.
- Intraday SL/TP ordering is resolved with a conservative stop-first rule because daily candles cannot reveal the true path.
- The scanner is a research tracker, not a validated production trading system.
