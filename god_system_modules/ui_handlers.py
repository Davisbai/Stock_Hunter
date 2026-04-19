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
from .utils import load_watchlist, save_watchlist, send_line_message, send_flex_message
from .trading_system import TaiwanStockTradingSystem
from .quant_engine import AdvancedQuantEngine, ShioajiMockAPI
from .breakout_analyzer import get_tomorrow_recommendations
from .sector_analyzer import SectorAnalyzer
from .etf_mapper import ETFMapper
from .flex_templates import generate_stock_report_flex
from .catalyst_engine import CatalystEngine

console = Console()

def run_full_scan_gui(scanner, is_auto=False):
    if not is_auto:
        console.print("\n[bold green]🚀 啟動全自動策略掃描 (專業升級版)...[/bold green]")

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. 總體經濟與大盤體質診斷
    engine = AdvancedQuantEngine()
    market_context = engine.fetch_macro_data()
    
    # 2. 類股動能分析
    sa = SectorAnalyzer()
    top_sectors_df = sa.fetch_sector_momentum()
    top_sectors = sa.get_top_sectors(5)
    rising_stars = sa.identify_rising_stars(3)
    
    # 3. ETF 映射建議
    em = ETFMapper()
    etf_recs = em.get_recommendation(top_sectors, market_context)

    # 4. 個股掃描與分析
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
            
    alerts = {}
    for ticker, df in all_dfs.items():
        last_day = df.iloc[-1]
        alerts[ticker] = {
            "日期": df.index[-1].strftime("%Y-%m-%d"),
            "收盤價": round(float(last_day['Close']), 2),
            "今日評分": int(last_day['Score']),
            "是否觸發賣出": bool(last_day['Sell_Signal']),
            "精準買點": bool(last_day.get('Pro_Bottom_Breakout', False)),
            "縮量埋伏": bool(last_day.get('Ambush_Setup', False))
        }
        
    # 5. 整理個股推薦清單 (取前 3 名高分且具備突破訊號者)
    tomorrow_hints = get_tomorrow_recommendations(alerts, all_dfs)
    ce = CatalystEngine()
    
    stock_picks = []
    for hint in tomorrow_hints[:3]:
        ticker = hint['ticker']
        s_name = COMBINED_MAP.get(ticker, "未知標的")
        
        # 🔎 動態偵測催化劑與主題
        try:
            # 獲取 Ticker 物件與 info 進行動態探測
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            dynamic_reason = ce.discover_themes(ticker, s_name, info)
        except:
            dynamic_reason = "技術面強勢突破 | 量能放大"
            
        stock_picks.append({
            "ticker": ticker,
            "name": s_name,
            "reason": f"{dynamic_reason} | 建議價: {hint['suggested_buy_trigger']}"
        })

    # 6. 組裝專業文字報表 (支援轉傳)
    line_message_lines = [
        f"📊 台股量化日報 ({now_str})",
        "────────────────",
        "🌍 【市場宏觀體質】",
        f"● 體質診斷: {market_context.current_regime}",
        f"● 美元/金油: {market_context.description[:20]}...",
        "",
        "📈 【強勢類股排行】"
    ]
    
    for i, sector in enumerate(top_sectors, 1):
        line_message_lines.append(f"{i}. {sector['Industry']} (動能: {sector['Net%']}%)")
        
    if rising_stars:
        line_message_lines.append("")
        line_message_lines.append("🔍 【潛力起漲類股 (Rising Stars)】")
        for star in rising_stars:
            line_message_lines.append(f"● {star['Industry']}: {star['Tag']} 跡象")
            
    line_message_lines.append("")
    line_message_lines.append("🚀 【潛力標的與動態題材】")
    for pick in stock_picks:
        line_message_lines.append(f"● {pick['name']} ({pick['ticker'].replace('.TW','')})")
        line_message_lines.append(f"  └ {pick['reason']}")
    
    line_message_lines.append("\n💡 長按本訊息即可直接轉傳分享！")
    
    send_line_message("\n".join(line_message_lines))
    
    # 同步監控清單
    for stock, alert in alerts.items():
        stock_name = COMBINED_MAP.get(stock, "")
        score = alert['今日評分']
        if alert["是否觸發賣出"] and stock in watchlist:
            del watchlist[stock]
            watchlist_updated = True
        elif score >= 80 and stock not in watchlist:
            watchlist[stock] = {"名稱": stock_name, "加入日期": alert['日期'], "加入價格": alert['收盤價']}
            watchlist_updated = True

    if watchlist_updated: save_watchlist(watchlist)
    
    if not is_auto:
        console.print("\n[bold cyan]✅ 全自動分析與推播任務完成[/bold cyan]")

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
