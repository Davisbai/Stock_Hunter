# god_system_modules/ui_handlers.py

import datetime
import os
import re
import yfinance as yf
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .config import STOCK_MAP, BACKTEST_START_DATE
from .utils import load_watchlist, save_watchlist, send_line_message
from .trading_system import TaiwanStockTradingSystem
from .quant_engine import AdvancedQuantEngine, ShioajiMockAPI
from .breakout_analyzer import get_tomorrow_recommendations

console = Console()

def run_full_scan_gui(scanner, is_auto=False):
    if not is_auto:
        console.print("\n[bold green]🚀 啟動全自動策略掃描 (核心實作還原版)...[/bold green]")

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not is_auto: print(f"--- 系統啟動時間: {now_str} ---")

    watchlist = load_watchlist()
    watchlist_updated = False

    hot_stocks = scanner.scan()
    DYNAMIC_MAP = {f"{item['code']}.TW": item['name'] for item in hot_stocks}
    WATCHLIST_MAP = {k: v.get("名稱", "") for k, v in watchlist.items()}
    
    COMBINED_MAP = {**STOCK_MAP, **DYNAMIC_MAP, **WATCHLIST_MAP}

    system = TaiwanStockTradingSystem(
        tickers=list(COMBINED_MAP.keys()),
        start_date=BACKTEST_START_DATE
    )
    
    system.fetch_market_data()
    
    all_dfs = {}
    for ticker in COMBINED_MAP.keys():
        df = system.process_stock(ticker)
        if df is not None:
            all_dfs[ticker] = df
            
    summary, alerts, logs = {}, {}, {}
    for ticker, df in all_dfs.items():
        last_day = df.iloc[-1]
        alerts[ticker] = {
            "日期": df.index[-1].strftime("%Y-%m-%d"),
            "收盤價": round(float(last_day['Close']), 2),
            "月線價": round(float(last_day['MA20']), 2),
            "大盤安全": bool(last_day['Market_OK']),
            "今日評分": int(last_day['Score']),
            "個股原始評分": int(last_day['Raw_Score']),
            "是否觸發賣出": bool(last_day['Sell_Signal']),
            "獨立行情": bool(last_day['Independent_Alpha']),
            "精準買點": bool(last_day.get('Pro_Bottom_Breakout', False)),
            "縮量埋伏": bool(last_day.get('Ambush_Setup', False)),
            "高檔背離": bool(last_day.get('Top_Divergence', False)),
            "乖離過大": bool(last_day.get('Overextended_MA5', False))
        }
        
    line_message_lines = [f"📊 Davis，今日台股策略掃描已完成\n時間: {now_str}\n"]

    tomorrow_hints = get_tomorrow_recommendations(alerts, all_dfs)
    if tomorrow_hints:
        line_message_lines.append("⚡ 【明日潛力進場標的】")
        for hint in tomorrow_hints:
            s_name = COMBINED_MAP.get(hint['ticker'], "")
            msg = f"🔥 {s_name} ({hint['ticker'].replace('.TW','')}): {hint['entry_strategy']}\n"
            msg += f"   - 追價點: {hint['suggested_buy_trigger']} | 拉回點: {hint['suggested_buy_limit']}\n"
            msg += f"   - 停損位: {hint['suggested_stop_loss']} | 目標位: {hint['suggested_target']}"
            line_message_lines.append(msg)
        line_message_lines.append("-" * 30 + "\n")

    for stock, alert in alerts.items():
        stock_name = COMBINED_MAP.get(stock, "")
        tag = "[熱門]" if stock in DYNAMIC_MAP else "[固定]"
        score = alert['今日評分']
        
        if not is_auto:
            status = "🟢 買進" if score >= 65 else "⚪ 觀望"
            if alert["是否觸發賣出"]: status = "🔴 賣出"
            print(f"{tag} {stock:<7} {stock_name:<4} | 收盤: {alert['收盤價']:>6.1f} | 評分: {score:>3} | 建議: {status}")
        
        # 同步監控清單
        if alert["是否觸發賣出"] and stock in watchlist:
            del watchlist[stock]
            watchlist_updated = True
        elif score >= 75 and stock not in watchlist:
            watchlist[stock] = {"名稱": stock_name, "加入日期": alert['日期'], "加入價格": alert['收盤價']}
            watchlist_updated = True

    if watchlist_updated: save_watchlist(watchlist)
    send_line_message("\n".join(line_message_lines))
    
    if not is_auto:
        console.print("\n[bold cyan]✅ 掃描與同步完成[/bold cyan]")

def run_single_query_mode_gui():
    while True:
        user_input = console.input("\n👉 [bold cyan]請輸入股票代碼或名稱 (q 退出):[/bold cyan] ").strip()
        if not user_input or user_input.lower() == 'q': break
        ticker = f"{user_input}.TW" if user_input.isdigit() else user_input

        system = TaiwanStockTradingSystem(tickers=[ticker])
        system.fetch_market_data()
        df = system.process_stock(ticker)
        if df is None: continue
        
        last_day = df.iloc[-1]
        score = int(last_day['Score'])
        console.print(f"\n📊 {ticker} 診斷結果: 評分 {score}")
        if last_day['Sell_Signal']: console.print("🔴 建議賣出")
        elif score >= 60: console.print("🟢 建議買進")

def run_market_health_check_gui():
    console.print("\n[bold magenta]🌐 正在診斷台股大盤現況...[/bold magenta]")
    try:
        df = yf.download("^TWII", period="3mo", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        last_close = float(df['Close'].iloc[-1])
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        status = "[bold green]多頭[/bold green]" if last_close > ma20 else "[bold red]空頭[/bold red]"
        console.print(Panel(f"目前指數: {last_close:.2f}\n月線位置: {ma20:.2f}\n狀態: {status}"))
    except Exception as e: console.print(f"錯誤: {e}")
