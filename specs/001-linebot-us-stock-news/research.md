# Research: LINE Bot 美股與新聞助理

**Date**: 2026-05-17  
**Phase**: 0 (Discovery & Validation)

---

## Executive Summary

本研究驗證 LINE Bot 美股助理的技術可行性。確認 Yahoo Finance API 與 Alpha Vantage API 均可免費使用；Google News RSS 無認證限制；台股供應鏈資料可由既有公開資源（TAITRA、證交所資料）取得。技術棧推薦：Python 3.11 + FastAPI + aiohttp。所有研究成果無重大障礙。

---

## 1. 市場數據來源研究

### 1.1 Yahoo Finance API

**來源**: https://finance.yahoo.com

**評估結果**: ✅ **推薦（首選）**

**優點**:
- 免費無額度限制
- 支持全球股票（包含 NASDAQ、NYSE、S&P 500 指數）
- 資料更新頻率：實時～5 分鐘
- 無需認證（直接爬蟲）或使用官方 SDK（yfinance）

**缺點**:
- 無官方 API（使用 yfinance 包裝庫進行 Web scraping）
- 反爬蟲保護：需實現 User-Agent 輪換 + 請求延遲
- 不穩定性：偶爾返回 429（Too Many Requests）

**推薦實現**:
```python
# 使用 yfinance 庫（維護良好、Python 3.11 支持）
import yfinance as yf
data = yf.download('AAPL', period='1d')
```

**成本**: 免費

---

### 1.2 Alpha Vantage API

**來源**: https://www.alphavantage.co/

**評估結果**: ✅ **推薦（備選）**

**優點**:
- 官方 REST API（穩定、有文件）
- 支持 Intraday、Daily、Weekly、Monthly 行情
- 免費層級：5 calls/minute
- 無爬蟲風險

**缺點**:
- 免費額度限制：5 calls/minute（高峰時段不足）
- 需要 API Key（免費申請）
- 股票代碼覆蓋度低於 Yahoo Finance

**推薦用途**:
- 作為 Yahoo Finance 的備選方案
- 用於無爬蟲阻力需求的場景

**成本**: 免費層級（5 calls/min），付費層級 $80/month（不需要）

---

### 1.3 決策

**採用方案**: Yahoo Finance (yfinance) 作為主要來源，Alpha Vantage 作為備選

**架構設計**:
```python
# services/market_data.py
async def get_market_data(symbols: List[str]):
    try:
        return await yahoo_finance_client.fetch(symbols)  # 5s timeout
    except Timeout:
        logger.warning(f"Yahoo Finance timeout, trying Alpha Vantage")
        return await alpha_vantage_client.fetch(symbols)  # 20s timeout
    except Exception:
        return {"error": "無法連接資料來源，請稍後重試"}
```

---

## 2. 新聞資料來源研究

### 2.1 Google News RSS Feed

**來源**: https://news.google.com/

**評估結果**: ✅ **推薦（免費、無認證）**

**優點**:
- 完全免費，無 API Key 或認證
- 無頻率限制
- RSS feed 易於解析（feedparser 庫）
- 自動分類（美國經濟新聞、科技股新聞等）

**缺點**:
- RSS feed 格式不穩定（Google 經常更新）
- 摘要長度有限（需自行擷取前 150 字）
- 新聞來源多樣（可信度參差不齊）

**推薦實現**:
```python
# integrations/google_news.py
import feedparser

def fetch_us_economic_news():
    url = "https://news.google.com/rss/search?q=美國經濟&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    return [
        {
            'title': entry.title,
            'summary': entry.summary[:150],  # 截取前 150 字
            'published': entry.published,
            'source': entry.source.title if hasattr(entry, 'source') else 'Google News'
        }
        for entry in feed.entries[:5]
    ]
```

**成本**: 免費

---

### 2.2 NewsAPI

**來源**: https://newsapi.org/

**評估結果**: ⏸️ **Optional（可升級）**

**優點**:
- 官方 API（穩定、有完善文件）
- 支持精確搜索與分類
- 免費層級：100 requests/day

**缺點**:
- 免費額度限制（100 req/day = 3.3 req/hour，不足）
- 付費層級：$45/month（初期不必要）

**推薦用途**: 若日後用戶量增加、對新聞品質要求提升，可升級至 NewsAPI

**成本**: 免費層級（100 req/day），付費 $45/month

---

### 2.3 決策

**採用方案**: Google News RSS（初版免費）+ 準備升級至 NewsAPI

**架構設計**（可升級）:
```python
# services/news_service.py (Dependency Injection)
class NewsService:
    def __init__(self, provider: NewsProvider = GoogleNewsProvider()):
        self.provider = provider  # 便於後續切換至 NewsAPI
```

---

## 3. 台股供應鏈資料來源研究

### 3.1 公開資源

**推薦來源**:

