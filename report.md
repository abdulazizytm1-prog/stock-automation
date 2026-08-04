# DAILY TRADING RESEARCH REPORT

**Date:** 2026-08-04

> Bu BOT TRADE QILMAYDI. Faqat kuzatadi va yozib boradi. OB = Research Candidate (PF=1.03 costsiz, cost bilan FAIL). FVG = DISABLED (3 testda 0 trade).

- Halal filter mode: static_watchlist
- Scanner version: 2026.06.20
- Market data status: fresh
- Final scanned watchlist: AAPL, NVDA, AVGO, QCOM, AMD, TSM, LLY, JNJ, MRK, XOM, CVX, PG, KO, HD, V, MA, TSLA
- Fetch success: 17/17
- Fetch errors: 0
- Failure rate: 0.0%

## Signals found: 2

### 1) AMD
- Setup: OB wick touch (Research Candidate)
- Trend: Bearish
- Reason: price returned to fresh bearish OB
- Entry: next day open
- SL: zone high +/- 0.3%
- TP: 2R
- Status: pending
- Zone status: fresh -> touched
- Grade: C (discount=False, displacement=False)
- Note: PF=1.03 (costsiz), cost bilan FAIL - faqat kuzatish uchun, trade tavsiyasi emas

### 2) XOM
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
- No valid setup
- Reason: trend filter failed (RANGE)

### 4) NVDA
- No valid setup
- Reason: trend filter failed (RANGE)

### 5) AVGO
- No valid setup
- Reason: trend filter failed (RANGE)

### 6) QCOM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 7) TSM
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 8) LLY
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 9) JNJ
- No valid setup
- Reason: trend filter failed (RANGE)

### 10) MRK
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 11) CVX
- No valid setup
- Reason: trend filter failed (RANGE)

### 12) PG
- No valid setup
- Reason: trend filter failed (RANGE)

### 13) KO
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 14) HD
- No valid setup
- Reason: trend filter failed (RANGE)

### 15) V
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

### 16) MA
- No valid setup
- Reason: trend filter failed (RANGE)

### 17) TSLA
- No trade
- Reason: latest candle fresh OB zonega birinchi valid retest qilmadi

---

## Bugungi journal hodisalari
- Yangi pending signal: 2
- Tasdiqlangan (open position bo'ldi): 0
- Yopilgan trade: 1
- Rejected signal: 0
- Intrabar ambiguity count: 0
- Closed AAPL: stop, R=-1.00

---

## Rolling Statistika (jami yopilgan trade'lar)
- Jami trade: 18
- Win rate: 44.4%
- Avg R: 0.26
- Total R: 4.69
- PF: 1.53
- Eng yaxshi tickerlar: V (+3.22R), HD (+2.00R), PG (+2.00R)
- Eng yomon tickerlar: AAPL (-2.00R), TSLA (-1.00R), CVX (-1.00R)

### Grade Breakdown
| Grade | n | Win Rate | Total R | PF |
|---|---|---|---|---|
| A | 0 | n/a | 0.00 | n/a |
| B | 0 | n/a | 0.00 | n/a |
| C | 18 | 44.4% | +4.69R | 1.53 |

---

## Hypothesis holati
| Hypothesis | Status | Dalil |
|---|---|---|
| OB wick-touch | RESEARCH CANDIDATE | n=427, PF=1.03 costsiz, cost bilan FAIL |
| FVG | DISABLED | 3 testda (n=3, n=26, n=427) 0 trade |

---

# Edge Validation

*(Based on 18 closed trade(s))*

## Grade Performance

| Grade | Trades | Wins | Losses | Win Rate |
|---|---|---|---|---|
| A | 0 | 0 | 0 | n/a |
| B | 0 | 0 | 0 | n/a |
| C | 18 | 8 | 10 | 44.4% |

## Symbol Performance

*Only symbols with ≥3 completed trades*

No symbol has reached the 3-trade minimum yet.

## Outcome Distribution

| Outcome | Count |
|---|---|
| TARGET_HIT | 6 |
| STOP_LOSS | 8 |
| Other | 4 |

## Holding Statistics

- Average Holding Days: 6.6
- Median Holding Days: 3.0
