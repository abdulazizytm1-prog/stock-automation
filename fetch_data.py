"""
fetch_data.py — Kunlik D1 bar'larni yfinance orqali olish.

MUHIM (halollik): Bu fayl Claude sandbox'ida TO'LIQ sinalmagan, chunki
sandbox'ning tarmoq ruxsati Yahoo Finance domenlarini bloklaydi
(query1/query2.finance.yahoo.com — allowlist'da yo'q). Bu — backtest
auditida IBKR MCP uchun yozilgan "NOT TESTED" bayrog'ining xuddi o'zi,
endi yfinance uchun.

LIKELY ishlaydi (PROVEN emas), chunki:
- yfinance millionlab GitHub repo'da, jumladan GitHub Actions runner'larida
  muvaffaqiyatli ishlatiladi (ular ochiq internetga ega, sandbox cheklovi yo'q)
- Kutubxona o'zi yetuk va keng qo'llaniladi

Birinchi marta GitHub Actions'da ishga tushganda natijani albatta tekshiring
(workflow log'da xato bo'lmasligi, report.md to'g'ri chiqishi).
"""

import time


def fetch_daily_bars(symbol, lookback_days=180, retries=3):
    """
    Bitta ticker uchun oxirgi `lookback_days` kunlik D1 bar qaytaradi:
    [{'date','open','high','low','close'}, ...] — eskidan yangiga saralangan.
    """
    import yfinance as yf

    last_err = None
    for attempt in range(retries):
        try:
            df = yf.download(symbol, period=f"{lookback_days}d", interval="1d",
                              progress=False, auto_adjust=True)
            if df is None or df.empty:
                raise ValueError(f"{symbol}: bo'sh ma'lumot qaytdi")
            # yfinance ba'zan MultiIndex column qaytaradi (bir nechta ticker so'ralganda)
            if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
                df.columns = df.columns.get_level_values(0)

            bars = []
            for date, row in df.iterrows():
                bars.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                })
            bars.sort(key=lambda b: b['date'])
            return bars
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(2)
    raise RuntimeError(f"{symbol}: {retries} urinishdan keyin ham ma'lumot olinmadi: {last_err}")


def fetch_all(symbols, lookback_days=180):
    """Watchlist uchun barchasini oladi. Xato bo'lgan ticker'lar alohida ro'yxatda qaytadi."""
    data, errors = {}, {}
    for sym in symbols:
        try:
            data[sym] = fetch_daily_bars(sym, lookback_days)
        except Exception as e:
            errors[sym] = str(e)
    return data, errors
