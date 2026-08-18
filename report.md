# DAILY TRADING RESEARCH REPORT

**Date:** 2026-08-18

> Bu BOT TRADE QILMAYDI. Faqat kuzatadi va yozib boradi. OB = Research Candidate (PF=1.03 costsiz, cost bilan FAIL). FVG = DISABLED (3 testda 0 trade).

- Halal filter mode: static_watchlist
- Scanner version: 2026.06.20
- Market data status: fresh
- Final scanned watchlist: AAPL, NVDA, AVGO, QCOM, AMD, TSM, LLY, JNJ, MRK, XOM, CVX, PG, KO, HD, V, MA, TSLA
- Fetch success: 17/17
- Fetch errors: 0
- Failure rate: 0.0%

## Signals found: 1

### 1) NVDA
- Setup: OB wick touch (Research Candidate)
- Trend: Bullish
- Reason: price returned to fresh bullish OB
- Entry: next day open
- SL: zone low +/- 0.3%
- TP: 2R
- Status: pending
- Zone status: fresh -> touched
- Grade: C (discount=False, displacement=False)
- Note: PF=1.03 (costsiz), cost bilan FAIL - faqat kuzatish uchun, trade tavsiyasi emas

### 2) AAPL
- No valid setup
- Reason: trend filter failed (RANGE)

### 3) AVGO
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 4) QCOM
- No valid setup
- Reason: trend filter failed (RANGE)

### 5) AMD
- No valid setup
- Reason: trend filter failed (RANGE)

### 6) TSM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 7) LLY
- No valid setup
- Reason: trend filter failed (RANGE)

### 8) JNJ
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 9) MRK
- No valid setup
- Reason: trend filter failed (RANGE)

### 10) XOM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 11) CVX
- No valid setup
- Reason: trend filter failed (RANGE)

### 12) PG
- No valid setup
- Reason: trend filter failed (RANGE)

### 13) KO
- No valid setup
- Reason: trend filter failed (RANGE)

### 14) HD
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 15) V
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 16) MA
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 17) TSLA
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

---

## Bugungi journal hodisalari
- Yangi pending signal: 1
- Tasdiqlangan (open position bo'ldi): 1
- Yopilgan trade: 2
- Rejected signal: 0
- Intrabar ambiguity count: 0
- Closed AVGO: stop, R=-1.00
- Closed TSM: stop, R=-1.00

---

## Rolling Statistika (jami yopilgan trade'lar)
- Jami trade: 26
- Win rate: 42.3%
- Avg R: 0.15
- Total R: 3.80
- PF: 1.31
- Eng yaxshi tickerlar: V (+3.22R), PG (+2.00R), QCOM (+2.00R)
- Eng yomon tickerlar: AAPL (-2.00R), CVX (-1.80R), TSLA (-1.00R)

### Grade Breakdown
| Grade | n | Win Rate | Total R | PF |
|---|---|---|---|---|
| A | 0 | n/a | 0.00 | n/a |
| B | 0 | n/a | 0.00 | n/a |
| C | 26 | 42.3% | +3.80R | 1.31 |

---

## Hypothesis holati
| Hypothesis | Status | Dalil |
|---|---|---|
| OB wick-touch | RESEARCH CANDIDATE | n=427, PF=1.03 costsiz, cost bilan FAIL |
| FVG | DISABLED | 3 testda (n=3, n=26, n=427) 0 trade |

---

# Edge Validation

*(Based on 26 closed trade(s))*

## Grade Performance

| Grade | Trades | Wins | Losses | Win Rate |
|---|---|---|---|---|
| A | 0 | 0 | 0 | n/a |
| B | 0 | 0 | 0 | n/a |
| C | 26 | 11 | 15 | 42.3% |

## Symbol Performance

*Only symbols with ≥3 completed trades*

| Ticker | Trades | Win Rate |
|---|---|---|
| AVGO | 3 | 33.3% |
| MRK | 3 | 33.3% |
| TSM | 3 | 33.3% |

## Outcome Distribution

| Outcome | Count |
|---|---|
| TARGET_HIT | 7 |
| STOP_LOSS | 10 |
| Other | 9 |

## Holding Statistics

- Average Holding Days: 8.5
- Median Holding Days: 3.0
