# Implementation Plan: LINE Bot 美股與新聞助理

**Branch**: `001-run-feature-hook` | **Date**: 2026-05-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-linebot-us-stock-news/spec.md`

## Summary

LINE Bot 美股與新聞助理是一款實時財務查詢工具，提供美股三大指數、個股行情、經濟新聞與台股關聯標的查詢。採用 Python 3.11 + FastAPI 實現高併發、非同步的 Webhook 路由；所有 LINE Webhook 請求經由 HMAC-SHA256 簽章驗證；針對外部 API（Yahoo Finance、Alpha Vantage、Google News RSS）實作嚴格的超時控制（20s timeout）與優雅降級機制。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 
- FastAPI（Web Framework 用於高併發 Webhook 路由）
- line-bot-sdk（LINE Messaging API 官方 SDK）
- aiohttp 或 httpx（非同步 HTTP 客戶端，用於外部 API 調用）
- pydantic（資料驗證與序列化）
- SQLAlchemy（ORM，用於快取與數據持久化）

**Storage**: 
- Primary: PostgreSQL 或 SQLite（台股關聯標的對照表、查詢日誌）
- Cache: Redis（optional，加速頻繁查詢）

**Testing**: pytest + pytest-asyncio（非同步單元與整合測試）

**Target Platform**: Linux server（Ubuntu 20.04+、Docker 容器化）

**Project Type**: Web service（LINE Webhook 異步處理服務）

**Performance Goals**: 
- 指數查詢：<300ms（90th percentile）
- 個股 + 新聞查詢：<2 秒（總耗時）
- 並發處理：≥100 req/s
- LINE ACK：<500ms

**Constraints**: 
- Webhook ACK response：<500ms（LINE 伺服器硬限制）
- 外部 API 調用超時：20 秒上限
- 訊息回覆延遲：<3 秒（用戶體驗目標）
- 資料新鮮度：指數/個股 5 分鐘內、新聞 <1 小時

**Scale/Scope**: 
- 預期日活：1,000～10,000 用戶
- 查詢峰值：100～500 qps
- 初版代碼規模：3,000～5,000 LOC

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **I. Reliability & Data Integrity (NON-NEGOTIABLE)**
- 所有金融資料在展示前需驗證（來源確認、資料完整性檢查）✓
- Webhook 請求簽章驗證（HMAC-SHA256）✓
- 降級策略：API 超時 → 清晰錯誤回覆，不返回過期資料 ✓
- **Status**: PASS

✅ **II. Responsive Performance**
- 技術方案：FastAPI + 非同步 asyncio 實現全非同步 I/O ✓
- LINE ACK 目標：<500ms ✓
- 指數查詢目標：<300ms（規格內） ✓
- **Status**: PASS

✅ **IV. Financial Data Security (NON-NEGOTIABLE)**
- HMAC-SHA256 簽章驗證（LINE 官方 Webhook 安全機制）✓
- API 認證：環境變數管理（不存儲代碼中）✓
- 傳輸安全：TLS 1.2+（HTTPS）✓
- **Status**: PASS

✅ **V. Test-First Development (NON-NEGOTIABLE)**
- 單元測試覆蓋率目標：80% ✓
- 整合測試：Webhook、外部 API、資料轉換 ✓
- **Status**: PASS

✅ **VI. Clear Documentation & Transparency**
- API 文件：FastAPI Swagger 自動生成 ✓
- 新聞摘要邏輯透明（標示來源、發布時間）✓
- README zh-TW、API 文件英文 ✓
- **Status**: PASS

✅ **VII. Modularity & Extensibility**
- 模組化設計：API、Handlers、Services、Integrations、Models ✓
- DI（Dependency Injection）便於切換實現 ✓
- **Status**: PASS

**Overall Gate Status**: ✅ PASSED - 設計符合憲法所有原則

## Project Structure

### Documentation (this feature)

```text
specs/001-linebot-us-stock-news/
├── plan.md                      # This file (implementation plan)
├── research.md                  # Phase 0 output (research findings)
├── data-model.md                # Phase 1 output (domain entities)
├── quickstart.md                # Phase 1 output (quick start guide)
├── contracts/                   # Phase 1 output (API contracts)
│   ├── webhook-payload.json
│   ├── index-query-response.json
│   ├── stock-query-response.json
│   ├── news-query-response.json
│   └── tw-stock-response.json
└── spec.md                      # Original specification
```

### Source Code (repository root - Web Service Structure)

```text
linebot-us-stock/
├── src/
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration & environment
│   ├── api/
│   │   ├── __init__.py
│   │   └── webhooks.py              # LINE Webhook endpoint + signature verification
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── index_handler.py         # 「美股」指數查詢邏輯
│   │   ├── stock_handler.py         # 股票代碼查詢 + 新聞綁定
│   │   ├── news_handler.py          # 「新聞」經濟新聞查詢
│   │   └── tw_stock_handler.py      # 台股關聯標的查詢
│   ├── services/
│   │   ├── __init__.py
│   │   ├── market_data.py           # Yahoo Finance / Alpha Vantage API wrapper
│   │   ├── news_service.py          # Google News RSS 抓取與摘要
│   │   └── tw_stock_service.py      # 台股關聯標的查詢
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── domain.py                # Domain entities (Index, Stock, News, etc.)
│   │   └── database.py              # SQLAlchemy ORM models
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── yahoo_finance.py         # Yahoo Finance API client
│   │   ├── alpha_vantage.py         # Alpha Vantage API client
│   │   ├── google_news.py           # Google News RSS client
│   │   └── line_api.py              # LINE Messaging API wrapper
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py            # Input validation (stock codes, keywords)
│   │   ├── formatters.py            # Traditional Chinese message formatting
│   │   ├── logger.py                # Structured logging
│   │   ├── retry.py                 # Retry logic with exponential backoff
│   │   └── errors.py                # Custom exception types
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py              # Database connection & session management
│   │   └── repositories.py          # Data access layer
│   └── exceptions.py                # Global exception definitions
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_validators.py
│   │   ├── test_formatters.py
│   │   ├── test_handlers.py
│   │   ├── test_services.py
│   │   └── test_integrations.py
│   ├── integration/
│   │   ├── test_webhook_routes.py   # Webhook integration tests
│   │   ├── test_api_integrations.py # External API integration tests
│   │   └── test_end_to_end.py       # End-to-end user flows
│   ├── fixtures/
│   │   ├── mock_api_responses.py
│   │   └── sample_data.py
│   └── conftest.py                  # pytest configuration & fixtures
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata & build config
├── Dockerfile                       # Docker container definition
├── docker-compose.yml               # Local development stack
├── .env.example                     # Environment variables template
├── .gitignore
├── README.md                        # Project documentation (zh-TW)
├── ARCHITECTURE.md                  # Technical architecture details
├── DEPLOYMENT.md                    # Deployment guide
└── CONTRIBUTING.md                  # Development guidelines (PEP 8, code style)
```

**Structure Decision**: Web service (Option 2) - 單一後端服務，無前端。採用層狀架構：
- **API Layer**: Webhook 路由 + 簽章驗證
- **Handler Layer**: 業務邏輯分流（指數、個股、新聞、台股）
- **Service Layer**: 資料查詢與業務規則
- **Integration Layer**: 外部 API 客戶端（Yahoo Finance、Google News 等）
- **Model Layer**: Pydantic schemas + SQLAlchemy ORM
- **Database Layer**: Repository pattern 用於資料存取

## Key Design Decisions

### 1. 非同步架構（Async-First）
- **FastAPI** + **asyncio** 實現全非同步 I/O
- 理由：提升併發能力、減少伺服器資源、適應 Webhook 高峰流量
- 外部 API：aiohttp / httpx async client

### 2. HMAC-SHA256 簽章驗證
- 驗證所有 Webhook 來自 LINE 伺服器
- 在 FastAPI middleware 實現（提前攔截無效請求）

### 3. 資料來源優先級
- **首選**: Yahoo Finance API（免費、穩定、覆蓋廣）
- **備選**: Alpha Vantage API
- **降級策略**: 兩者皆失敗 → 清晰錯誤訊息，不返回過期資料

### 4. 新聞摘要生成
- Google News RSS（無認證）+ 自動摘要（100～150 字）
- 標示來源、發布時間、關聯股票代碼

### 5. 台股關聯標的查詢
- **初版**: 固定對照表（SQLite / JSON）
- **長期**: 實時 API 查詢（供應鏈資料商）
- 使用 DI 便於後續切換實現

### 6. 錯誤處理與降級
- 所有外部 API：20 秒 timeout 限制
- 超時 / 失敗 → 記錄日誌 + 回覆清晰錯誤訊息
- 不緩存過期資料（避免誤導投資決策）

### 7. 程式碼品質保障
- **PEP 8** 風格指南完全遵循
- **Type Hints** 100% 覆蓋（static analysis via mypy）
- **Pydantic** 驗證所有輸入 & 輸出
- **DI 容器**: FastAPI Depends
- **Test Coverage**: ≥80% 目標

---

## Phase Workflow

### Phase 0: Research (現在)
- [ ] 確認 Yahoo Finance API 與 Alpha Vantage API 的免費額度與限制
- [ ] 評估 Google News RSS vs NewsAPI 可用性與合規性
- [ ] 確認台股供應鏈資料來源與許可證
- [ ] 測試 LINE Messaging API SDK 的非同步支持
- **Deliverable**: `research.md`

### Phase 1: Design & Contracts (after Phase 0)
- [ ] 生成詳細資料模型（Domain Entities）
- [ ] 定義 API 契約與 JSON schemas
- [ ] 編寫快速開始指南（本機開發 & Docker 部署）
- [ ] Re-evaluate Constitution Check（後設計檢查）
- **Deliverables**: `data-model.md`, `contracts/`, `quickstart.md`

### Phase 2: Tasks (after Phase 1)
- 由 `/speckit.tasks` 生成依賴排序的任務清單

---

**Plan Status**: ✅ Phase 1 Kickoff Ready  
**Last Updated**: 2026-05-17
