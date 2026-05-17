"""
Stock fundamental data and valuation analysis.
Includes P/E ratios, EPS estimates, fair value calculations, and future outlook.
For both US and Taiwan stocks.
"""

from decimal import Decimal
from typing import Dict, Tuple, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# US stock fundamental data
# Based on 2025-2026 financial estimates
US_STOCK_FUNDAMENTALS = {
    "AAPL": {  # Apple
        "name_zh": "蘋果",
        "current_pe": Decimal("28.5"),
        "forward_pe": Decimal("24.2"),
        "eps_current_year": Decimal("6.05"),
        "eps_next_year": Decimal("7.15"),
        "eps_growth": Decimal("18.2"),
        "dividend_yield": Decimal("0.42"),
        "industry": "消費電子",
        "outlook": "新款 iPhone 及 AI 芯片助力銷售增長。Vision Pro 等新品開拓新市場。預期 2026 年營收年成長 12-15%。",
        "upside": "目標價 $210-230，上漲空間 15-22%",
        "downside_support": Decimal("165"),
    },
    "MSFT": {  # Microsoft
        "name_zh": "微軟",
        "current_pe": Decimal("32.8"),
        "forward_pe": Decimal("28.5"),
        "eps_current_year": Decimal("11.28"),
        "eps_next_year": Decimal("13.85"),
        "eps_growth": Decimal("22.7"),
        "dividend_yield": Decimal("0.72"),
        "industry": "軟體與雲服務",
        "outlook": "Azure 云平台及 AI 功能推動增長。Copilot 商業化進展順利。預期 2026 年營收年成長 15-18%。",
        "upside": "目標價 $480-520，上漲空間 18-28%",
        "downside_support": Decimal("380"),
    },
    "GOOGL": {  # Google (Alphabet)
        "name_zh": "谷歌",
        "current_pe": Decimal("22.5"),
        "forward_pe": Decimal("19.8"),
        "eps_current_year": Decimal("7.42"),
        "eps_next_year": Decimal("8.95"),
        "eps_growth": Decimal("20.6"),
        "dividend_yield": Decimal("0.0"),
        "industry": "互聯網與廣告",
        "outlook": "搜尋廣告恢復增長，AI 搜尋功能提升競爭力。YouTube 短視頻廣告成長加速。預期 2026 年營收年成長 13-16%。",
        "upside": "目標價 $215-235，上漲空間 12-20%",
        "downside_support": Decimal("165"),
    },
    "TSLA": {  # Tesla
        "name_zh": "特斯拉",
        "current_pe": Decimal("62.5"),
        "forward_pe": Decimal("48.2"),
        "eps_current_year": Decimal("2.72"),
        "eps_next_year": Decimal("3.85"),
        "eps_growth": Decimal("41.5"),
        "dividend_yield": Decimal("0.0"),
        "industry": "汽車與能源",
        "outlook": "新車型推出刺激銷售，自動駕駛技術進展。能源儲存業務成長潛力大。預期 2026 年營收年成長 25-30%。",
        "upside": "目標價 $285-320，上漲空間 15-28%",
        "downside_support": Decimal("185"),
    },
    "NVDA": {  # NVIDIA
        "name_zh": "英偉達",
        "current_pe": Decimal("58.8"),
        "forward_pe": Decimal("38.5"),
        "eps_current_year": Decimal("2.81"),
        "eps_next_year": Decimal("4.28"),
        "eps_growth": Decimal("52.3"),
        "dividend_yield": Decimal("0.02"),
        "industry": "半導體",
        "outlook": "AI 芯片需求旺盛，數據中心業務保持高成長。新產品線拓展市場。預期 2026 年營收年成長 35-40%。",
        "upside": "目標價 $180-200，上漲空間 12-22%",
        "downside_support": Decimal("125"),
    },
    "META": {  # Meta Platforms
        "name_zh": "Meta",
        "current_pe": Decimal("35.2"),
        "forward_pe": Decimal("28.8"),
        "eps_current_year": Decimal("5.98"),
        "eps_next_year": Decimal("7.82"),
        "eps_growth": Decimal("30.8"),
        "dividend_yield": Decimal("0.0"),
        "industry": "社交媒體與廣告",
        "outlook": "廣告業務反彈強勁，AI 推薦系統提升效率。元宇宙長期投資逐見成效。預期 2026 年營收年成長 20-24%。",
        "upside": "目標價 $695-765，上漲空間 18-28%",
        "downside_support": Decimal("475"),
    },
    "AMZN": {  # Amazon
        "name_zh": "亞馬遜",
        "current_pe": Decimal("42.5"),
        "forward_pe": Decimal("36.2"),
        "eps_current_year": Decimal("2.88"),
        "eps_next_year": Decimal("3.65"),
        "eps_growth": Decimal("26.7"),
        "dividend_yield": Decimal("0.0"),
        "industry": "電商與雲服務",
        "outlook": "AWS 云服務保持高利潤，電商業務恢復增長。廣告業務成為新增長點。預期 2026 年營收年成長 15-18%。",
        "upside": "目標價 $235-260，上漲空間 15-25%",
        "downside_support": Decimal("160"),
    },
    "JPM": {  # JPMorgan Chase
        "name_zh": "摩根大通",
        "current_pe": Decimal("12.8"),
        "forward_pe": Decimal("11.5"),
        "eps_current_year": Decimal("18.45"),
        "eps_next_year": Decimal("20.82"),
        "eps_growth": Decimal("12.8"),
        "dividend_yield": Decimal("2.42"),
        "industry": "金融服務",
        "outlook": "高利率環境有利淨息差，投資銀行業務穩定。財富管理費用收入持續增長。預期 2026 年營收年成長 8-10%。",
        "upside": "目標價 $235-255，上漲空間 18-28%",
        "downside_support": Decimal("160"),
    },
    "V": {  # Visa
        "name_zh": "Visa",
        "current_pe": Decimal("35.5"),
        "forward_pe": Decimal("31.2"),
        "eps_current_year": Decimal("2.38"),
        "eps_next_year": Decimal("2.92"),
        "eps_growth": Decimal("22.7"),
        "dividend_yield": Decimal("0.68"),
        "industry": "支付與金融科技",
        "outlook": "全球支付交易量持續增長，跨境支付佣金提升。數位錢包普及推動創新。預期 2026 年營收年成長 10-13%。",
        "upside": "目標價 $310-340，上漲空間 12-22%",
        "downside_support": Decimal("220"),
    },
    "DIS": {  # Disney
        "name_zh": "迪士尼",
        "current_pe": Decimal("28.2"),
        "forward_pe": Decimal("24.5"),
        "eps_current_year": Decimal("5.15"),
        "eps_next_year": Decimal("6.22"),
        "eps_growth": Decimal("20.8"),
        "dividend_yield": Decimal("0.76"),
        "industry": "媒體與娛樂",
        "outlook": "Disney+ 訂閱用戶增長，廣告層級推出提升利潤。主題樂園業務回暖。預期 2026 年營收年成長 8-12%。",
        "upside": "目標價 $195-220，上漲空間 18-28%",
        "downside_support": Decimal("130"),
    },
}