| 來源 | 說明 | 可用性 |
|------|------|--------|
| [台灣證交所](https://www.twse.com.tw) | 官方上市公司資訊 | ✅ 公開 |
| [TAITRA](https://taitra.org.tw) | 業界關聯性對照表 | ✅ 部分公開 |
| [經濟日報](https://money.udn.com/) | 供應鏈新聞分析 | ✅ 公開 |
| [CMoney 股市](https://www.cmoney.tw/) | 股票關聯度分析 | ⏸️ 需驗證 API |

### 3.2 初版實現策略

**方案**: 固定對照表（JSON / SQLite）+ 人工維護

**示例**:
```json
{
  "AAPL": {
    "zh_name": "蘋果",
    "tw_stocks": [
      {
        "code": "2330",
        "name": "台積電",
        "reason": "晶片代工供應商",
        "strength": "high"
      },
      {
        "code": "2454",
        "name": "聯發科",
        "reason": "晶片設計相關",
        "strength": "medium"
      }
    ]
  },
  "TSLA": {
    "zh_name": "特斯拉",
    "tw_stocks": [
      {
        "code": "2317",
        "name": "鴻海",
        "reason": "代工合作夥伴",
        "strength": "high"
      }
    ]
  }
}
```

**維護計畫**:
- 初版：30～50 個常見美股代碼
- 月度更新：根據新聞事件新增/修正關聯標的
- 長期升級：接入供應鏈資料 API 實現自動更新

**成本**: 免費（人工維護）

---

### 3.3 長期升級（6 個月後）

若需實時供應鏈資料，可評估：
- **Crunchbase API** ($1,000+/month) - 企業關係圖譜
- **Bloomberg Terminal** ($24,000+/year) - 專業投資資料
- 自建爬蟲 + 機器學習模型 - 成本高，推遲執行

**推薦**：初期使用固定表格，積累用戶反饋後再決定升級

---

## 4. LINE Messaging API 非同步支持研究

### 4.1 LINE Bot SDK

**來源**: https://github.com/line/line-bot-sdk-python

**評估結果**: ✅ **完全支持 asyncio**

**驗證**:
```python
# 官方 SDK 3.0+ 版本支持非同步
from linebot.v3.messaging import AsyncApiClient

async def send_message():
    client = AsyncApiClient()
    await client.push_message(...)
```

**推薦版本**: `line-bot-sdk>=3.4.0`

**成本**: 免費（官方開源）

---

## 5. 技術棧最終評估

| 技術 | 評估 | 備選 |
|------|------|------|
| **Web Framework** | FastAPI (async-first) ✅ | Django (不支持async route) ❌ |
| **市場數據** | Yahoo Finance (yfinance) ✅ | Alpha Vantage (備選) ⏳ |
| **新聞資料** | Google News RSS ✅ | NewsAPI (升級預備) ⏳ |
| **台股供應鏈** | 固定表格 (JSON) ✅ | API integration (長期) ⏳ |
| **資料庫** | SQLite (初期) + PostgreSQL (升級) ✅ | MySQL (可選) ⏳ |
| **非同步客戶端** | aiohttp / httpx ✅ | requests (同步，不推薦) ❌ |
| **LINE SDK** | Official v3.0+ ✅ | 自建 Webhook (不必要) ❌ |

---

## 6. 風險與降級策略

### 6.1 Yahoo Finance 反爬蟲

**風險**: 403 Forbidden / 429 Too Many Requests

**降級策略**:
1. 實現 User-Agent 輪換
2. 請求間隔 1 秒
3. 備選至 Alpha Vantage
4. 最終：返回清晰錯誤訊息

### 6.2 Google News RSS 變更

**風險**: RSS feed 結構更新導致解析失敗

**降級策略**:
1. 監控 RSS feed 結構
2. 自動化測試（daily）
3. 備選至 NewsAPI（需 API Key）
4. 人工干預機制

### 6.3 外部 API 超時

**風險**: 網路延遲、伺服器過載

**降級策略**:
1. 所有外部 API 調用：20 秒 timeout
2. 快速失敗 → 記錄日誌 → 清晰回覆用戶
3. 不返回過期快取資料（避免誤導投資決策）

---

## 7. 決策與建議

### ✅ 推薦立即實行

1. **Yahoo Finance (yfinance)** - 市場數據首選
   - 開始整合，實現 User-Agent 輪換與速率控制

2. **Google News RSS** - 新聞來源
   - 簡單實現，成本零，風險低

3. **固定對照表 (JSON)** - 台股關聯標的
   - 初版快速交付，積累用戶數據

4. **FastAPI + aiohttp** - 技術棧
   - 完全非同步，高併發，符合憲法原則

### ⏳ 準備升級（3～6 個月後）

1. **Alpha Vantage** - 作為 Yahoo Finance 備選
2. **NewsAPI** - 若新聞品質要求提升
3. **PostgreSQL** - 從 SQLite 升級（用戶量增長）
4. **Redis Cache** - 加速頻繁查詢

### ❌ 暫不實行

1. **自建爬蟲** - 反爬蟲風險高
2. **Crunchbase / Bloomberg** - 成本高，不必要
3. **複雜 ML 模型** - 優先完成 MVP

---

## 8. 結論

✅ **無重大技術障礙。推薦立即進入 Phase 1 設計階段。**

所有推薦方案：
- 免費或低成本
- 成熟穩定（官方 SDK、廣泛使用）
- 符合憲法原則（可靠性、性能、安全性）
- 可擴展性強（易於升級或替換）

---

**Research Status**: ✅ COMPLETE  
**Recommended Action**: Proceed to Phase 1 (Design & Contracts)  
**Last Updated**: 2026-05-17
