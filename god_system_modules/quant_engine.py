# god_system_modules/quant_engine.py

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from rich.console import Console

console = Console()

class MarketContext:
    """用於儲存總體經濟與市場體質狀態"""
    def __init__(self):
        self.is_bull_market = False
        self.ma_status = ""
        self.usd_trend = "中立"
        self.gold_trend = "中立"
        self.oil_trend = "中立"
        self.macro_score = 0
        self.last_updated = ""

    def __repr__(self):
        return f"<MarketContext(Bull={self.is_bull_market}, Score={self.macro_score})>"

class AdvancedQuantEngine:
    def __init__(self, ticker="2330.TW", target_vol=0.15):
        self.ticker = ticker
        self.target_vol = target_vol
        self.data = pd.DataFrame()
        self.gmm_model = None
        self.meta_classifier = None
        
    def fetch_data(self, period="3y"):
        console.print(f"[dim]📥 正在獲取 {self.ticker} 的市場數據...[/dim]")
        df = yf.download(self.ticker, period=period, progress=False)
        if df.empty: return False
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df['Return'] = df['Close'].pct_change()
        df['Volatility_20'] = df['Return'].rolling(window=20).std() * np.sqrt(252)
        df['Volatility_50'] = df['Return'].rolling(window=50).std() * np.sqrt(252)
        df['Momentum_10'] = df['Close'] / df['Close'].shift(10) - 1
        df['Momentum_20'] = df['Close'] / df['Close'].shift(20) - 1
        self.data = df.dropna().copy()
        return True

    def fetch_macro_data(self):
        """獲取總體經濟指標 (美元, 黃金, 原油)"""
        console.print("[dim]🌍 正在獲取全球總體經濟指標...[/dim]")
        macro_symbols = {
            "USD": "DX-Y.NYB",
            "Gold": "GC=F",
            "Oil": "CL=F"
        }
        
        context = MarketContext()
        context.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        try:
            for name, sym in macro_symbols.items():
                m_data = yf.download(sym, period="3mo", progress=False, auto_adjust=True)
                if m_data.empty: continue
                if isinstance(m_data.columns, pd.MultiIndex): m_data.columns = m_data.columns.get_level_values(0)
                
                # 簡單趨勢判斷: 目前價格 vs 20日均線
                current_price = m_data['Close'].iloc[-1]
                ma20 = m_data['Close'].rolling(20).mean().iloc[-1]
                trend = "強勢" if current_price > ma20 else "弱勢"
                
                if name == "USD": context.usd_trend = trend
                elif name == "Gold": context.gold_trend = trend
                elif name == "Oil": context.oil_trend = trend
            
            # 台股大盤體質檢測 (^TWII)
            twii = yf.download("^TWII", period="1y", progress=False, auto_adjust=True)
            if not twii.empty:
                if isinstance(twii.columns, pd.MultiIndex): twii.columns = twii.columns.get_level_values(0)
                close = twii['Close'].iloc[-1]
                ma20 = twii['Close'].rolling(20).mean().iloc[-1]
                ma60 = twii['Close'].rolling(60).mean().iloc[-1]
                ma240 = twii['Close'].rolling(240).mean().iloc[-1]
                
                context.is_bull_market = bool(close > ma60)
                if close > ma20 > ma60 > ma240:
                    context.ma_status = "多頭排列 (強勢)"
                    context.macro_score = 100
                elif close > ma60:
                    context.ma_status = "多頭回檔 / 區間"
                    context.macro_score = 70
                else:
                    context.ma_status = "空頭趨勢 / 走弱"
                    context.macro_score = 30
                    
                # 美元負相關懲罰: 美元強勢對台股不利
                if context.usd_trend == "強勢":
                    context.macro_score -= 15
                    
            return context
        except Exception as e:
            console.print(f"[bold red]❌ 獲取總經數據失敗: {e}[/bold red]")
            return context

    def detect_market_regime(self):
        if len(self.data) < 100: return
        features = self.data[['Return', 'Volatility_20']].dropna()
        self.gmm_model = GaussianMixture(n_components=3, covariance_type="full", random_state=42)
        self.gmm_model.fit(features)
        self.data['Regime'] = self.gmm_model.predict(features)
        
    def apply_triple_barrier(self, pt_multiplier=1.5, sl_multiplier=1.0, t_max=10):
        df = self.data.copy()
        events = []
        for i in range(len(df) - t_max):
            start_price = df['Close'].iloc[i]
            daily_vol = df['Volatility_20'].iloc[i] / np.sqrt(252)
            if pd.isna(daily_vol) or daily_vol == 0: continue
            upper = start_price * (1 + pt_multiplier * daily_vol * np.sqrt(t_max))
            lower = start_price * (1 - sl_multiplier * daily_vol * np.sqrt(t_max))
            hit_upper = hit_lower = False
            for j in range(1, t_max + 1):
                future = df['Close'].iloc[i + j]
                if future >= upper:
                    hit_upper = True
                    events.append({'date': df.index[i], 'label': 1})
                    break
                elif future <= lower:
                    hit_lower = True
                    events.append({'date': df.index[i], 'label': 0})
                    break
            if not hit_upper and not hit_lower:
                label = 1 if df['Close'].iloc[i + t_max] > start_price else 0
                events.append({'date': df.index[i], 'label': label})
        events_df = pd.DataFrame(events).set_index('date')
        self.data = self.data.join(events_df['label'], how='left').fillna(0)
        
    def train_meta_labeling_model(self):
        self.data['SMA_20'] = self.data['Close'].rolling(window=20).mean()
        trade_days = self.data[self.data['Close'] > self.data['SMA_20']].dropna()
        if len(trade_days) < 50: return False
        features = ['Volatility_20', 'Volatility_50', 'Momentum_10', 'Momentum_20', 'Regime']
        X, y = trade_days[features], trade_days['label']
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.meta_classifier = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.meta_classifier.fit(X_train, y_train)
        return True
        
    def calculate_position_size(self, current_vol):
        if pd.isna(current_vol) or current_vol == 0: return 0.0
        return round(min(self.target_vol / current_vol, 1.0), 4)

class ShioajiMockAPI:
    def __init__(self):
        self.connected = False
    def connect(self):
        console.print("[dim]🔄 正在與券商伺服器 (Shioaji) 建立加密連線...[/dim]")
        self.connected = True
        return True
    def place_order(self, ticker, action, price, qty):
        if not self.connected: return
        console.print(f"[bold green]✅ 訂單已送出:[/bold green] {action} {ticker} | 數量: {qty} | 價格: {price}")