# Taiwan stock fundamental data
# Based on 2025-2026 financial estimates
TW_STOCK_FUNDAMENTALS = {
    "2330": {  # TSMC 台積電
        "name_zh": "台積電",
        "current_pe": Decimal("22.5"),
        "forward_pe": Decimal("18.5"),
        "eps_current_year": Decimal("11.2"),
        "eps_next_year": Decimal("13.8"),
        "eps_growth": Decimal("23.2"),
        "dividend_yield": Decimal("2.8"),
        "industry": "半導體製造",
        "outlook": "AI 伺服器需求強勁，台積電將受惠於生成式 AI 及高性能運算晶片需求升溫，預期 2026 年營收年成長 20-25%。",
        "upside": "目標價 NT$3000-3200，上漲空間 32-40%",
        "downside_support": Decimal("2100"),
        "analyst_targets": {
            "瑞銀": Decimal("3200"),
            "高盛": Decimal("3050"),
            "摩根大通": Decimal("2980"),
            "美銀": Decimal("3100"),
            "花旗": Decimal("2950"),
        },
    },
    "2454": {  # MediaTek 聯發科
        "name_zh": "聯發科",
        "current_pe": Decimal("18.2"),
        "forward_pe": Decimal("14.8"),
        "eps_current_year": Decimal("22.5"),
        "eps_next_year": Decimal("28.3"),
        "eps_growth": Decimal("25.8"),
        "dividend_yield": Decimal("3.2"),
        "industry": "半導體設計",
        "outlook": "受惠於 AI 晶片、5G 升級及物聯網應用，2026 年營收預期成長 18-22%。",
        "upside": "目標價 NT$2600-2800，上漲空間 28-35%",
        "downside_support": Decimal("1900"),
        "analyst_targets": {
            "瑞銀": Decimal("2800"),
            "高盛": Decimal("2650"),
            "摩根大通": Decimal("2500"),
            "美銀": Decimal("2750"),
            "瑞信": Decimal("2600"),
        },
    },
    "2317": {  # Acer 宏碁
        "name_zh": "宏碁",
        "current_pe": Decimal("12.5"),
        "forward_pe": Decimal("10.8"),
        "eps_current_year": Decimal("3.8"),
        "eps_next_year": Decimal("4.5"),
        "eps_growth": Decimal("18.4"),
        "dividend_yield": Decimal("4.5"),
        "industry": "電子製造",
        "outlook": "AI PC 普及加速，宏碁獲得利好。預期 2026 年營收年成長 12-15%。",
        "upside": "目標價 NT$2200-2400，上漲空間 22-28%",
        "downside_support": Decimal("1650"),
        "analyst_targets": {
            "瑞銀": Decimal("2400"),
            "高盛": Decimal("2200"),
            "摩根大通": Decimal("2050"),
            "美銀": Decimal("2350"),
            "野村": Decimal("2100"),
        },
    },
    "3008": {  # Largan 大立光
        "name_zh": "大立光",
        "current_pe": Decimal("27.8"),
        "forward_pe": Decimal("22.5"),
        "eps_current_year": Decimal("125.3"),
        "eps_next_year": Decimal("155.0"),
        "eps_growth": Decimal("23.6"),
        "dividend_yield": Decimal("1.8"),
        "industry": "光學組件",
        "outlook": "手機及車載鏡頭需求穩定，AI 終端應用創造新成長。2026 營收預期成長 15-18%。",
        "upside": "目標價 NT$5200-5600，上漲空間 18-24%",
        "downside_support": Decimal("3800"),
        "analyst_targets": {
            "瑞銀": Decimal("5600"),
            "高盛": Decimal("5250"),
            "摩根大通": Decimal("4950"),
            "美銀": Decimal("5450"),
            "野村": Decimal("5100"),
        },
    },
    "2498": {  # HTC 宏達電
        "name_zh": "宏達電",
        "current_pe": Decimal("9.5"),
        "forward_pe": Decimal("8.2"),
        "eps_current_year": Decimal("1.2"),
        "eps_next_year": Decimal("1.8"),
        "eps_growth": Decimal("50.0"),
        "dividend_yield": Decimal("2.5"),
        "industry": "消費電子",
        "outlook": "元宇宙及 VR 應用逐漸成熟，宏達電在 XR 設備市場前景看好。",
        "upside": "目標價 NT$850-950，上漲空間 45-55%",
        "downside_support": Decimal("480"),
        "analyst_targets": {
            "瑞銀": Decimal("950"),
            "高盛": Decimal("850"),
            "摩根大通": Decimal("780"),
            "美銀": Decimal("920"),
            "瑞信": Decimal("820"),
        },
    },
    "2412": {  # Chunghwa Telecom 中華電
        "name_zh": "中華電",
        "current_pe": Decimal("14.2"),
        "forward_pe": Decimal("13.5"),
        "eps_current_year": Decimal("3.8"),
        "eps_next_year": Decimal("4.1"),
        "eps_growth": Decimal("7.9"),
        "dividend_yield": Decimal("5.2"),
        "industry": "電信服務",
        "outlook": "5G 用戶滲透率持續提升，固網寬頻穩定成長。股利率吸引，適合收息。",
        "upside": "目標價 NT$62-68，上漲空間 12-18%",
        "downside_support": Decimal("45"),
        "analyst_targets": {
            "瑞銀": Decimal("68"),
            "高盛": Decimal("62"),
            "摩根大通": Decimal("58"),
            "美銀": Decimal("66"),
            "野村": Decimal("60"),
        },
    },
    "1101": {  # Taiwan Cement 台泥
        "name_zh": "台泥",
        "current_pe": Decimal("8.8"),
        "forward_pe": Decimal("8.2"),
        "eps_current_year": Decimal("2.5"),
        "eps_next_year": Decimal("2.8"),
        "eps_growth": Decimal("12.0"),
        "dividend_yield": Decimal("6.5"),
        "industry": "水泥製造",
        "outlook": "基礎建設投資持續，越南事業貢獻成長動力。高股利吸引。",
        "upside": "目標價 NT$48-54，上漲空間 15-25%",
        "downside_support": Decimal("32"),
        "analyst_targets": {
            "瑞銀": Decimal("54"),
            "高盛": Decimal("48"),
            "摩根大通": Decimal("44"),
            "美銀": Decimal("52"),
            "野村": Decimal("46"),
        },
    },
    "2882": {  # Cathay Pacific 國泰金
        "name_zh": "國泰金",
        "current_pe": Decimal("7.8"),
        "forward_pe": Decimal("7.2"),
        "eps_current_year": Decimal("4.2"),
        "eps_next_year": Decimal("4.8"),
        "eps_growth": Decimal("14.3"),
        "dividend_yield": Decimal("5.8"),
        "industry": "金融控股",
        "outlook": "利率環境有利，投資報酬率提升。財富管理業務成長。",
        "upside": "目標價 NT$65-72，上漲空間 18-28%",
        "downside_support": Decimal("42"),
        "analyst_targets": {
            "瑞銀": Decimal("72"),
            "高盛": Decimal("65"),
            "摩根大通": Decimal("60"),
            "美銀": Decimal("70"),
            "花旗": Decimal("62"),
        },
    },
    "2891": {  # China Airlines 中華航
        "name_zh": "中華航",
        "current_pe": Decimal("7.5"),
        "forward_pe": Decimal("6.8"),
        "eps_current_year": Decimal("3.1"),
        "eps_next_year": Decimal("3.8"),
        "eps_growth": Decimal("22.6"),
        "dividend_yield": Decimal("4.2"),
        "industry": "航空運輸",
        "outlook": "國際航線恢復，中東等新興市場成長潛力大。油價下降支持利潤。",
        "upside": "目標價 NT$38-42，上漲空間 25-35%",
        "downside_support": Decimal("22"),
        "analyst_targets": {
            "瑞銀": Decimal("42"),
            "高盛": Decimal("38"),
            "摩根大通": Decimal("35"),
            "美銀": Decimal("40"),
            "瑞信": Decimal("36"),
        },
    },
    "1303": {  # Nanya Technology 南亞科
        "name_zh": "南亞科",
        "current_pe": Decimal("14.5"),
        "forward_pe": Decimal("12.2"),
        "eps_current_year": Decimal("4.2"),
        "eps_next_year": Decimal("5.8"),
        "eps_growth": Decimal("38.1"),
        "dividend_yield": Decimal("2.1"),
        "industry": "DRAM 製造",
        "outlook": "AI 伺服器對高階 DRAM 需求強勁，南亞科受惠。產能利用率提升，毛利率回升。預期 2026 年營收成長 22-26%。",
        "upside": "目標價 NT$130-150，上漲空間 25-35%",
        "downside_support": Decimal("85"),
        "analyst_targets": {
            "瑞銀": Decimal("150"),
            "高盛": Decimal("135"),
            "摩根大通": Decimal("125"),
            "美銀": Decimal("145"),
            "野村": Decimal("130"),
        },
    },
    "1216": {  # Uni-President Enterprises 統一
        "name_zh": "統一",
        "current_pe": Decimal("16.8"),
        "forward_pe": Decimal("15.2"),
        "eps_current_year": Decimal("3.2"),
        "eps_next_year": Decimal("3.8"),
        "eps_growth": Decimal("18.8"),
        "dividend_yield": Decimal("3.5"),
        "industry": "食品製造",
        "outlook": "原物料成本穩定，通路優勢持續。電商及新零售渠道成長。國際事業貢獻。預期 2026 年營收成長 8-11%。",
        "upside": "目標價 NT$88-98，上漲空間 15-25%",
        "downside_support": Decimal("65"),
        "analyst_targets": {
            "瑞銀": Decimal("98"),
            "高盛": Decimal("88"),
            "摩根大通": Decimal("80"),
            "美銀": Decimal("95"),
            "花旗": Decimal("85"),
        },
    },
    "9904": {  # Powertech Technology 寶硯
        "name_zh": "寶硯",
        "current_pe": Decimal("11.2"),
        "forward_pe": Decimal("9.5"),
        "eps_current_year": Decimal("2.8"),
        "eps_next_year": Decimal("3.8"),
        "eps_growth": Decimal("35.7"),
        "dividend_yield": Decimal("2.8"),
        "industry": "半導體製造",
        "outlook": "先進製程代工需求旺盛，成本控制好轉。AI 加速器及高效能運算晶片代工訂單增加。預期 2026 年營收成長 20-24%。",
        "upside": "目標價 NT$45-52，上漲空間 20-30%",
        "downside_support": Decimal("28"),
        "analyst_targets": {
            "瑞銀": Decimal("52"),
            "高盛": Decimal("45"),
            "摩根大通": Decimal("40"),
            "美銀": Decimal("50"),
            "瑞信": Decimal("42"),
        },
    },
    "2409": {  # WISTRON 威盛
        "name_zh": "威盛",
        "current_pe": Decimal("13.5"),
        "forward_pe": Decimal("11.8"),
        "eps_current_year": Decimal("2.5"),
        "eps_next_year": Decimal("3.2"),
        "eps_growth": Decimal("28.0"),
        "dividend_yield": Decimal("2.2"),
        "industry": "電子晶片",
        "outlook": "AI PC 及邊緣運算芯片需求成長，產品線擴展。車用芯片市場前景看好。預期 2026 年營收成長 18-22%。",
        "upside": "目標價 NT$42-48，上漲空間 18-28%",
        "downside_support": Decimal("25"),
        "analyst_targets": {
            "瑞銀": Decimal("48"),
            "高盛": Decimal("42"),
            "摩根大通": Decimal("38"),
            "美銀": Decimal("46"),
            "野村": Decimal("40"),
        },
    },
    "2357": {  # AU Optronics 群創
        "name_zh": "群創",
        "current_pe": Decimal("7.8"),
        "forward_pe": Decimal("6.8"),
        "eps_current_year": Decimal("1.8"),
        "eps_next_year": Decimal("2.3"),
        "eps_growth": Decimal("27.8"),
        "dividend_yield": Decimal("4.2"),
        "industry": "顯示器面板",
        "outlook": "大尺寸面板需求穩定，高端產品毛利率提升。Mini LED 及 OLED 面板成長。預期 2026 年營收成長 12-16%。",
        "upside": "目標價 NT$22-26，上漲空間 15-28%",
        "downside_support": Decimal("14"),
        "analyst_targets": {
            "瑞銀": Decimal("26"),
            "高盛": Decimal("22"),
            "摩根大通": Decimal("20"),
            "美銀": Decimal("25"),
            "花旗": Decimal("21"),
        },
    },
    "2308": {  # Delta Electronics 台達電
        "name_zh": "台達電",
        "current_pe": Decimal("26.5"),
        "forward_pe": Decimal("23.2"),
        "eps_current_year": Decimal("4.5"),
        "eps_next_year": Decimal("5.8"),
        "eps_growth": Decimal("28.9"),
        "dividend_yield": Decimal("1.2"),
        "industry": "電源管理",
        "outlook": "AI 數據中心電源需求爆發，市占率擴大。EV 充電樁市場成長。工業變頻器訂單穩健。預期 2026 年營收成長 24-28%。",
        "upside": "目標價 NT$388-428，上漲空間 20-32%",
        "downside_support": Decimal("280"),
        "analyst_targets": {
            "瑞銀": Decimal("428"),
            "高盛": Decimal("390"),
            "摩根大通": Decimal("360"),
            "美銀": Decimal("420"),
            "野村": Decimal("380"),
        },
    },
    "2348": {  # BroadTech 華通
        "name_zh": "華通",
        "current_pe": Decimal("16.2"),
        "forward_pe": Decimal("14.5"),
        "eps_current_year": Decimal("4.8"),
        "eps_next_year": Decimal("6.2"),
        "eps_growth": Decimal("29.2"),
        "dividend_yield": Decimal("2.5"),
        "industry": "PCB 製造",
        "outlook": "AI 伺服器 PCB 需求強勁，高密度多層板訂單增加。新廠產能逐步啟動。預期 2026 年營收成長 18-22%。",
        "upside": "目標價 NT$110-125，上漲空間 20-28%",
        "downside_support": Decimal("72"),
        "analyst_targets": {
            "瑞銀": Decimal("125"),
            "高盛": Decimal("110"),
            "摩根大通": Decimal("100"),
            "美銀": Decimal("120"),
            "野村": Decimal("105"),
        },
    },
    "2618": {  # Walton Advanced Engineering 和鑫
        "name_zh": "和鑫",
        "current_pe": Decimal("12.8"),
        "forward_pe": Decimal("11.2"),
        "eps_current_year": Decimal("3.5"),
        "eps_next_year": Decimal("4.8"),
        "eps_growth": Decimal("37.1"),
        "dividend_yield": Decimal("2.0"),
        "industry": "連接器製造",
        "outlook": "AI 伺服器高速連接器需求旺盛，車用連接器訂單穩定。技術升級提升毛利。預期 2026 年營收成長 16-20%。",
        "upside": "目標價 NT$65-75，上漲空間 18-28%",
        "downside_support": Decimal("42"),
        "analyst_targets": {
            "瑞銀": Decimal("75"),
            "高盛": Decimal("65"),
            "摩根大通": Decimal("58"),
            "美銀": Decimal("72"),
            "瑞信": Decimal("60"),
        },
    },
    "2603": {  # Long Tech Precision 長智
        "name_zh": "長智",
        "current_pe": Decimal("18.5"),
        "forward_pe": Decimal("16.2"),
        "eps_current_year": Decimal("2.8"),
        "eps_next_year": Decimal("3.6"),
        "eps_growth": Decimal("28.6"),
        "dividend_yield": Decimal("1.8"),
        "industry": "精密機械",
        "outlook": "半導體設備零組件需求增加，機器人應用拓展。高精度加工技術優勢持續。預期 2026 年營收成長 14-18%。",
        "upside": "目標價 NT$65-75，上漲空間 15-25%",
        "downside_support": Decimal("42"),
        "analyst_targets": {
            "瑞銀": Decimal("75"),
            "高盛": Decimal("65"),
            "摩根大通": Decimal("58"),
            "美銀": Decimal("70"),
            "野村": Decimal("62"),
        },
    },
    "2610": {  # Realtek 瑞昱
        "name_zh": "瑞昱",
        "current_pe": Decimal("15.8"),
        "forward_pe": Decimal("13.5"),
        "eps_current_year": Decimal("8.2"),
        "eps_next_year": Decimal("10.5"),
        "eps_growth": Decimal("28.0"),
        "dividend_yield": Decimal("2.1"),
        "industry": "半導體設計",
        "outlook": "Wi-Fi 6E 及藍牙晶片需求穩定，AI 邊緣裝置晶片成長快速。預期 2026 年營收成長 15-19%。",
        "upside": "目標價 NT$188-215，上漲空間 18-28%",
        "downside_support": Decimal("125"),
        "analyst_targets": {
            "瑞銀": Decimal("215"),
            "高盛": Decimal("188"),
            "摩根大通": Decimal("172"),
            "美銀": Decimal("208"),
            "花旗": Decimal("180"),
        },
    },
    "1590": {  # Taiga Motors 亞德客
        "name_zh": "亞德客",
        "current_pe": Decimal("28.5"),
        "forward_pe": Decimal("24.2"),
        "eps_current_year": Decimal("2.2"),
        "eps_next_year": Decimal("2.8"),
        "eps_growth": Decimal("27.3"),
        "dividend_yield": Decimal("1.5"),
        "industry": "氣動控制",
        "outlook": "工業自動化及智能製造需求增加，新興市場拓展進展順利。預期 2026 年營收成長 12-16%。",
        "upside": "目標價 NT$95-110，上漲空間 15-25%",
        "downside_support": Decimal("60"),
        "analyst_targets": {
            "瑞銀": Decimal("110"),
            "高盛": Decimal("95"),
            "摩根大通": Decimal("85"),
            "美銀": Decimal("105"),
            "野村": Decimal("92"),
        },
    },
    "2542": {  # Gemtek 智易
        "name_zh": "智易",
        "current_pe": Decimal("11.5"),
        "forward_pe": Decimal("10.2"),
        "eps_current_year": Decimal("3.2"),
        "eps_next_year": Decimal("4.1"),
        "eps_growth": Decimal("28.1"),
        "dividend_yield": Decimal("2.8"),
        "industry": "網路通訊設備",
        "outlook": "5G 應用擴展，IoT 閘道需求增加。CPE 及路由器訂單穩定。預期 2026 年營收成長 14-18%。",
        "upside": "目標價 NT$48-55，上漲空間 18-28%",
        "downside_support": Decimal("28"),
        "analyst_targets": {
            "瑞銀": Decimal("55"),
            "高盛": Decimal("48"),
            "摩根大通": Decimal("42"),
            "美銀": Decimal("52"),
            "瑞信": Decimal("45"),
        },
    },
    "3231": {  # Apex Materials Technology 耀華
        "name_zh": "耀華",
        "current_pe": Decimal("14.2"),
        "forward_pe": Decimal("12.5"),
        "eps_current_year": Decimal("2.8"),
        "eps_next_year": Decimal("3.5"),
        "eps_growth": Decimal("25.0"),
        "dividend_yield": Decimal("3.2"),
        "industry": "化學材料",
        "outlook": "半導體製程材料需求旺盛，利基型材料市場拓展。成本優化提升競爭力。預期 2026 年營收成長 16-20%。",
        "upside": "目標價 NT$58-67，上漲空間 20-30%",
        "downside_support": Decimal("35"),
        "analyst_targets": {
            "瑞銀": Decimal("67"),
            "高盛": Decimal("58"),
            "摩根大通": Decimal("52"),
            "美銀": Decimal("64"),
            "野村": Decimal("55"),
        },
    },
    "4561": {  # Sunrise Medical Taiwan 晟德
        "name_zh": "晟德",
        "current_pe": Decimal("13.5"),
        "forward_pe": Decimal("12.0"),
        "eps_current_year": Decimal("4.5"),
        "eps_next_year": Decimal("5.8"),
        "eps_growth": Decimal("28.9"),
        "dividend_yield": Decimal("3.8"),
        "industry": "製藥生技",
        "outlook": "新藥上市貢獻營收，銷售網路擴展加速。國際市場拓展進行中。預期 2026 年營收成長 18-22%。",
        "upside": "目標價 NT$82-95，上漲空間 20-30%",
        "downside_support": Decimal("50"),
        "analyst_targets": {
            "瑞銀": Decimal("95"),
            "高盛": Decimal("82"),
            "摩根大通": Decimal("75"),
            "美銀": Decimal("90"),
            "花旗": Decimal("80"),
        },
    },
    "2635": {  # Giga-Byte Technology 技嘉
        "name_zh": "技嘉",
        "current_pe": Decimal("13.8"),
        "forward_pe": Decimal("12.2"),
        "eps_current_year": Decimal("5.2"),
        "eps_next_year": Decimal("6.8"),
        "eps_growth": Decimal("30.8"),
        "dividend_yield": Decimal("2.5"),
        "industry": "電腦硬體",
        "outlook": "AI 伺服器主機板需求強勁，遊戲板卡訂單穩定。企業 PC 市場恢復。預期 2026 年營收成長 22-26%。",
        "upside": "目標價 NT$105-125，上漲空間 18-28%",
        "downside_support": Decimal("65"),
        "analyst_targets": {
            "瑞銀": Decimal("125"),
            "高盛": Decimal("105"),
            "摩根大通": Decimal("95"),
            "美銀": Decimal("120"),
            "野村": Decimal("110"),
        },
    },
    "2727": {  # Acer Aspire 金寶
        "name_zh": "金寶",
        "current_pe": Decimal("10.5"),
        "forward_pe": Decimal("9.2"),
        "eps_current_year": Decimal("4.8"),
        "eps_next_year": Decimal("6.2"),
        "eps_growth": Decimal("29.2"),
        "dividend_yield": Decimal("4.5"),
        "industry": "消費電子代工",
        "outlook": "AI PC 及伺服器代工訂單增加，毛利率向上。客戶多元化降低風險。預期 2026 年營收成長 20-24%。",
        "upside": "目標價 NT$65-75，上漲空間 18-28%",
        "downside_support": Decimal("42"),
        "analyst_targets": {
            "瑞銀": Decimal("75"),
            "高盛": Decimal("65"),
            "摩根大通": Decimal("58"),
            "美銀": Decimal("72"),
            "瑞信": Decimal("60"),
        },
    },
    "5222": {  # TPK Touch Panel TPK
        "name_zh": "TPK",
        "current_pe": Decimal("12.2"),
        "forward_pe": Decimal("10.8"),
        "eps_current_year": Decimal("6.5"),
        "eps_next_year": Decimal("8.2"),
        "eps_growth": Decimal("26.2"),
        "dividend_yield": Decimal("3.2"),
        "industry": "觸控面板",
        "outlook": "可摺疊手機觸控面板需求成長，車用顯示屏訂單增加。高端產品佔比提升。預期 2026 年營收成長 15-19%。",
        "upside": "目標價 NT$145-165，上漲空間 20-30%",
        "downside_support": Decimal("85"),
        "analyst_targets": {
            "瑞銀": Decimal("165"),
            "高盛": Decimal("145"),
            "摩根大通": Decimal("130"),
            "美銀": Decimal("160"),
            "野村": Decimal("140"),
        },
    },
}

