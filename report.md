# DAILY TRADING RESEARCH REPORT

**Date:** 2026-08-26

> Bu BOT TRADE QILMAYDI. Faqat kuzatadi va yozib boradi. OB = Research Candidate (PF=1.03 costsiz, cost bilan FAIL). FVG = DISABLED (3 testda 0 trade).

- Halal filter mode: static_watchlist
- Scanner version: 2026.06.20
- Market data status: no fresh market data / market holiday
- Final scanned watchlist: AAPL, NVDA, AVGO, QCOM, AMD, TSM, LLY, JNJ, MRK, XOM, CVX, PG, KO, HD, V, MA, TSLA
- Fetch success: 17/17
- Fetch errors: 0
- Failure rate: 0.0%

## Signals found: 2

### 1) LLY
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

### 2) TSLA
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

### 3) AAPL
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 4) NVDA
- No valid setup
- Reason: trend filter failed (RANGE)

### 5) AVGO
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 6) QCOM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 7) AMD
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 8) TSM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 9) JNJ
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 10) MRK
- No valid setup
- Reason: trend filter failed (RANGE)

### 11) XOM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 12) CVX
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 13) PG
- No valid setup
- Reason: trend filter failed (RANGE)

### 14) KO
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 15) HD
- No valid setup
- Reason: trend filter failed (RANGE)

### 16) V
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 17) MA
- No valid setup
- Reason: trend filter failed (RANGE)

---

## Bugungi journal hodisalari
- Yangi pending signal: 2
- Tasdiqlangan (open position bo'ldi): 0
- Yopilgan trade: 1
- Rejected signal: 0
- Intrabar ambiguity count: 0
- Closed HD: time_stop, R=0.12

---

## Rolling Statistika (jami yopilgan trade'lar)
- Jami trade: 28
- Win rate: 42.9%
- Avg R: 0.10
- Total R: 2.92
- PF: 1.22
- Eng yaxshi tickerlar: V (+3.22R), PG (+2.00R), QCOM (+2.00R)
- Eng yomon tickerlar: AAPL (-2.00R), CVX (-1.80R), TSLA (-1.00R)

### Grade Breakdown
| Grade | n | Win Rate | Total R | PF |
|---|---|---|---|---|
| A | 0 | n/a | 0.00 | n/a |
| B | 0 | n/a | 0.00 | n/a |
| C | 28 | 42.9% | +2.92R | 1.22 |

---

## Hypothesis holati
| Hypothesis | Status | Dalil |
|---|---|---|
| OB wick-touch | RESEARCH CANDIDATE | n=427, PF=1.03 costsiz, cost bilan FAIL |
| FVG | DISABLED | 3 testda (n=3, n=26, n=427) 0 trade |

---

# Edge Validation

*(Based on 28 closed trade(s))*

## Grade Performance

| Grade | Trades | Wins | Losses | Win Rate |
|---|---|---|---|---|
| A | 0 | 0 | 0 | n/a |
| B | 0 | 0 | 0 | n/a |
| C | 28 | 12 | 16 | 42.9% |

## Symbol Performance

*Only symbols with ≥3 completed trades*

| Ticker | Trades | Win Rate |
|---|---|---|
| AVGO | 3 | 33.3% |
| HD | 3 | 66.7% |
| MRK | 3 | 33.3% |
| TSM | 3 | 33.3% |

## Outcome Distribution

| Outcome | Count |
|---|---|
| TARGET_HIT | 7 |
| STOP_LOSS | 11 |
| Other | 10 |

## Holding Statistics

- Average Holding Days: 8.8
- Median Holding Days: 3.0
