# 台股美股功能完整性檢查報告

**檢查日期**: 2026-05-20  
**檢查範圍**: 根據 [spec.md](specs/001-linebot-us-stock-news/spec.md) 中定義的功能需求

---

## 📊 功能實現概況

| 功能 | User Story | 優先級 | 狀態 | 缺漏詳情 |
|------|-----------|--------|------|---------|
| 美股三大指數 | US1 | P1 | ✅ 完成 | - |
| 個股查詢 | US2 | P1 | ⚠️ 部分完成 | 缺少快速回覆按鈕 |
| 經濟新聞 | US3 | P2 | ✅ 完成 | - |
| 台股關聯查詢 | US4 | P2 | ⚠️ 部分完成 | 缺少觸發機制 |

---

## ✅ 已實現的功能

### 1. US1: 取得三大指數摘要 (Priority: P1) ✅

**文件**: `src/handlers/index_handler.py`

**實現內容**:
- ✅ 查詢 S&P 500 指數
- ✅ 查詢那斯達克指數
- ✅ 查詢費城半導體指數
- ✅ 中文條列式格式化
- ✅ 錯誤處理和降級策略
- ✅ 觸發關鍵詞: 「美股」、「指數」

**API 來源**:
- `src/services/market_data.py` - 市場數據服務
- `src/integrations/yahoo_finance.py` - Yahoo Finance API

**格式示例**:
```
📈 美股三大指數

🔴 S&P 500: 5,234.80 ↑0.45% (前收: 5,211.40)
  資料日期: 2026-05-19

🟢 那斯達克: 16,890.50 ↓0.32% (前收: 16,944.60)
  資料日期: 2026-05-19

🔴 費城半導體: 3,145.20 ↑1.23% (前收: 3,107.60)
  資料日期: 2026-05-19

📊 資料來源：Yahoo Finance
```

---

### 2. US2: 個股代碼查詢 (Priority: P1) ⚠️ **缺快速回覆按鈕**

**文件**: `src/handlers/stock_handler.py`

**已實現內容**:
- ✅ 查詢個股價格數據（開盤、收盤、高低）
- ✅ 計算漲跌幅
- ✅ 查詢相關新聞摘要（3～5 則）
- ✅ 查詢基本面數據（PE、EPS、股息殖利率）
- ✅ 中文條列式格式化
- ✅ 支持大小寫混用（TSLA、tsla 都可)
- ✅ 錯誤處理

**缺漏內容** ❌:
- ❌ **快速回覆按鈕 (FR-007a)** - 缺少「是否查詢台股關聯股」的快速回覆選項
- 根據需求應該在個股查詢後提供兩個快速回覆按鈕:
  - 「🔗 查詢台股關聯股」 (postback: `action=tw_stock_query&code=AAPL`)
  - 「❌ 不查詢」 (postback: `action=skip`)

**格式示例**:
```
📈 AAPL - 蘋果公司
💰 現價: $180.50 🔴↑0.70%
📍 前收: $179.25
🔓 開盤價: $179.85
📈 最高價: $182.10
📉 最低價: $178.50
💼 市值: $2,800B
📊 PE比: 28.5 (實時)
💵 股息殖利率: 0.45%

📰 相關新聞:
• 蘋果新 iPhone 發佈會確認
  ...摘要...
  來源: Reuters | 2026-05-19
```

**需要的修改**:
```
【缺失】快速回覆按鈕:
□ 「🔗 查詢台股關聯股」
□ 「❌ 不查詢」
```

---

### 3. US3: 經濟新聞查詢 (Priority: P2) ✅

**文件**: `src/handlers/news_handler.py`

**實現內容**:
- ✅ 查詢最新經濟新聞
- ✅ 返回 3～5 則新聞
- ✅ 中文摘要格式（100～150 字）
- ✅ 時間和來源標註
- ✅ 錯誤處理
- ✅ 觸發關鍵詞: 「新聞」、「news」

**API 來源**:
- `src/integrations/google_news.py` - Google News RSS
- `src/integrations/alpha_vantage.py` - Alpha Vantage API

**格式示例**:
```
📰 最新美國經濟新聞

• 聯準會宣佈升息決定
  美國聯邦準備委員會在今日宣佈升息 0.5%，以控制通脹...
  來源: Reuters | 2026-05-19
  🔗 https://example.com

• 科技股集體上漲
  ...
```

---

### 4. US4: 台股關聯查詢 (Priority: P2) ⚠️ **缺少觸發機制**

**文件**: `src/handlers/tw_stock_handler.py`

**已實現內容**:
- ✅ 查詢台股關聯標的
- ✅ 返回相關關聯說明
- ✅ 中文格式化輸出
- ✅ Postback 事件處理
- ✅ 錯誤處理

**缺漏內容** ❌:
- ❌ **快速回覆按鈕觸發** - 個股查詢後應該自動提供快速回覆按鈕
- 目前只支持:
  - 手動輸入台股代碼或名稱 ✅
  - 通過 postback 事件觸發（但沒有快速回覆按鈕觸發 postback）❌