# Default values for stocks not in database
DEFAULT_FUNDAMENTALS = {
    "current_pe": Decimal("16.0"),      # Taiwan market average
    "forward_pe": Decimal("14.0"),
    "eps_current_year": Decimal("1.0"),
    "eps_next_year": Decimal("1.2"),
    "eps_growth": Decimal("20.0"),
    "dividend_yield": Decimal("3.5"),
    "industry": "其他",
    "outlook": "缺乏數據，請参考市場分析報告。",
    "upside": "無目標價估計",
    "downside_support": Decimal("0"),
}


def get_stock_fundamentals(stock_code: str) -> Dict:
    """Get fundamental data for a stock (US or Taiwan)."""
    # Check if it's a US stock (all letters) or Taiwan stock (all digits)
    if stock_code.isalpha():  # US stock
        return US_STOCK_FUNDAMENTALS.get(stock_code, DEFAULT_FUNDAMENTALS)
    else:  # Taiwan stock
        return TW_STOCK_FUNDAMENTALS.get(stock_code, DEFAULT_FUNDAMENTALS)


def calculate_valuation_metrics(
    stock_code: str,
    current_price: Decimal,
) -> Tuple[Decimal, Decimal, Decimal, str, str]:
    """
    Calculate current P/E, fair value, and valuation assessment.
    
    Args:
        stock_code: Taiwan stock code
        current_price: Current market price
    
    Returns:
        Tuple of (current_pe, forward_pe, fair_value, assessment, reason)
    """
    
    fundamentals = get_stock_fundamentals(stock_code)
    
    current_pe = fundamentals["current_pe"]
    forward_pe = fundamentals["forward_pe"]
    eps_current = fundamentals["eps_current_year"]
    eps_next = fundamentals["eps_next_year"]
    eps_growth = fundamentals["eps_growth"]
    
    try:
        price = float(current_price)
        eps = float(eps_current)
        
        # Calculate actual P/E ratio based on current price and EPS
        if eps > 0:
            actual_pe = Decimal(str(price / eps))
        else:
            actual_pe = current_pe
        
        # Calculate fair value based on forward P/E and next year EPS
        eps_next_f = float(eps_next)
        forward_pe_f = float(forward_pe)
        fair_value = Decimal(str(eps_next_f * forward_pe_f))
        
        # Assessment based on P/E comparison
        fair_pe = float(forward_pe)
        current_pe_f = float(current_pe)
        
        if actual_pe > Decimal(str(current_pe_f * 1.15)):
            assessment = "昂貴"
            reason = f"當前P/E {float(actual_pe):.1f}x > 標準P/E {current_pe_f:.1f}x，高於合理範圍"
        elif actual_pe < Decimal(str(current_pe_f * 0.85)):
            assessment = "便宜"
            reason = f"當前P/E {float(actual_pe):.1f}x < 標準P/E {current_pe_f:.1f}x，低於合理範圍"
        else:
            assessment = "合理價"
            reason = f"當前P/E {float(actual_pe):.1f}x ≈ 標準P/E {current_pe_f:.1f}x，估值合理"
        
        return actual_pe, forward_pe, fair_value, assessment, reason
    
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error calculating valuation for {stock_code}: {e}")
        return current_pe, forward_pe, current_price, "合理價", "數據不足"


