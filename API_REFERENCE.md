# API 參考

## 📋 概述

LINE 美股助理 API 是一個 LINE Webhook，接受消息和按鈕點擊事件，返回格式化的市場數據和新聞。

### 基本信息

- **Base URL**: `https://api.example.com` (或部署域名)
- **Webhook Endpoint**: `POST /webhook/line`
- **Authentication**: HMAC-SHA256 簽名驗證
- **Response Format**: JSON
- **Content-Type**: `application/json`

---

## Webhook Endpoint

### 接收消息和事件

```
POST /webhook/line
```

#### 認證

LINE 在每個請求的 `X-Line-Signature` 標頭中發送 HMAC-SHA256 簽名。

```
X-Line-Signature: <base64_encoded_signature>
```

簽名生成:
```
signature = base64(hmac_sha256(request_body, CHANNEL_SECRET))
```

#### Request Body

```json
{
  "destination": "xxxxxxxxxx",
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "id": "100001",
        "text": "美股"
      },
      "timestamp": 1462629479859,
      "source": {
        "type": "user",
        "userId": "U206d25c2ea6bd87c17655609a1c37cb8"
      },
      "replyToken": "nHuyWiB7yP5Zw52FIkcQT"
    }
  ]
}
```

#### Response

**成功 (200 OK)**:
```json
{
  "message": "OK"
}
```

應用將非同步發送回覆消息到用戶。

**失敗 (403 Forbidden)**:
```json
{
  "detail": "Unauthorized"
}
```

簽名驗證失敗時返回。

---

## 支持的查詢命令

### 1. 美股指數查詢

**觸發**: "美股", "指數", "index"

**功能**:
- 獲取三大美股指數 (S&P 500, Nasdaq, 費城半導體)
- 顯示現價、漲跌幅、前收盤價
- 自動從緩存或 Yahoo Finance 獲取

**響應示例**:
```
📈 美股三大指數 (2026-05-17)
• S&P 500: 4500.25 ↑0.45% (前收: 4480.00)
• 那斯達克: 14200.50 ↑0.62% (前收: 14110.00)
• 費城半導體: 3820.75 ↓0.15% (前收: 3826.50)

📊 資料來源：Yahoo Finance
```

**緩存**: 5 分鐘 TTL

---

### 2. 個股查詢

**觸發**: 股票代碼 (1-5 個英文字母, 不分大小寫)
- 例: "AAPL", "TSLA", "MSFT", "nvda"

**功能**:
- 獲取個股現價和漲跌幅
- 顯示市值、PE比、股息率
- 自動取得相關新聞文章 (3-5 篇)
- 新聞按相關度排序

**響應示例**:
```
📈 AAPL - 蘋果公司
現價: $180.50 ↑0.70% (前收: $179.25)
市值: $2,800B | PE比: 28.5 | 股息: 0.45%

📰 相關新聞:
• 蘋果新 iPhone 發佈會確認
  蘋果公司宣佈將在下月舉辦新品發佈會，預計推出新款 iPhone 15...
  🔗 TechNews | 2026-05-17

• 蘋果股價創新高
  受到新品發佈預期推動，蘋果股價今日創下今年新高...
  🔗 MarketWatch | 2026-05-16

📊 資料來源：Yahoo Finance
```

**數據源**:
- 股價: Yahoo Finance (primary) → 直接錯誤 (no fallback)
- 新聞: Google News RSS

**緩存**:
- 股價: 5 分鐘 TTL
- 新聞: 1 小時 TTL

**錯誤情況**:
```
⚠️ 查詢出錯

無法找到該股票，請檢查代碼是否正確。

若問題持續發生，請重新嘗試或聯絡客服。
```

---

### 3. 經濟新聞查詢

**觸發**: "新聞", "news", "NEWS"

**功能**:
- 獲取最新的美國經濟新聞
- 包括聯準會動向、失業率、製造業指數等
- 返回 5 篇最新文章

