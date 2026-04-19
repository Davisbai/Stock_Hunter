# god_system_modules/sector_analyzer.py

import yfinance as yf
import pandas as pd
import numpy as np
from rich.console import Console

console = Console()

# 定義代表性產業指數 (Yahoo Finance 符號)
TAIWAN_SECTORS = {
    "半導體": "^TWSI",
    "電腦及週邊": "^TWCOI",
    "電子零組件": "^TWEOC",
    "電子通路": "^TWEDO",
    "通信網路": "^TWCEI",
    "金融保險": "^TWFI",
    "電機機械": "^TWEHI",
    "航運業": "^TWNI",
    "鋼鐵工業": "^TWBI",
    "塑膠工業": "^TWPI",
    "生技醫療": "^TWMBI",
    "汽車工業": "^TWAI",
    "化學工業": "^TWCI",
    "水泥工業": "^TWCPI",
    "紡織纖維": "^TWTI",
    "造紙工業": "^TWPI2",
    "橡膠工業": "^TWRMI",
    "玻璃陶瓷": "^TWGI",
    "觀光事業": "^TWOI",
    "其他電子": "^TWEOI"
}

class SectorAnalyzer:
    def __init__(self, benchmark="^TWII"):
        self.benchmark = benchmark
        self.sector_data = {}
        self.ranking_df = pd.DataFrame()

    def fetch_sector_momentum(self, period="6mo"):
        """計算各產業的 Net% (動能) 與 RS 排名"""
        console.print("[dim]📊 正在分析類股輪動動能...[/dim]")
        
        # 獲取基準位 (大盤)
        b_data = yf.download(self.benchmark, period=period, progress=False, auto_adjust=True)
        if b_data.empty: return pd.DataFrame()
        if isinstance(b_data.columns, pd.MultiIndex): b_data.columns = b_data.columns.get_level_values(0)
        
        b_ret = b_data['Close'].pct_change().rolling(20).sum() # 20日累積報酬

        results = []
        for name, sym in TAIWAN_SECTORS.items():
            try:
                s_data = yf.download(sym, period=period, progress=False, auto_adjust=True)
                if s_data.empty: continue
                if isinstance(s_data.columns, pd.MultiIndex): s_data.columns = s_data.columns.get_level_values(0)
                
                # 計算 Net% (20日報酬)
                current_price = s_data['Close'].iloc[-1]
                prev_price = s_data['Close'].iloc[-20] if len(s_data) >= 20 else s_data['Close'].iloc[0]
                net_momentum = (current_price / prev_price - 1) * 100
                
                # 相對強弱 (RS) vs 大盤
                s_ret = s_data['Close'].pct_change().rolling(20).sum()
                rs_score = (s_ret.iloc[-1] - b_ret.iloc[-1]) * 100
                
                # 簡單 Value% (目前價格 vs 120日均線的乖離，負值代表低估)
                ma120 = s_data['Close'].rolling(120).mean().iloc[-1]
                value_score = (current_price / ma120 - 1) * 100 if not pd.isna(ma120) else 0
                
                results.append({
                    "Industry": name,
                    "Symbol": sym,
                    "Net%": round(net_momentum, 2),
                    "RS_Score": round(rs_score, 2),
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

    def get_top_sectors(self, top_n=3):
        if self.ranking_df.empty: return []
        return self.ranking_df.head(top_n).to_dict('records')
