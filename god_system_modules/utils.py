# god_system_modules/utils.py

import os
import json
import requests
from rich.console import Console
from .config import WATCHLIST_FILE, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID

console = Console()

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=4)

def send_line_message(text_content):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        'to': LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': text_content
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            console.print('\n✅ [bold green][系統提示] LINE 訊息已成功推播至您的手機！[/bold green]')
        else:
            console.print(f'\n❌ [bold red][系統提示] 發送 LINE 訊息失敗：{response.status_code} - {response.text}[/bold red]')
    except Exception as e:
        console.print(f"\n❌ [bold red][系統提示] LINE API 請求發生錯誤: {e}[/bold red]")
