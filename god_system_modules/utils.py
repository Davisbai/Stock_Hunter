# god_system_modules/utils.py

import os
import json
import requests
from rich.console import Console
from .config import WATCHLIST_FILE, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID

# 導入 LINE SDK v3
try:
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        PushMessageRequest,
        TextMessage,
        FlexMessage,
        FlexContainer
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

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
    """發送純文字訊息，優先使用 SDK，失敗或未安裝則回退至 requests"""
    if SDK_AVAILABLE:
        try:
            configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                push_message_request = PushMessageRequest(
                    to=LINE_USER_ID,
                    messages=[TextMessage(text=text_content)]
                )
                line_bot_api.push_message(push_message_request)
            console.print('\n✅ [bold green][系統提示] LINE SDK 推播成功！[/bold green]')
            return
        except Exception as e:
            console.print(f"\n⚠️ [系統提示] LINE SDK 推播失敗: {e}，嘗試使用 Requests 回退方案。")

    # 回退方案 (備援)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': text_content}]
    }
    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            console.print('\n✅ [bold green][系統提示] LINE 訊息 (Requests) 發送成功！[/bold green]')
        else:
            console.print(f'\n❌ [bold red]發送 LINE 失敗：{response.status_code}[/bold red]')
    except Exception as e:
        console.print(f"\n❌ [系統提示] LINE API 請求錯誤: {e}")

def send_flex_message(alt_text, flex_json_obj):
    """發送專業級 Flex Message"""
    if not SDK_AVAILABLE:
        console.print("[bold red]❌ 無法發送 Flex Message: 未安裝 line-bot-sdk[/bold red]")
        return

    try:
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # 將 dict 轉換為 FlexContainer
            container = FlexContainer.from_dict(flex_json_obj)
            
            flex_message = FlexMessage(
                alt_text=alt_text,
                contents=container
            )
            
            push_message_request = PushMessageRequest(
                to=LINE_USER_ID,
                messages=[flex_message]
            )
            line_bot_api.push_message(push_message_request)
            console.print('\n✅ [bold green][系統提示] LINE Flex Message 推播成功！[/bold green]')
    except Exception as e:
        console.print(f"\n❌ [系統提示] LINE Flex Message 發送錯誤: {e}")
