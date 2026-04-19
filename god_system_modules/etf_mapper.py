# god_system_modules/etf_mapper.py

class ETFMapper:
    def __init__(self):
        # 產業與主題對應的 ETF 清單
        self.mapping = {
            "半導體": {"code": "00830.TW", "name": "國泰費城半導體"},
            "電子": {"code": "0050.TW", "name": "元大台灣50"},
            "金融": {"code": "0055.TW", "name": "元大MSCI金融"},
            "中小型": {"code": "0051.TW", "name": "元大中型100"},
            "高股息": {"code": "00878.TW", "name": "國泰永續高股息"},
            "低波動": {"code": "00713.TW", "name": "元大台灣高息低波"},
            "科技優息": {"code": "00929.TW", "name": "復華台灣科技優息"},
            "5G通訊": {"code": "00881.TW", "name": "國泰台灣5G+"}
        }

    def get_recommendation(self, top_sectors, market_context):
        """根據強勢類股與市場體質給出 ETF 建議"""
        recommendations = []
        
        # 1. 根據強勢類股映射 (進攻型)
        for sector in top_sectors:
            name = sector['Industry']
            if name in self.mapping:
                item = self.mapping[name]
                recommendations.append({
                    "reason": f"類股動能榜首 ({name})",
                    "code": item['code'],
                    "name": item['name'],
                    "type": "進攻型"
                })
        
        # 2. 根據市場體質添加 (防禦型)
        if not market_context.is_bull_market or market_context.macro_score < 50:
            item = self.mapping["低波動"]
            recommendations.append({
                "reason": "市場震盪，啟動防禦機制",
                "code": item['code'],
                "name": item['name'],
                "type": "防禦型"
            })
            item = self.mapping["高股息"]
            recommendations.append({
                "reason": "資金轉向高殖利率標的",
                "code": item['code'],
                "name": item['name'],
                "type": "防禦型"
            })
        else:
            # 多頭市場額外推薦
            item = self.mapping["電子"]
            recommendations.append({
                "reason": "大盤趨勢向上，配置權值標的",
                "code": item['code'],
                "name": item['name'],
                "type": "攻擊型"
            })

        # 去重
        seen = set()
        final_list = []
        for r in recommendations:
            if r['code'] not in seen:
                final_list.append(r)
                seen.add(r['code'])
                
        return final_list[:3] # 最多回傳 3 個