**格式示例**:
```
🔗 AAPL 相關台股

找到 3 個相關標的:

1. 台積電 (2330)
   關聯: 晶片代工核心供應商
   強度: ⭐⭐⭐⭐⭐

2. 大立光 (3008)
   關聯: iPhone 相機鏡頭供應商
   強度: ⭐⭐⭐⭐

3. 玉晶光 (3406)
   關聯: iPhone 光學元件供應商
   強度: ⭐⭐⭐
```

---

## 🔧 具體缺漏問題和修復方案

### 問題 1: 快速回覆按鈕未實現 ❌

**影響範圍**: US2（個股查詢）→ US4（台股查詢）的流程

**需求 (FR-007a)**:
```
Given 使用者完成某美股代碼查詢
When Bot 顯示後續操作
Then 必須提供是否查詢台股關聯個股的明確選項（快速回覆按鈕）
```

**問題根源**:
1. `format_stock_message()` 只返回 text 字符串
2. `send_reply_message()` 只支持純文本消息

**修復方案**:

#### 修改 1: `src/utils/formatters.py`

改變 `format_stock_message()` 的返回值:

```python
# 現在: 返回 str
def format_stock_message(...) -> str:
    return "\n".join(lines)

# 應改為: 返回 dict，包含 message 和 quick_reply
def format_stock_message(...) -> dict:
    return {
        "message": "\n".join(lines),
        "quick_reply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "🔗 查詢台股關聯股",
                        "data": f"action=tw_stock_query&code={stock.code}"
                    }
                },
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "❌ 不查詢",
                        "data": "action=skip"
                    }
                }
            ]
        }
    }
```

#### 修改 2: `src/handlers/stock_handler.py`

調整返回結構:

```python
# 返回包含 quick_reply 的完整結構
return {
    "success": True,
    "message": formatted_result["message"],
    "quick_reply": formatted_result.get("quick_reply"),  # 新增
}
```

#### 修改 3: `src/api/webhooks.py`

更新 `send_reply_message()` 支持快速回覆:

```python
async def send_reply_message(
    self, reply_token: str, text: str, quick_reply: Optional[dict] = None
) -> bool:
    """Send reply message with optional quick reply buttons"""
    settings = get_settings()
    url = "https://api.line.me/v2/bot/message/reply"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    }
    
    message = {
        "type": "text",
        "text": text,
    }
    
    # 添加快速回覆
    if quick_reply:
        message["quickReply"] = quick_reply
    
    data = {
        "replyToken": reply_token,
        "messages": [message]
    }
    
    # ... 發送請求 ...
```

#### 修改 4: `src/api/webhooks.py` - Webhook 路由

處理返回的完整結構:

```python
elif detect_query_type(query_text) == "stock":
    # Stock query (AAPL, TSLA, etc.)
    try:
        stock_code = validate_stock_code(query_text)
        result = await handle_stock_query(self.db, stock_code)
        
        if result.get("success"):
            message = result.get("message")
            quick_reply = result.get("quick_reply")
            
            # 發送帶快速回覆的消息
            await self.send_reply_message(
                reply_token, 
                message, 
                quick_reply=quick_reply
            )
        # ...
```

---

## 🎯 修復優先級

| 優先級 | 項目 | 估計工時 | 難度 |
|--------|------|---------|------|
| P0 (必須) | 快速回覆按鈕實現 | 2-3 小時 | ⭐⭐ 中 |

---

## 📋 檢查清單

### US1: 美股三大指數
- [x] 查詢 S&P 500
- [x] 查詢那斯達克
- [x] 查詢費城半導體
- [x] 中文條列式
- [x] 錯誤處理
- [x] 集成測試

### US2: 個股查詢
- [x] 價格數據
- [x] 新聞摘要
- [x] 基本面數據
- [x] 中文格式
- [x] 大小寫處理
- [ ] **快速回覆按鈕** ❌
- [x] 錯誤處理

### US3: 經濟新聞
- [x] 新聞查詢
- [x] 3～5 則新聞
- [x] 摘要翻譯
- [x] 時間標註
- [x] 來源標註
- [x] 錯誤處理

### US4: 台股關聯
- [x] 查詢相關股票
- [x] 關聯說明
- [x] 中文格式
- [ ] **快速回覆按鈕觸發** ❌
- [x] Postback 處理
- [x] 錯誤處理

---

## 📝 總結

### 已完成: 90%
- ✅ 美股三大指數 (100%)
- ✅ 經濟新聞 (100%)
- ✅ 個股查詢核心 (100%)
- ✅ 台股查詢核心 (100%)

### 待完成: 10%
- ❌ 快速回覆按鈕（US2 → US4 流程）
  - 需修改 4 個檔案
  - 預計 2-3 小時完成
  - 不影響現有功能

### 建議下一步
1. 實現快速回覆按鈕（2-3 小時）
2. 編寫集成測試（1-2 小時）
3. 部署和用戶驗收測試（1-2 小時）
