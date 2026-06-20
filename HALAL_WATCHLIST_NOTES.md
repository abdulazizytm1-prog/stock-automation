# Halal Watchlist — Metodologiya va Eslatmalar

**Bu DINIY YOKI MOLIYAVIY MASLAHAT EMAS.** Men Shariah olimi ham, moliyaviy
maslahatchi ham emasman. Quyida — joriy, ommaviy AAOIFI-asoslangan
screening manbalaridan yig'ilgan, tekshirilishi mumkin bo'lgan ma'lumot.
Real pul bilan harakat qilishdan oldin albatta Zoya, Musaffa yoki Islamicly
orqali o'zingiz tasdiqlang — bu ro'yxat faqat SCANNING uchun boshlang'ich nuqta.

## Manbalar

- Musaffa Academy, "Top 15 Halal S&P 500 Stocks" — May 2026 snapshot, AAOIFI standart
- HalalSignalz, "76 Halal Stocks List" — Jun 4, 2026 snapshot
- Zoya Finance va Raseed Invest — "Top Rated/Best Halal Stocks 2026" maqolalari

## AAOIFI mezonlari (qisqacha)

1. Asosiy biznes faoliyati halal bo'lishi kerak (riba, alkogol, qimor, cho'chqa
   go'shti, an'anaviy sug'urta/bank — bularning hech biri yo'q)
2. Halol bo'lmagan daromad — jami daromadning 5% dan kam
3. Foiz keltiruvchi qarz — bozor capitalizatsiyasining 30% dan kam
4. Foiz keltiruvchi aktivlar (naqd pul va h.k.) — bozor capitalizatsiyasining 30% dan kam

Bu nisbatlar **har chorakda** qayta hisoblanadi — bugun halol bo'lgan stock
3 oydan keyin halol bo'lmasligi mumkin.

## Eski watchlist'dan ATAYLAB olib tashlangan tickerlar

| Ticker | Sabab |
|---|---|
| MSFT | Manbalar o'rtasida ZIDDIYAT bor — Musaffa "Not Halal" (gaming/reklama daromadi 5% chegaraga yaqin), HalalSignalz "Pass" deb ko'rsatadi. Konservativ tomonni tanladim — chiqarib tashladim. |
| GOOGL | Xuddi shu ziddiyat — Musaffa "Questionable/Doubtful", boshqa manbalar "Pass". Chiqarib tashlandi. |
| AMZN | Musaffa "Not Halal" (Amazon Lending — foizli kreditlash, reklama daromadi, yuqori naqd pul zaxirasi AAOIFI chegarasidan oshadi). Chiqarib tashlandi. |
| META | Manbalar ziddiyatli (ba'zilari "Pass" 3.2% qarz/1.06% foiz daromadi bilan, ba'zilari yo'q). Konservativ — chiqarib tashlandi, lekin chegara yaqin, xohlasangiz qaytarish mumkin. |
| JPM, GS | Barcha banklar — riba (foiz) asosida ishlaydi, biznes faoliyat skriningidan o'tmaydi. |
| UNH | Sog'liqni saqlash sug'urtasi — an'anaviy sug'urta gharar (noaniqlik) va foiz tufayli taqiqlangan. |
| SPY, QQQ | Bular ODDIY indeks ETF'lari — tarkibida banklar, sug'urta kompaniyalari va boshqa halol bo'lmagan kompaniyalar bor, shuning uchun ETF'ning o'zi halol emas, garchi ba'zi tarkibidagi aktivlar halol bo'lsa ham. |
| CAT | Tasdiqlanmagan — Cat Financial (kreditlash bo'limi) AAOIFI chegarasiga yaqinlashtirishi mumkin, ishonchli manbada topilmadi, ehtiyot bo'lib chiqarib tashlandi. |

## Halol ETF alternativasi (agar diversifikatsiya uchun ETF kerak bo'lsa)

SPY/QQQ o'rniga: **SPUS** (SP Funds S&P 500 Shariah Industry Exclusions ETF)
yoki **HLAL** (Wahed FTSE USA Shariah ETF) — bular maxsus Shariah-screened
indekslarni kuzatadi. Ular ham `engine.py` orqali xuddi alohida stock kabi
skanerlanishi mumkin, watchlist.txt'ga qo'shing.

## Sektor taqsimoti (59 ticker)

Tech/Software: 8, Semiconductors: 10, Cybersecurity: 4, Auto/Clean Energy: 4,
Healthcare&Biotech: 8, Big Pharma: 6, Fintech/Payments: 6, Energy: 3,
Consumer Disc: 4, Consumer Staples: 3, Industrials: 2, Networking: 1

**Diqqat:** Halol universe tabiatan tech/healthcare'ga og'ib ketadi (banklar,
sug'urta — butun sektorlar yo'q). Bu Test 3'dagi "faqat tech emas" talabini
to'liq qondira olmaydi — bu cheklov, halollik bilan aytaman, men uni
yashirmayman. Financials sektor umuman yo'q (V/MA fee-based bo'lgani uchun
istisno, lekin "Financials" GICS klassifikatsiyasida).

## Keyingi qadam

`scan.py` ushbu yangi watchlist bilan ishlaydi — kod o'zgarishsiz, faqat
`watchlist.txt` fayli yangilandi. Birinchi GitHub Actions ishga tushishida
barcha 59 ticker uchun yfinance fetch sinaladi.
