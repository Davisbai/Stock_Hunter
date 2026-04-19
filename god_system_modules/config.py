# god_system_modules/config.py

import os

# 📂 本地資料庫設定
WATCHLIST_FILE = "long_term_watchlist.json"

# 📱 LINE 推播設定 (優先從環境變數讀取，次之則使用本地數值)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '/2ubptsBfLObWol5cufqQGqplAv1aNCg/1fsfhKgTf3DZZzyqrjyPh2qhc1C9IGbGxMbUUe0RX3epQsAlcew7sqCrtFGedCpL3UK3FGtsjjxkgKXtT/PuPQWr0hRyP3h6uc4VmmoX5p3jWzWKl4Z3wdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LINE_CHANNEL_SECRET')
LINE_USER_ID = os.getenv('LINE_USER_ID', 'U98822ea2b4b6b353b3dade3ea64b5360')

# 全域的股票代碼對應表
STOCK_MAP = {
    "2303.TW": "聯電", "3481.TW": "群創", "2344.TW": "華邦電",
    "2408.TW": "南亞科", "2603.TW": "長榮", "2609.TW": "陽明",
    "2308.TW": "台達電", "2313.TW": "華通", "6770.TW": "力積電",
    "3231.TW": "緯創", "2014.TW": "中鴻"
}

# 市場相關設定
MARKET_TICKER = "^TWII"
DEFAULT_START_DATE = "2023-01-01"
BACKTEST_START_DATE = "2025-09-01"
