# god_system_modules/flex_templates.py

def generate_stock_report_flex(context, top_sectors, etf_recs, stock_picks):
    """
    生成專業級台股分析 Flex Message JSON
    context: MarketContext 物件
    top_sectors: 類股排名 list
    etf_recs: ETF 建議 list
    stock_picks: 個股推薦 list (包含 ticker, name, reason)
    """
    
    # 顏色定義
    header_color = "#1DB446" if context.is_bull_market else "#E63946"
    
    # 构建類股文字
    sector_text = " / ".join([f"{s['Industry']}({s['Net%']}%)" for s in top_sectors[:3]])
    
    # 构建 ETF 區塊
    etf_contents = []
    for etf in etf_recs:
        etf_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"• {etf['name']}", "size": "sm", "color": "#555555", "flex": 4},
                {"type": "text", "text": etf['code'].split('.')[0], "size": "xs", "color": "#aaaaaa", "align": "end", "flex": 2}
            ]
        })

    # 构建個股區塊
    stock_contents = []
    for s in stock_picks:
        stock_contents.append({
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": s['name'], "weight": "bold", "size": "md", "color": "#111111"},
                        {"type": "text", "text": s['ticker'].split('.')[0], "size": "sm", "color": "#888888", "align": "end"}
                    ]
                },
                {"type": "text", "text": s.get('reason', '技術面突破 + 法人佈局'), "size": "xs", "color": "#666666", "wrap": True, "margin": "xs"}
            ]
        })

    flex_json = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "量化日報：台股類股輪動與強勢股診斷", "weight": "bold", "size": "sm", "color": "#ffffff"},
                {"type": "text", "text": f"截止日期: {context.last_updated}", "size": "xs", "color": "#ffffff", "margin": "xs"}
            ],
            "backgroundColor": header_color
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # Layer 1: 大盤與類股
                {"type": "text", "text": "🌐 大盤宏觀狀態與類股動能", "weight": "bold", "size": "md", "margin": "md"},
                {"type": "text", "text": f"市場體質: {context.ma_status}", "size": "sm", "color": "#333333", "margin": "sm"},
                {"type": "text", "text": f"強勢產業: {sector_text}", "size": "sm", "color": "#333333"},
                {"type": "separator", "margin": "lg"},
                
                # Layer 2: ETF 配置
                {"type": "text", "text": "📊 產業類股之 ETF 避險與配置", "weight": "bold", "size": "md", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": etf_contents
                },
                {"type": "separator", "margin": "lg"},
                
                # Layer 3: 個股推薦
                {"type": "text", "text": "🚀 近期潛力飆股推薦清單", "weight": "bold", "size": "md", "margin": "lg", "color": "#E63946"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": stock_contents
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {"type": "uri", "label": "查看更多細節", "uri": "https://tw.stock.yahoo.com/"}
                }
            ],
            "flex": 0
        }
    }
    return flex_json
