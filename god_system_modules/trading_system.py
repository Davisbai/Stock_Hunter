# god_system_modules/trading_system.py

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from .config import MARKET_TICKER, DEFAULT_START_DATE
from .indicators import calculate_base_indicators, calculate_advanced_signals

class TaiwanStockTradingSystem:
    def __init__(self, tickers, start_date=DEFAULT_START_DATE):
        self.tickers = tickers
        self.start_date = start_date
        self.market_ticker = MARKET_TICKER
        self.market_data = None
        
    def fetch_market_data(self):
        print("\n正在獲取大盤(加權指數)數據...")
        self.market_data = yf.download(self.market_ticker, start=self.start_date, progress=False, auto_adjust=True)
        if isinstance(self.market_data.columns, pd.MultiIndex):
            self.market_data.columns = self.market_data.columns.get_level_values(0)
        self.market_data.index = pd.to_datetime(self.market_data.index).tz_localize(None).normalize()
        self.market_data['Market_MA20'] = self.market_data['Close'].rolling(window=20).mean()
        self.market_data['Market_OK'] = self.market_data['Close'] > self.market_data['Market_MA20']

    def fetch_real_chip_data(self, df, ticker):
        code = ticker.replace('.TW', '').replace('.TWO', '')
        start_date_str = df.index[0].strftime('%Y-%m-%d')
        df['Foreign_Buy'] = 0.0
        df['Trust_Buy'] = 0.0
        
        try:
            url_inst = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={code}&start_date={start_date_str}"
            res_inst = requests.get(url_inst, timeout=10).json()
            if res_inst.get('msg') == 'success' and res_inst.get('data'):
                df_inst = pd.DataFrame(res_inst['data'])
                is_foreign = df_inst['name'].str.contains('外資', na=False)
                df_foreign = df_inst[is_foreign]
                if not df_foreign.empty:
                    foreign_buy = df_foreign.groupby('date').apply(lambda x: x['buy'].sum() - x['sell'].sum())
                    foreign_buy.index = pd.to_datetime(foreign_buy.index).normalize()
                    df['Foreign_Buy'] = foreign_buy / 1000
                is_trust = df_inst['name'] == '投信'
                df_trust = df_inst[is_trust]
                if not df_trust.empty:
                    trust_buy = df_trust.groupby('date').apply(lambda x: x['buy'].sum() - x['sell'].sum())
                    trust_buy.index = pd.to_datetime(trust_buy.index).normalize()
                    df['Trust_Buy'] = trust_buy / 1000
            time.sleep(0.5)
        except: pass
        df['Foreign_Buy'] = df['Foreign_Buy'].fillna(0)
        df['Trust_Buy'] = df['Trust_Buy'].fillna(0)
        return df

    def process_stock(self, ticker):
        df = yf.download(ticker, start=self.start_date, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            
        if self.market_data is None:
            self.fetch_market_data()

        df = self.fetch_real_chip_data(df, ticker)
        df = calculate_base_indicators(df)
        
        # 籌碼連三紅判斷
        df['Inst_Consecutive'] = ((df['Foreign_Buy'] > 0) | (df['Trust_Buy'] > 0)).rolling(window=3).sum() >= 2
        
        df = df.join(self.market_data[['Close', 'Market_OK']], how='left', rsuffix='_Mkt').ffill()
        df['Market_OK'] = df['Market_OK'].fillna(False)
        df = calculate_advanced_signals(df)

        # 核心：計算 Independent_Alpha
        df['RS_Line'] = df['Close'] / (df['Close_Mkt'] + 1e-9)
        df['RS_Slope'] = df['RS_Line'].pct_change(5) 
        stock_ma20_up = df['MA20'] > df['MA20'].shift(1)
        df['Independent_Alpha'] = (~df['Market_OK']) & (df['Close'] > df['MA20']) & stock_ma20_up & (df['RS_Slope'] > 0)

        # 評分與訊號
        df['Raw_Score'] = 0
        df.loc[df['Close'] > df['MA20'], 'Raw_Score'] += 25
        df.loc[df['MACD'] > df['Signal'], 'Raw_Score'] += 25
        df.loc[df['K'] > df['D'], 'Raw_Score'] += 10
        df.loc[df['Inst_Consecutive'], 'Raw_Score'] += 20
        df.loc[df['Price_Breakout'] & df['Volume_Surge'], 'Raw_Score'] += 15
        df.loc[df['Price_Breakout'] & df['Volume_Surge'] & df['MA_Squeeze'].shift(1), 'Raw_Score'] += 10
        df.loc[df['Early_Start'], 'Raw_Score'] += 5
        df.loc[df['Pro_Bottom_Breakout'], 'Raw_Score'] += 35
        df.loc[df['Ambush_Setup'], 'Raw_Score'] += 25

        df['Score'] = df['Raw_Score']
        df.loc[(~df['Market_OK']) & (~df['Independent_Alpha']), 'Score'] = df['Raw_Score'] * 0.6
        df['Buy_Signal'] = (df['Score'] >= 60)
        
        macd_death_cross = (df['MACD'] < df['Signal']) & (df['MACD'].shift(1) >= df['Signal'].shift(1))
        break_ma20 = df['Close'] < (df['MA20'] * 0.98)
        df['Sell_Signal'] = macd_death_cross | break_ma20 | df['Top_Divergence'] | df['Overextended_MA5'] | df['Hit_Resistance']
        df.loc[df['Buy_Signal'], 'Sell_Signal'] = False 

        df['Position'] = np.nan
        df.loc[df['Buy_Signal'], 'Position'] = 1
        df.loc[df['Sell_Signal'], 'Position'] = 0
        df['Position'] = df['Position'].ffill().fillna(0)
        df['Trade_Action'] = df['Position'].diff()
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']
        return df

    def run_analysis(self):
        self.fetch_market_data()
        results_summary, daily_alerts, trade_logs = {}, {}, {}
        for ticker in self.tickers:
            df = self.process_stock(ticker)
            if df is None: continue
            trades = df[df['Strategy_Returns'] != 0]['Strategy_Returns']
            win_rate = (trades > 0).sum() / len(trades) if len(trades) > 0 else 0
            actions = df[df['Trade_Action'] != 0].dropna(subset=['Trade_Action'])
            trade_logs[ticker] = [
                f"{date.strftime('%Y-%m-%d')} | {'🟢 買進' if row['Trade_Action'] == 1 else '🔴 賣出'} | 價格: {row['Close']:.2f} | 觸發評分: {int(row['Score'])}"
                for date, row in actions.iterrows()
            ]
            results_summary[ticker] = {
                "總交易天數": len(trades),
                "勝率 (%)": round(win_rate * 100, 2),
                "策略累積報酬 (%)": round(((1 + df['Strategy_Returns']).prod() - 1) * 100, 2)
            }
            last_day = df.iloc[-1]
            daily_alerts[ticker] = {
                "日期": df.index[-1].strftime("%Y-%m-%d"),
                "收盤價": round(float(last_day['Close']), 2),
                "月線價": round(float(last_day['MA20']), 2),
                "大盤安全": bool(last_day['Market_OK']),
                "今日評分": int(last_day['Score']),
                "個股原始評分": int(last_day['Raw_Score']),
                "是否觸發賣出": bool(last_day['Sell_Signal']),
                "獨立行情": bool(last_day['Independent_Alpha']),
                "RS斜率": round(float(last_day['RS_Slope']), 4),
                "專業起漲": bool(last_day.get('Pro_Bottom_Breakout', False)),
                "縮量埋伏": bool(last_day.get('Ambush_Setup', False)),
                "高檔背離": bool(last_day.get('Top_Divergence', False)),
                "乖離過大": bool(last_day.get('Overextended_MA5', False))
            }
        return results_summary, daily_alerts, trade_logs
