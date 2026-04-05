# main.py (原 GOD_SYSTEM_NEW.py)

import datetime
import os
import time
import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from god_system_modules.scanners import YahooMarketScanner
from god_system_modules.ui_handlers import (
    run_full_scan_gui, 
    run_single_query_mode_gui, 
    run_market_health_check_gui
)
import yfinance as yf

console = Console()

def main():
    parser = argparse.ArgumentParser(description="台股獵手 - 模組化專業版 (Stock-Hunter)")
    parser.add_argument("--auto", action="store_true", help="執行自動化模式 (不進入選單)")
    args = parser.parse_args()

    scanner = YahooMarketScanner()

    if args.auto:
        rprint(f"[bold green]🤖 正在以自動化模式執行定時掃描... ({datetime.datetime.now()})[/bold green]")
        
        # 🔗 [新增] 檢查今日是否為開市日 (檢查加權指數是否有今日資料)
        try:
            rprint("[dim]正在檢查市場開市狀態...[/dim]")
            market = yf.download("^TWII", period="1d", progress=False, auto_adjust=True)
            if not market.empty:
                last_trade_date = market.index[-1].date()
                today = datetime.datetime.now().date()
                if last_trade_date < today:
                    rprint(f"[bold yellow]⚠️ 今日 ({today}) 非開市日或尚未有數據，跳過自動掃描。[/bold yellow]")
                    return
            else:
                rprint("[bold red]❌ 無法獲取市場數據，跳過掃描。[/bold red]")
                return
        except Exception as e:
            rprint(f"[bold red]❌ 檢查開市狀態時發生錯誤: {e}[/bold red]")
            return

        run_full_scan_gui(scanner, is_auto=True)
        rprint("[bold blue]✅ 自動化掃描任務已結束。[/bold blue]")
        return

    rprint(f"\n🚀 啟動【台股獵手 - 模組化專業版】 {datetime.datetime.now().date()}")
    
    while True:
        menu = Panel(
            "1. 🚀 [bold cyan]執行完整策略掃描[/bold cyan] (大盤監控 + 庫存更新 + LINE推播)\n"
            "2. 🔎 [bold yellow]單股深度診斷[/bold yellow] (即時回測與技術籌碼評分)\n"
            "5. 📊 [bold magenta]檢查大盤現況[/bold magenta] (加權指數體質與均線分析)\n"
            "q. [bold red]退出系統[/bold red]",
            title="🎯 台股獵手 v3.0 - Automation & Breakout Ready",
            border_style="bright_blue"
        )
        console.print(menu)
        
        choice = console.input("\n[bold]請選擇功能: [/bold]").strip().lower()
        
        if choice == '1':
            run_full_scan_gui(scanner)
        elif choice == '2':
            run_single_query_mode_gui()
        elif choice == '5':
            run_market_health_check_gui()
        elif choice == 'q':
            console.print("\n[bold red]👋 系統已退出，祝您投資順利！[/bold red]\n")
            break
        else:
            console.print("[bold red]❌ 無效的選擇，請重新輸入。[/bold red]")
            time.sleep(1)

if __name__ == "__main__":
    main()