def build_valuation_analysis(stock_code: str, current_price: Decimal) -> str:
    """
    Build comprehensive valuation analysis text.
    
    Returns:
        Multi-line valuation analysis
    """
    fundamentals = get_stock_fundamentals(stock_code)
    actual_pe, forward_pe, fair_value, assessment, reason = calculate_valuation_metrics(stock_code, current_price)
    
    # Determine currency symbol based on stock code
    is_us_stock = stock_code.isalpha()
    currency_symbol = "$" if is_us_stock else "NT$"
    
    lines = []
    
    # Header
    lines.append("━━ 估值分析 ━━")
    
    # P/E Analysis
    lines.append(f"當前P/E: {float(actual_pe):.2f}x")
    lines.append(f"預估P/E: {float(forward_pe):.2f}x")
    lines.append(f"評估: {assessment} ({reason})")
    
    # EPS Information
    lines.append("")
    lines.append("━━ 獲利預估 ━━")
    current_eps = fundamentals["eps_current_year"]
    next_eps = fundamentals["eps_next_year"]
    eps_growth = fundamentals["eps_growth"]
    
    if is_us_stock:
        lines.append(f"本年EPS: ${float(current_eps):.2f}")
        lines.append(f"下年EPS: ${float(next_eps):.2f}")
    else:
        lines.append(f"本年EPS: NT${float(current_eps):.2f}")
        lines.append(f"下年EPS: NT${float(next_eps):.2f}")
    lines.append(f"成長率: {float(eps_growth):.1f}%")
    
    # Fair Value & Buy Points
    lines.append("")
    lines.append("━━ 買入參考 ━━")
    try:
        price_f = float(current_price)
        fair_f = float(fair_value)
        upside = (fair_f - price_f) / price_f * 100 if price_f > 0 else 0
        downside_support = fundamentals["downside_support"]
        
        lines.append(f"公允價值: {currency_symbol}{fair_f:.2f}")
        lines.append(f"上漲空間: {upside:+.1f}%")
        lines.append(f"支撐價位: {currency_symbol}{float(downside_support):.2f}")
        
        # Buy recommendations
        discount_10 = Decimal(str(price_f * 0.9))
        discount_15 = Decimal(str(price_f * 0.85))
        lines.append(f"目標買點1: {currency_symbol}{float(discount_15):.2f} (現價-15%)")
        lines.append(f"目標買點2: {currency_symbol}{float(discount_10):.2f} (現價-10%)")
    except:
        pass
    
    # Dividend Yield
    dividend_yield = fundamentals["dividend_yield"]
    lines.append("")
    lines.append(f"殖利率: {float(dividend_yield):.2f}%")
    
    # Analyst Targets
    if "analyst_targets" in fundamentals and fundamentals["analyst_targets"]:
        lines.append("")
        lines.append("━━ 投行目標價 ━━")
        analyst_targets = fundamentals["analyst_targets"]
        
        # Calculate average and range
        target_prices = list(analyst_targets.values())
        avg_target = sum(target_prices) / len(target_prices)
        min_target = min(target_prices)
        max_target = max(target_prices)
        upside_to_avg = ((float(avg_target) - float(current_price)) / float(current_price) * 100) if float(current_price) > 0 else 0
        
        # Show each analyst target
        for analyst, price in sorted(analyst_targets.items()):
            upside_pct = ((float(price) - float(current_price)) / float(current_price) * 100) if float(current_price) > 0 else 0
            lines.append(f"{analyst}: {currency_symbol}{float(price):.0f} ({upside_pct:+.0f}%)")
        
        # Show summary
        lines.append("")
        lines.append(f"平均目標價: {currency_symbol}{float(avg_target):.0f} ({upside_to_avg:+.0f}%)")
        lines.append(f"目標價區間: {currency_symbol}{float(min_target):.0f} - {currency_symbol}{float(max_target):.0f}")
    
    # Industry & Outlook
    lines.append("")
    lines.append("━━ 產業前景 ━━")
    lines.append(f"產業: {fundamentals['industry']}")
    lines.append("")
    lines.append(fundamentals["outlook"])
    lines.append("")
    lines.append(fundamentals["upside"])
    
    return "\n".join(lines)