**響應示例**:
```
📰 最新美國經濟新聞

• 聯準會升息決定確認
  美國聯邦準備委員會宣佈升息 0.5%，以控制通脹，市場反應積極...
  🔗 路透社 | 2026-05-17

• 美國失業率創新低
  美國 4 月失業率下降至 3.4%，創 50 年新低，勞動力市場供應緊張...
  🔗 美聯社 | 2026-05-16

• 供應鏈緩解推動製造業恢復
  隨著全球供應鏈正常化，美國製造業指數反彈至 55.2，超過預期...
  🔗 財經新聞 | 2026-05-15

(更多新聞...)
```

**數據源**: Google News RSS

**緩存**: 1 小時 TTL

---

### 4. 台股相關標的查詢 (Postback)

**觸發**: 股票查詢後的 "查詢台股" 按鈕點擊

**功能**:
- 獲取與美股相關的台灣股票
- 顯示關係類型 (供應商、競爭者、同業等)
- 按相關強度排序

**響應示例**:
```
🔗 與 AAPL 相關的台股標的

• 台積電 (2330) - 供應商
  台積電是 Apple 晶片製造商，負責生產 A 系列處理器
  相關度: [██████████░░░░░░░░] 95%

• 聯發科 (2454) - 競爭者
  聯發科在行動晶片領域與蘋果競爭
  相關度: [███████░░░░░░░░░░░░] 65%

• 世芯 (3661) - 產業同業
  世芯提供相關晶片設計服務
  相關度: [████░░░░░░░░░░░░░░░░] 45%

📊 資料來源：Database
```

**數據源**: 本機數據庫

**緩存**: 24 小時 TTL

---

## 數據結構

### Index (指數)

```json
{
  "code": "^GSPC",
  "name": "S&P 500",
  "zh_name": "標普 500",
  "current_price": 4500.25,
  "previous_close": 4480.00,
  "change_amount": 20.25,
  "change_percent": 0.45,
  "direction": "↑",
  "last_updated": "2026-05-17T10:30:00Z",
  "data_source": "yahoo_finance"
}
```

### Stock (個股)

```json
{
  "code": "AAPL",
  "company_name": "Apple Inc.",
  "zh_name": "蘋果公司",
  "current_price": 180.50,
  "previous_close": 179.25,
  "change_amount": 1.25,
  "change_percent": 0.70,
  "direction": "↑",
  "market_cap_billion": 2800.0,
  "pe_ratio": 28.5,
  "dividend_yield": 0.45,
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "last_updated": "2026-05-17T10:30:00Z",
  "data_source": "yahoo_finance"
}
```

### NewsArticle (新聞)

```json
{
  "id": "news_001",
  "title": "蘋果新 iPhone 發佈會確認",
  "summary": "蘋果公司宣佈將在下月舉辦新品發佈會，預計推出新款 iPhone 15...",
  "source": "TechNews",
  "url": "https://example.com/article",
  "published_at": "2026-05-17T08:00:00Z",
  "category": "earnings",
  "related_stocks": ["AAPL"],
  "relevance_score": 0.95,
  "fetched_at": "2026-05-17T10:30:00Z"
}
```

### TaiwanStock (台股)

```json
{
  "us_code": "AAPL",
  "tw_code": "2330",
  "tw_name": "台積電",
  "relationship_type": "supplier",
  "relationship_detail": "台積電是 Apple 晶片製造商",
  "strength": 0.95
}
```

---

## 錯誤代碼

| 代碼 | HTTP | 消息 | 說明 |
|------|------|------|------|
| E001_TIMEOUT | 504 | 查詢超時 | API 回應時間過長 |
| E002_INVALID_INPUT | 400 | 輸入無效 | 查詢文本格式錯誤 |
| E003_API_ERROR | 502 | API 錯誤 | 外部 API 失敗 |
| E004_STOCK_NOT_FOUND | 404 | 股票未找到 | 股票代碼不存在 |
| E005_TW_STOCK_FETCH_ERROR | 500 | 無法獲取台股 | 台股查詢失敗 |
| E999_INTERNAL_ERROR | 500 | 系統內部錯誤 | 未預期的異常 |

---

## 速率限制和超時

### 外部 API 速率限制

