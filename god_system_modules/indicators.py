# god_system_modules/indicators.py

import pandas as pd
import numpy as np

def calculate_base_indicators(df):
    """計算基礎 KD 與 MACD 指標"""
    # 1. KD 隨機指標
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min + 1e-9)
    df['K'] = df['RSV'].ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    
    # 2. MACD 指標
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 3. 均線與籌碼輔助相關基礎欄位
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA5'] = df['Close'].rolling(window=5).mean()
    return df

def calculate_advanced_signals(df):
    """計算專業級起漲、洗盤與逃頂訊號"""
    # [一般起漲點]
    df['Price_Breakout'] = df['Close'] >= df['Close'].rolling(window=10).max()
    df['Volume_Surge'] = df['Volume'] > (df['Volume'].rolling(window=5).mean() * 1.5)
    
    ma10 = df['Close'].rolling(10).mean()
    ma20 = df['MA20']
    ma5 = df['MA5']
    ma_max = pd.concat([ma5, ma10, ma20], axis=1).max(axis=1)
    ma_min = pd.concat([ma5, ma10, ma20], axis=1).min(axis=1)
    df['MA_Squeeze'] = (ma_max - ma_min) / (ma_min + 1e-9) < 0.03
    
    macd_gold_cross = (df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1))
    df['Early_Start'] = macd_gold_cross & (df['MACD'] < 0)

    # [VCP 與 波動率結構]
    exp10 = df['Close'].ewm(span=10, adjust=False).mean()
    exp20 = df['Close'].ewm(span=20, adjust=False).mean()
    df['MACD_Custom'] = exp10 - exp20
    df['Signal_Custom'] = df['MACD_Custom'].ewm(span=8, adjust=False).mean()

    df['BB_Mid'] = df['MA20']
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    df['BBW'] = (df['BB_Upper'] - (df['BB_Mid'] - 2 * df['BB_Std'])) / (df['BB_Mid'] + 1e-9) 
    df['BBW_Min_120'] = df['BBW'].rolling(window=120).min()
    df['Is_Squeezing'] = df['BBW'] <= (df['BBW_Min_120'] * 1.3) 

    df['Up_Volume'] = np.where(df['Close'] > df['Close'].shift(1), df['Volume'], 0)
    df['Down_Volume'] = np.where(df['Close'] < df['Close'].shift(1), df['Volume'], 0)
    df['Acc_Vol_Ratio'] = df['Up_Volume'].rolling(60).sum() / (df['Down_Volume'].rolling(60).sum() + 1e-5)
    df['Smart_Money_Accumulating'] = df['Acc_Vol_Ratio'] > 1.25 

    df['Volume_Breakout_Pro'] = df['Volume'] > df['Volume'].rolling(20).mean() * 2.5
    df['Price_Breakout_BB'] = (df['Close'] > df['BB_Upper']) & (df['Close'] > df['Open'])
    df['MACD_Gold_Cross_Pro'] = (df['MACD_Custom'] > df['Signal_Custom']) & (df['MACD_Custom'].shift(1) <= df['Signal_Custom'].shift(1))
    df['MACD_Near_Zero'] = df['MACD_Custom'].abs() < (df['Close'] * 0.015) 

    df['Pro_Bottom_Breakout'] = df['Is_Squeezing'].shift(1) & \
                                df['Smart_Money_Accumulating'] & \
                                df['Volume_Breakout_Pro'] & \
                                df['Price_Breakout_BB'] & \
                                (df['MACD_Gold_Cross_Pro'] | df['MACD_Near_Zero'])

    # [縮量洗盤平台埋伏]
    df['Volume_Dry_Up'] = df['Volume'].rolling(5).mean() < (df['Volume'].rolling(60).mean() * 0.5)
    df['Low_Recent_10'] = df['Low'].rolling(window=10).min()
    df['Low_Prev_10'] = df['Low'].shift(10).rolling(window=10).min()
    df['No_New_Lows'] = df['Low_Recent_10'] >= df['Low_Prev_10']
    
    big_green_candle = (df['Close'] / df['Open'] > 1.04) & (df['Volume'] > df['Volume'].rolling(20).mean() * 1.5)
    df['Has_Recent_Action'] = big_green_candle.rolling(window=20).max() == 1
    df['Ambush_Setup'] = df['No_New_Lows'] & df['Has_Recent_Action'] & df['Volume_Dry_Up'] & (df['Close'] > df['MA5'])

    # [逃頂與警報]
    high_vol_warning = df['Volume'] > (df['Volume'].rolling(20).mean() * 2)
    price_stagnant = df['Close'].pct_change() <= 0.01 
    high_level = df['Close'] > (df['MA20'] * 1.10)
    df['Top_Divergence'] = high_vol_warning & price_stagnant & high_level
    df['Overextended_MA5'] = (df['Close'] - df['MA5']) / (df['MA5'] + 1e-9) > 0.08
    
    upper_shadow = df['High'] - df[['Open', 'Close']].max(axis=1)
    candle_body = df[['Open', 'Close']].max(axis=1) - df[['Open', 'Close']].min(axis=1)
    df['Hit_Resistance'] = (df['High'] >= df['High'].rolling(60).max().shift(1)) & (upper_shadow > candle_body * 2)

    return df
