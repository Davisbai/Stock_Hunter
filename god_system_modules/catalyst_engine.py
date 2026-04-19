# god_system_modules/catalyst_engine.py

import yfinance as yf
from rich.console import Console

console = Console()

# 知名的 BBU 概念股起始庫 (用於加速比對)
KNOWN_BBU_TICKERS = ["6781.TW", "3211.TW", "4931.TW", "2301.TW", "2308.TW", "1504.TW", "3003.TW", "6187.TW"]

class CatalystEngine:
    def __init__(self):
        self.theme_keywords = {
            "BBU 備援電力": ["Battery", "Power Supply", "UPS", "BBU", "備援電池", "電池組", "電源模組"],
            "AI 伺服器供應鏈": ["AI", "Server", "HPC", "GPU", "伺服器", "散熱", "組裝"],
            "先進封裝與設備": ["Packaging", "CoWoS", "Equipment", "封裝", "半導體設備"],
            "低軌衛星": ["Satellite", "Low Earth Orbit", "衛星", "航太"]
        }

    def discover_themes(self, ticker, name, info=None):
        """
        動態偵測個股所屬的熱門題材
        """
        results = []
        
        # 1. 優先匹配已知清單
        if ticker in KNOWN_BBU_TICKERS:
            results.append("BBU 核心概念股")
            
        # 2. 從 yfinance info 中動態探測 (若有提供 info)
        if info:
            summary = str(info.get('longBusinessSummary', "")).lower()
            industry = str(info.get('industry', "")).lower()
            combined_text = summary + " " + industry
            
            for theme, keywords in self.theme_keywords.items():
                if any(kw.lower() in combined_text for kw in keywords):
                    if theme not in results:
                        results.append(theme)
        
        if not results:
            results.append("技術面突破標的")
            
        return " | ".join(results[:2]) # 最多回傳兩個標籤

    def get_stock_catalyst_async(self, ticker_list):
        """
        批次獲取多個標的的催化劑資訊 (示範用，實務可加入多線程)
        """
        catalyst_map = {}
        for ticker in ticker_list:
            try:
                t_obj = yf.Ticker(ticker)
                # 僅在必要時獲取 info 以節省時間
                info = t_obj.info 
                catalyst_map[ticker] = self.discover_themes(ticker, "", info)
            except:
                catalyst_map[ticker] = "市場熱門動能股"
        return catalyst_map