| API | 速率限制 | 超時 | 備註 |
|-----|---------|------|------|
| Yahoo Finance | 1 req/sec | 5s | 股票和指數數據 |
| Alpha Vantage | 5 req/min | 20s | 指數回退 (可選) |
| Google News RSS | 10 req/sec | 10s | 新聞源 |

### 自動重試

- **初始延遲**: 1 秒
- **最大嘗試次數**: 3 次
- **指數退避**: 2x (1s → 2s → 4s)
- **抖動**: ±20% 隨機

---

## 查詢日誌

所有查詢都被記錄到 `query_logs` 表以進行分析:

```json
{
  "id": 1,
  "user_id": "U206d25c2ea6bd87c17655609a1c37cb8",
  "query_text": "AAPL",
  "query_type": "stock",
  "status": "success",
  "response_time_ms": 1250,
  "error_message": null,
  "created_at": "2026-05-17T10:30:00Z"
}
```

### 查詢類型

- `index`: 美股指數查詢
- `stock`: 個股查詢
- `news`: 經濟新聞
- `tw_stock`: 台股查詢
- `unknown`: 無法識別的查詢

### 查詢狀態

- `success`: 成功返回結果
- `failed`: 查詢或驗證失敗
- `pending`: 進行中

---

## 實現細節

### 緩存鍵格式

```
index_{code}          # 例: index_gspc
stock_{code}          # 例: stock_aapl
stock_news_{code}     # 例: stock_news_aapl
economic_news         # 經濟新聞 (共享)
tw_stocks_{code}      # 例: tw_stocks_aapl
```

### TTL 策略

| 類型 | TTL | 原因 |
|------|-----|------|
| 指數 | 5 分鐘 | 市場開盤時實時性重要 |
| 股票 | 5 分鐘 | 同上 |
| 新聞 | 1 小時 | 新聞更新頻率較低 |
| 台股 | 24 小時 | 相關性數據相對穩定 |

### 回退邏輯

#### 指數查詢

```
1. 檢查緩存
2. 嘗試 Yahoo Finance (timeout: 5s)
3. 失敗？→ 嘗試 Alpha Vantage (timeout: 20s)
4. 失敗？→ 返回過期緩存或錯誤
```

#### 個股查詢

```
1. 檢查緩存
2. 嘗試 Yahoo Finance (timeout: 5s)
3. 失敗？→ 立即返回錯誤 (無備用源)
```

#### 新聞查詢

```
1. 檢查緩存
2. 嘗試 Google News RSS (timeout: 10s)
3. 失敗？→ 返回過期緩存或空列表
```

---

## 集成示例

### 直接 Webhook 測試

```bash
# 使用 curl
curl -X POST https://api.example.com/webhook/line \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: <signature>" \
  -d '{
    "destination": "xxxxxxxxxx",
    "events": [{
      "type": "message",
      "message": {
        "type": "text",
        "text": "AAPL"
      },
      "source": {
        "userId": "U206d25c..."
      },
      "replyToken": "nHuyWiB7yP5Zw52FIkcQT"
    }]
  }'
```

### Python 客戶端

```python
import requests
import json
import hmac
import hashlib
import base64

channel_secret = "your_channel_secret"
webhook_url = "https://api.example.com/webhook/line"

payload = {
    "destination": "xxxxxxxxxx",
    "events": [{
        "type": "message",
        "message": {
            "type": "text",
            "text": "美股"
        },
        "source": {
            "userId": "U206d25c2ea6bd87c17655609a1c37cb8"
        },
        "replyToken": "nHuyWiB7yP5Zw52FIkcQT"
    }]
}

body = json.dumps(payload).encode('utf-8')
signature = base64.b64encode(
    hmac.new(
        channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
).decode('utf-8')

response = requests.post(
    webhook_url,
    json=payload,
    headers={
        "X-Line-Signature": signature
    }
)

print(response.status_code)
```

---

## 健康檢查

### Endpoint

```
GET /health
```

### Response

**成功 (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-17T10:30:00Z",
  "components": {
    "database": "ok",
    "cache": "ok"
  }
}
```

---

更多信息:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系統設計
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- [Swagger UI](http://localhost:8000/docs) - 互動式 API 文檔
