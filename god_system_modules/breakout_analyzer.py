# god_system_modules/breakout_analyzer.py

import pandas as pd
import numpy as np

class BreakoutAnalyzer:
    def __init__(self, threshold_vol_ratio=1.5):
        self.threshold_vol_ratio = threshold_vol_ratio

    def analyze_stock(self, ticker, df):
        if df is None or len(df) < 20:
            return None

        last_day = df.iloc[-1]
        
        # 1. 識別爆發特徵
        is_breakout = (last_day['Price_Breakout'] and last_day['Volume_Surge']) or \
                      (last_day.get('Pro_Bottom_Breakout', False)) or \
                      (last_day['Close'] > last_day['BB_Upper'])
        
        # 2. 計算建議進場價位
        today_high = last_day['High']
        today_close = last_day['Close']
        ma5 = last_day['MA5']
        
        suggest_buy_trigger = round(today_high * 1.005, 2)
        suggest_buy_limit = round(max(ma5, today_close * 0.97), 2)
        suggested_stop_loss = round(min(last_day['Low'], today_close * 0.95), 2)
        recent_high = df['High'].rolling(window=60).max().iloc[-1]
        suggested_target = round(max(recent_high, today_close * 1.10), 2)

        analysis = {
            "ticker": ticker,
            "is_breakout_mode": bool(is_breakout),
            "strength_score": int(last_day.get('Score', 0)),
            "entry_strategy": "",
            "suggested_buy_trigger": suggest_buy_trigger,
            "suggested_buy_limit": suggest_buy_limit,
            "suggested_stop_loss": suggested_stop_loss,
            "suggested_target": suggested_target,
            "reason": []
        }

        if last_day.get('Pro_Bottom_Breakout', False):
            analysis["entry_strategy"] = "🌊 VCP/布林壓縮突破 (極強)"
            analysis["reason"].append("波動極度收斂後爆量轉強")
        elif last_day['Price_Breakout'] and last_day['Volume_Surge']:
            analysis["entry_strategy"] = "🚀 爆量起漲突破"
            analysis["reason"].append("量價配合突破近期平台")
        elif last_day.get('Ambush_Setup', False):
            analysis["entry_strategy"] = "🥷 縮量埋伏守株待兔"
            analysis["reason"].append("縮量洗盤結束，隨時可能發動")
            
        return analysis

def get_tomorrow_recommendations(alerts, all_dfs):
    analyzer = BreakoutAnalyzer()
    recommendations = []
    
    for ticker, alert in alerts.items():
        df = all_dfs.get(ticker)
        if df is None: continue
        
        analysis = analyzer.analyze_stock(ticker, df)
        if analysis and (analysis['is_breakout_mode'] or analysis['strength_score'] >= 75):
            recommendations.append(analysis)
            
    recommendations.sort(key=lambda x: x['strength_score'], reverse=True)
    return recommendations[:5]
