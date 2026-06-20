"""
halal_filter.py — DINAMIK halal skrining, Musaffa B2B API orqali.

NIMA UCHUN API, NIMA UCHUN O'ZIM HISOBLAMAYMAN:
AAOIFI skrining ikki qismdan iborat — (1) biznes faoliyat skrining
("bu kompaniya nima qiladi" — bank/qimor/alkogol emasligini bilish
matn/biznes tavsifini tushunishni talab qiladi, faqat OHLC narx
ma'lumotidan chiqarib bo'lmaydi) va (2) moliyaviy nisbat skrining
(qarz/market cap, foiz daromadi/jami daromad). Ikkalasini ham
ishonchli avtomatlashtirish uchun chinakam moliyaviy hisobotlar
(balance sheet, income statement breakdown) kerak — bu yfinance'ning
oddiy OHLC fetch'idan butunlay boshqa, ancha murakkab data manbai.
Bu masala diniy ahamiyatga ega bo'lgani uchun, men o'zim heuristika
yozib "taxminiy halol" deyishni TO'G'RI DEB HISOBLAMAYMAN — buning
o'rniga haqiqiy Shariah kengashi nazorat qiladigan xizmat (Musaffa)
API'siga ulanaman.

HOLAT: NOT TESTED. Bu kod Musaffa B2B API hujjatidagi namunaga
asoslangan, lekin ishlashi uchun sizning client_id/secret_key
kerak (https://musaffa.com/business yoki shunga o'xshash orqali
ro'yxatdan o'tib olinadi — bepul/pullik shartlarini o'zingiz
tekshiring). Men buni sinay olmadim, chunki API kalitiga ega emasman
va musaffa.com domeni sandbox tarmoq ruxsatida yo'q.
"""

import base64
import hashlib
import json
from datetime import datetime, timezone

import requests

MUSAFFA_URL = "https://platform.musaffa.com/b2b/api/v2/musaffa/stocks/screening-list"


def check_halal_status(symbols, client_id, secret_key):
    """
    symbols: ['AAPL', 'TSLA', ...]
    Qaytaradi: {symbol: {'status': 'COMPLIANT'|'NOT_COMPLIANT'|'DOUBTFUL'|'UNKNOWN',
                          'raw': <to'liq API javobi>}}
    """
    json_body = json.dumps({"stocks": symbols})
    now = datetime.now(timezone.utc)
    date_time_format = now.strftime("%Y%m%d%H%M%S")

    token_pre = secret_key + date_time_format + json_body
    token_sha512 = hashlib.sha512(token_pre.encode("utf8")).digest()
    token_base64 = base64.b64encode(token_sha512)

    headers = {
        "token": token_base64,
        "clientId": client_id,
        "time": date_time_format,
        "Content-Type": "application/json",
    }

    resp = requests.post(MUSAFFA_URL, data=json_body, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    result = {}
    for item in data:
        sym = item.get("stockName")
        status = item.get("shariahComplianceStatus", "UNKNOWN")
        result[sym] = {'status': status, 'raw': item}
    return result


def filter_watchlist(symbols, client_id, secret_key, strict=True):
    """
    strict=True: faqat 'COMPLIANT' o'tadi (eng kuchli filtr, sizning so'rovingiz).
    strict=False: 'COMPLIANT' va 'DOUBTFUL' ikkalasi ham o'tadi.
    """
    statuses = check_halal_status(symbols, client_id, secret_key)
    passed = []
    for sym in symbols:
        st = statuses.get(sym, {}).get('status', 'UNKNOWN')
        if st == 'COMPLIANT':
            passed.append(sym)
        elif not strict and st == 'DOUBTFUL':
            passed.append(sym)
    return passed, statuses


if __name__ == '__main__':
    import os
    import sys

    client_id = os.environ.get('MUSAFFA_CLIENT_ID')
    secret_key = os.environ.get('MUSAFFA_SECRET_KEY')
    if not client_id or not secret_key:
        print("XATO: MUSAFFA_CLIENT_ID va MUSAFFA_SECRET_KEY environment "
              "o'zgaruvchilarini sozlang (Musaffa B2B account kerak).")
        sys.exit(1)

    test_symbols = ['AAPL', 'MSFT', 'JPM', 'TSLA']
    passed, statuses = filter_watchlist(test_symbols, client_id, secret_key, strict=True)
    print("Holat:", statuses)
    print("O'tganlar (strict):", passed)
