# god_system_modules/scanners.py

import requests
import re
import time
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd
from .config import STOCK_MAP

try:
    import twstock
except ImportError:
    pass

class YahooMarketScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.scan_limit = 10

    def get_chinese_name(self, code):
        check_code = f"{code}.TW"
        if check_code in STOCK_MAP: return STOCK_MAP[check_code]
        try:
            if 'twstock' in globals() and code in twstock.codes:
                return twstock.codes[code].name
        except: pass
        return code

    def get_foreign_buying(self, code):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': f'https://fubon-ebrokerdj.fbs.com.tw/z/zc/zcl/zcl.djhtm?a={code}'
            }
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zcl/zcl.djhtm?a={code}"
            
            res = self.session.get(url, headers=headers, timeout=10)
            res.encoding = 'cp950'
            dfs = pd.read_html(StringIO(res.text))
            
            for df in dfs:
                if df.shape[1] < 2: continue
                combined_text = "".join([str(x) for x in df.values.flatten()])
                if '外資' in combined_text and '買賣超' in combined_text:
                    for i in range(len(df)):
                        cell_date = str(df.iloc[i, 0])
                        if '/' in cell_date and len(cell_date) <= 10:
                            raw_val = str(df.iloc[i, 1])
                            clean_val = re.sub(r'[^-0-9]', '', raw_val)
                            if clean_val: return int(clean_val), cell_date
            return 0, "無數據"
        except: return 0, "錯誤"

    def fetch_top_gainers(self):
        url = "https://tw.stock.yahoo.com/rank/change-up?exchange=TAI"
        try:
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/quote/\d{4}\.TW$'))
            candidates, seen = [], set()
            for link in links:
                match = re.search(r'/quote/(\d{4})\.TW', link.get('href'))
                if match:
                    code = match.group(1)
                    if code not in seen:
                        seen.add(code)
                        candidates.append({'code': code, 'name': self.get_chinese_name(code)})
                if len(candidates) >= self.scan_limit: break
            return candidates
        except: return []

    def scan(self):
        candidates = self.fetch_top_gainers()
        qualified = []
        print(f"\n🔍 --- 掃描熱門股 (前 {len(candidates)} 名) ---")
        for item in candidates:
            code, name = item['code'], item['name']
            fb, date = self.get_foreign_buying(code)
            if fb > 0:
                print(f"{code} {name:<4}: 外資買 {fb:>5} 張 -> ✅")
                qualified.append(item)
                check_code = f"{code}.TW"
                if check_code not in STOCK_MAP: STOCK_MAP[check_code] = name
            else:
                print(f"{code} {name:<4}: 外資賣超或無資料 -> ❌")
            time.sleep(0.1)
        return qualified
