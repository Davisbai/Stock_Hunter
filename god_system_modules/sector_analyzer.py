# god_system_modules/sector_analyzer.py

import yfinance as yf
import pandas as pd
import numpy as np
from rich.console import Console

console = Console()

# 使用具代表性的產業 ETF 或 權值龍頭股作為外部動能指標 (避免 Yahoo 指數 404 錯誤)
TAIWAN_SECTORS = {
    "半導體": "0052.TW",   # 富邦科技 (含大量半導體)
    "電腦及週邊": "2382.TW", # 廣達 (AI 伺服器龍頭)
    "電子零組件": "2308.TW", # 台達電
    "電子通路": "3702.TW",   # 大聯大
    "通信網路": "2454.TW",   # 聯發科 (或選中華電)
    "金融保險": "0055.TW",   # 元大 MS 台灣金融
    "電機機械": "1504.TW",   # 東元
    "航運業": "2603.TW",     # 長榮
    "鋼鐵工業": "2002.TW",   # 中鋼
    "塑膠工業": "1301.TW",   # 台塑
    "生技醫療": "1760.TW",   # 寶齡爵林 (或相關指標)
    "汽車工業": "2207.TW",   # 和泰車
    "化學工業": "1722.TW",   # 台肥
    "水泥工業": "1101.TW",   # 台泥
    "紡織纖維": "1402.TW",   # 遠東新
    "造紙工業": "1904.TW",   # 正隆
    "橡膠工業": "2105.TW",   # 正新
    "玻璃陶瓷": "1802.TW",   # 台玻
    "觀光事業": "2707.TW",   # 晶華
    "其餘電子": "2317.TW"    # 鴻海
}

class SectorAnalyzer:
    def __init__(self, benchmark="^TWII"):
        self.benchmark = benchmark
        self.sector_data = {}
        self.ranking_df = pd.DataFrame()

    def fetch_sector_momentum(self, period="6mo"):
        """計算各產業的 Net% (5日與20日動能) 與 RS 排名"""
        console.print("[dim]📊 正在分析動態類股輪動與起漲跡象...[/dim]")
        
        # 獲取基準位 (大盤)
        b_data = yf.download(self.benchmark, period=period, progress=False, auto_adjust=True)
        if b_data.empty: return pd.DataFrame()
        if isinstance(b_data.columns, pd.MultiIndex): b_data.columns = b_data.columns.get_level_values(0)
        
        b_ret_20 = b_data['Close'].pct_change().rolling(20).sum()
        b_ret_5 = b_data['Close'].pct_change().rolling(5).sum()

        results = []
        for name, sym in TAIWAN_SECTORS.items():
            try:
                s_data = yf.download(sym, period=period, progress=False, auto_adjust=True)
                if s_data.empty: continue
                if isinstance(s_data.columns, pd.MultiIndex): s_data.columns = s_data.columns.get_level_values(0)
                
                # 計算動能
                current_price = s_data['Close'].iloc[-1]
                
                # 20日動能
                p_20 = s_data['Close'].iloc[-20] if len(s_data) >= 20 else s_data['Close'].iloc[0]
                net_20 = (current_price / p_20 - 1) * 100
                
                # 5日動能 (剛起步跡象)
                p_5 = s_data['Close'].iloc[-5] if len(s_data) >= 5 else s_data['Close'].iloc[0]
                net_5 = (current_price / p_5 - 1) * 100
                
                # 相對強弱 (RS) vs 大盤
                s_ret_20 = s_data['Close'].pct_change().rolling(20).sum()
                rs_score = (s_ret_20.iloc[-1] - b_ret_20.iloc[-1]) * 100
                
                # 起漲係數 (短期動能增速)
                acceleration = net_5 - (net_20 / 4) # 理想情況 5日應佔 20日的 1/4，若超出則代表正在加速
                
                # 簡單 Value% (均線乖離)
                ma120 = s_data['Close'].rolling(120).mean().iloc[-1]
                value_score = (current_price / ma120 - 1) * 100 if not pd.isna(ma120) else 0
                
                results.append({
                    "Industry": name,
                    "Symbol": sym,
                    "Net%": round(net_20, 2),
                    "Net5d%": round(net_5, 2),
                    "RS_Score": round(rs_score, 2),
                    "Acceleration": round(acceleration, 2),
                    "Value%": round(value_score, 2),
                    "Last_Price": round(current_price, 2)
                })
            except Exception as e:
                console.print(f"[warning]無法獲取 {name} ({sym}) 數據: {e}[/warning]")
        
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by="Net%", ascending=False).reset_index(drop=True)
            df['Rank'] = df.index + 1
            self.ranking_df = df
        return df

    def get_top_sectors(self, top_n=10):
        if self.ranking_df.empty: return []
        return self.ranking_df.head(top_n).to_dict('records')

    def identify_rising_stars(self, top_n=3):
        """識別起漲跡象：區分【超跌反彈】與【強勢噴發】"""
        if self.ranking_df.empty: return []
        
        # 共同條件：5日動能超越 20日的 1/4 (正在加速) 且 5日動能為正
        stars_df = self.ranking_df[
            (self.ranking_df['Net5d%'] > 0) & 
            (self.ranking_df['Acceleration'] > 0.3)
        ].copy()
        
        results = []
        for _, row in stars_df.iterrows():
            tag = "強勢高檔噴發" if row['Value%'] > 0 else "超跌低檔反彈"
            results.append({
                "Industry": row['Industry'],
                "Tag": tag,
                "Acceleration": row['Acceleration']
            })
            
        # 依照加速力道排序並取前 N 名
        results = sorted(results, key=lambda x: x['Acceleration'], reverse=True)
        return results[:top_n]
