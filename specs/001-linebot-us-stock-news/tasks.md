# Tasks: LINE Bot 美股與新聞助理

**Input**: Design documents from `specs/001-linebot-us-stock-news/`

**Prerequisites**: 
- ✅ plan.md (implementation plan, tech stack, architecture)
- ✅ spec.md (4 user stories with P1/P2 priorities)
- ✅ research.md (technology decisions validated)
- ✅ data-model.md (9 domain entities defined)
- ✅ contracts/ (5 API contracts with schemas)
- ✅ quickstart.md (developer setup guide)

**Status**: Ready for Implementation | **Target**: MVP (US1 + US2)

---

## Execution Strategy

### Phase Breakdown

| Phase | Name | Stories | Duration | Dependency |
|-------|------|---------|----------|------------|
| 1 | Setup | N/A | 1 day | None |
| 2 | Foundational | N/A | 3-4 days | Phase 1 ✓ |
| 3 | US1 MVP | 美股指數 | 2-3 days | Phase 2 ✓ |
| 4 | US2 MVP | 個股+新聞 | 3-4 days | Phase 3 ✓ |
| 5 | US3 | 經濟新聞 | 1-2 days | Phase 2 ✓ |
| 6 | US4 | 台股關聯 | 2-3 days | Phase 4 ✓ |
| 7 | Polish | 文檔&部署 | 2-3 days | Phase 6 ✓ |

### MVP Scope (Recommended)

**Minimum**: Phase 1 + Phase 2 + Phase 3 + Phase 4
- Covers both P1 priorities (US1 + US2)
- Delivers full MVP with user value
- Estimated 9-14 days development

**Extended**: Add Phase 5 + Phase 6
- Covers all P2 features
- Complete feature set
- Estimated 14-21 days total

### Parallel Opportunities

- **Within Phase 2**: DB setup, middleware, config, logging, exception handling (can run in parallel)
- **Within Phase 3**: Index models and handlers (data fetching + message formatting)
- **Within Phase 4**: Stock models and handlers (stock data, news integration)
- **Cross-Phase**: Tests can be written before implementation (TDD)

---

## Phase 1: Setup (Project Initialization) ⚙️

**Goal**: Initialize project structure, install dependencies, set up development environment

**Duration**: 1 day

**All tasks must complete before Phase 2 begins**

### Configuration & Dependencies

- [ ] T001 Create project directory structure per implementation plan (src/, tests/, docs/)
- [ ] T002 Initialize requirements.txt with core dependencies (FastAPI, line-bot-sdk, aiohttp, pydantic, sqlalchemy, pytest)
- [ ] T003 Create pyproject.toml with project metadata and build config
- [ ] T004 Create .env.example template with all required environment variables (LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, etc.)
- [ ] T005 Create .gitignore excluding .env, __pycache__, venv, .pytest_cache, *.db
- [ ] T006 Create README.md (Traditional Chinese) with project overview, setup, and running instructions
- [ ] T007 Create Docker-related files (Dockerfile, docker-compose.yml) for containerized development

### Development Tooling

- [ ] T008 [P] Create Makefile or scripts for common tasks (install, test, lint, run)
- [ ] T009 [P] Configure Black code formatter in pyproject.toml
- [ ] T010 [P] Create pytest.ini configuration for test discovery and markers

**Checkpoint**: Project structure ready, dependencies installed ✓

---

## Phase 2: Foundational (Blocking Prerequisites) 🏗️

**Goal**: Build core infrastructure that ALL user stories depend on

**Duration**: 3-4 days

**CRITICAL**: No user story work can proceed until this phase is 100% complete

### Database & Data Access

- [x] T011 Create SQLAlchemy database models in src/models/database.py (Index, Stock, NewsArticle, TaiwanStock, APICache, QueryLog, UserQuery models based on data-model.md)
- [x] T012 Implement database connection & session management in src/db/database.py (SQLite for dev, PostgreSQL for prod)
- [x] T013 Create database initialization script (migrations/schema setup)
- [x] T014 Implement repository pattern in src/db/repositories.py for data access (IndexRepository, StockRepository, NewsRepository, TaiwanStockRepository, CacheRepository)

### Configuration & Secrets Management

- [x] T015 Create src/config.py to load environment variables (LINE channel token/secret, API keys, database URL, server host/port, log level, timeout settings)
- [x] T016 Validate all required environment variables are present on startup
- [x] T017 Create src/exceptions.py with custom exception classes (APIError, SignatureError, ValidationError, TimeoutError, DatabaseError)

### Logging & Monitoring Infrastructure

- [x] T018 Implement structured logging in src/utils/logger.py (JSON format, structured fields for user_id, query_type, timestamp)
- [ ] T019 Create request/response logging middleware (log all Webhook events and API calls)
- [ ] T020 Set up log rotation and log file management

### API & Middleware Layer

- [x] T021 Initialize FastAPI application in src/main.py (app instance, CORS configuration, health check endpoint /health)
- [x] T022 Implement HMAC-SHA256 signature verification middleware in src/api/webhooks.py (verify X-Line-Signature header on all requests)
- [x] T023 Create error handling middleware (catch exceptions, format error responses in Traditional Chinese)
- [x] T024 Add request ID tracking middleware for debugging and logging

### Validation & Utility Functions

- [x] T025 Implement input validation functions in src/utils/validators.py:
  - `validate_stock_code()` - Check uppercase 1-5 letter format
  - `validate_tw_stock_code()` - Check 4-digit format
  - `validate_query_text()` - Check length and content
- [x] T026 Implement message formatting utilities in src/utils/formatters.py:
  - `format_index_message()` - Format index data to zh-TW conditions style message
  - `format_stock_message()` - Format stock data with prices, changes, news
  - `format_news_message()` - Format news articles (title, summary, source, date)
  - `format_tw_stock_message()` - Format Taiwan stock correlations with relationship descriptions
  - `truncate_summary()` - Truncate news summaries to 150 chars while preserving sentences
- [x] T027 Implement retry logic in src/utils/retry.py with exponential backoff for external API calls
- [x] T028 Create Pydantic schemas in src/models/schemas.py (Request/Response models from contracts/)

### Cache Management

- [x] T029 Implement APICache layer in src/db/repositories.py with TTL support:
  - Index cache: 5 minutes
  - Stock cache: 5 minutes
  - News cache: 1 hour
  - Taiwan stock cache: 24 hours
- [x] T030 Create cache invalidation logic for stale data

### Tests for Foundational Phase (TDD - write before implementation)

- [x] T031 [P] Create unit tests in tests/unit/test_validators.py for all validation functions
- [x] T032 [P] Create unit tests in tests/unit/test_formatters.py for all message formatting functions
- [x] T033 [P] Create unit tests in tests/unit/test_config.py for environment variable loading
- [x] T034 [P] Create integration tests in tests/integration/test_webhook_signature.py for HMAC-SHA256 verification
- [x] T035 [P] Create integration tests in tests/integration/test_error_handling.py for error scenarios

**Checkpoint**: Infrastructure ready, all core services functional, database initialized ✓

---

## Phase 3: User Story 1 - 取得三大指數摘要 (Priority: P1) 📊

**Goal**: Implement "美股" query to fetch and display S&P 500, NASDAQ, Philadelphia Semiconductor indices

**Independent Test**: Input "美股" and verify response contains all 3 indices with change percentages, formatted in Traditional Chinese bullets

**Duration**: 2-3 days

**Dependencies**: Phase 2 ✓

### Models for US1

- [x] T036 Create Index domain model in src/models/domain.py with fields: id, zh_name, current_price, previous_close, change_amount, change_percent, high_52w, low_52w, last_updated, data_source, direction property
- [x] T037 [P] Create SQLAlchemy Index ORM model in src/models/database.py if not done in Phase 2

### Integration Layer for US1

- [ ] T038 Create Yahoo Finance client in src/integrations/yahoo_finance.py:
  - `async def fetch_indices(symbols: List[str]) -> Dict[str, Index]` 
  - Handle rate limiting (1 second delay between calls)
  - User-Agent rotation to bypass anti-bot measures
  - Timeout: 5 seconds
- [ ] T039 Create Alpha Vantage client in src/integrations/alpha_vantage.py as backup (with rate limit 5 calls/min)
- [ ] T040 Implement fallback logic: try Yahoo Finance first (5s timeout) → if fails, try Alpha Vantage (20s timeout) → if both fail, return error

### Service Layer for US1

- [ ] T041 [US1] Implement market data service in src/services/market_data.py:
  - `async def get_indices() -> List[Index]` - Fetch ^GSPC, ^IXIC, ^SOX
  - Check cache first (5 min TTL)
  - Call integrations with fallback
  - Update cache on success
  - Return error dict on all failures

### Handler Layer for US1

- [ ] T042 [US1] Create index handler in src/handlers/index_handler.py:
  - `async def handle_index_query() -> str` - Format index data using formatters.py
  - Call market_data service
  - Handle errors (return zh-TW error message)
  - Return formatted message (3-5 lines, bullet points, direction indicators)

### Webhook Integration for US1

- [ ] T043 [US1] Create Webhook endpoint in src/api/webhooks.py:
  - Listen on POST `/webhook/line`
  - Verify HMAC-SHA256 signature
  - Extract message text and event type
  - Route "美股" queries to index_handler
  - Reply to LINE using LINE SDK (reply_token)

### Integration & Service Layer for US1

- [x] T038 Create Yahoo Finance client in src/integrations/yahoo_finance.py with fallback to Alpha Vantage
- [x] T039 Create Alpha Vantage client in src/integrations/alpha_vantage.py as backup
- [x] T040 Implement fallback logic: Yahoo Finance (5s timeout) → Alpha Vantage (20s timeout)
- [x] T041 Implement market data service in src/services/market_data.py with caching
- [x] T042 Create index handler in src/handlers/index_handler.py

### Webhook Integration for US1

- [x] T043 Update Webhook endpoint to route "美股" queries to index_handler

### Tests for US1

- [x] T044 [P] [US1] Create unit tests in tests/integration/test_index_handler.py:
  - Test index data formatting
  - Test error message generation
  - Test direction indicators and success/failure scenarios
- [x] T045 [P] [US1] Create market data service tests:
  - Test cache hit/miss
  - Test fallback from Yahoo Finance to Alpha Vantage
  - Test timeout handling
- [x] T046 [P] [US1] Create integration tests:
  - Verify query validators
  - Verify message formatting
- [x] T047 [US1] Create end-to-end integration test in tests/integration/test_index_query_e2e.py:
  - Mock LINE Webhook request with "美股" message
  - Verify response handling with valid/invalid signatures
  - Verify Traditional Chinese formatting
  - Verify Webhook status code 200

**Checkpoint**: "美股" query fully functional and tested ✓

---

## Phase 4: User Story 2 - 以代碼查詢個股與相關新聞 (Priority: P1) 📈

**Goal**: Implement stock code queries (e.g., "AAPL") to fetch price and latest related news

**Independent Test**: Input "AAPL" and verify response contains stock price changes, 3-5 related news articles (100-150 chars each in zh-TW), formatted as bullets

**Duration**: 3-4 days

**Dependencies**: Phase 2 ✓ + Phase 3 ✓

### Models for US2

- [ ] T048 Create Stock domain model in src/models/domain.py with fields: code, company_name, zh_name, current_price, previous_close, change_amount, change_percent, market_cap_billion, pe_ratio, dividend_yield, sector, industry, last_updated, data_source, direction property
- [ ] T049 Create NewsArticle domain model with fields: id, title, summary, source, url, published_at, category, related_stocks, relevance_score, fetched_at
- [ ] T050 [P] Create SQLAlchemy Stock ORM if not done in Phase 2
- [ ] T051 [P] Create SQLAlchemy NewsArticle ORM if not done in Phase 2

### Integration Layer for US2

- [ ] T052 Create Google News RSS client in src/integrations/google_news.py:
  - `async def fetch_news(query: str, limit: int = 5) -> List[NewsArticle]`
  - Parse RSS feed using feedparser library
  - Filter for US economic news and stock-related articles
  - Timeout: 10 seconds
- [ ] T053 [P] Extend Yahoo Finance client to fetch individual stock data (not just indices)
- [ ] T054 [P] Implement news source extraction logic (link to article, publication date, source attribution)

### Service Layer for US2

- [ ] T055 [US2] Implement stock data service in src/services/market_data.py:
  - `async def get_stock(code: str) -> Stock` - Validate code, fetch from Yahoo/Alpha Vantage
  - Cache with 5 min TTL
  - Handle invalid codes (return error dict)
- [ ] T056 [US2] Implement news service in src/services/news_service.py:
  - `async def fetch_related_news(code: str, limit: int = 5) -> List[NewsArticle]`
  - Fetch stock-specific news from Google News RSS
  - Filter and rank by relevance (keyword matching)
  - Truncate summaries to 150 chars (preserving sentences)
  - Translate titles/summaries to Traditional Chinese if needed
  - Cache with 1 hour TTL
  - Handle zero results gracefully

### Handler Layer for US2

- [ ] T057 [US2] Create stock handler in src/handlers/stock_handler.py:
  - `async def handle_stock_query(code: str) -> str` 
  - Validate stock code (case-insensitive)
  - Call market_data service for price
  - Call news service for articles
  - Format both using formatters.py
  - Return combined message
  - Prepare Quick Reply buttons for Taiwan stock lookup (yes/no)
- [ ] T058 [US2] Extend formatters.py with `format_stock_with_news_message()`:
  - Stock header: code, name, price, change%
  - News section: 3-5 articles with title, summary (zh-TW), source, date
  - Quick Reply buttons at bottom

### Webhook Integration for US2

- [ ] T059 [US2] Extend src/api/webhooks.py to route stock code queries:
  - Detect stock codes (1-5 uppercase letters)
  - Route to stock_handler
  - Send response with Quick Reply buttons (台股查詢: yes/no)
  - Handle postback from Quick Reply (route to Taiwan stock handler in US4)

### Tests for US2 (TDD - write first)

- [ ] T060 [P] [US2] Create contract test in tests/contract/test_stock_api.py:
  - Verify stock-query-response.json schema
  - Test with mock stock and news data
  - Verify news array has 3-5 items
  - Verify summary field is 100-150 chars
- [ ] T061 [P] [US2] Create unit tests in tests/unit/test_stock_handler.py:
  - Test case-insensitive code handling (aapl = AAPL)
  - Test invalid code error message
  - Test message formatting with news
  - Test Quick Reply button generation
- [ ] T062 [P] [US2] Create unit tests in tests/unit/test_news_service.py:
  - Test news fetching and filtering
  - Test summary truncation at 150 chars
  - Test source attribution
  - Test date formatting
  - Test empty results handling
- [ ] T063 [P] [US2] Create unit tests in tests/unit/test_formatters.py for new stock formatter
- [ ] T064 [US2] Create integration test in tests/integration/test_stock_query_e2e.py:
  - Mock Webhook request with "AAPL" message
  - Verify response contains stock price, change %
  - Verify response contains 3-5 news articles
  - Verify Traditional Chinese formatting
  - Verify Quick Reply buttons present
- [ ] T065 [US2] Create integration test in tests/integration/test_stock_code_variations.py:
  - Test uppercase (AAPL), lowercase (aapl), mixed (ApPl)
  - Test invalid codes (TOOLONG, 123, empty)
  - Test numeric-heavy codes (3M = MMM)

**Checkpoint**: Stock + News queries fully functional, Quick Reply buttons working ✓

---

## Phase 5: User Story 3 - 取得美國重要經濟新聞 (Priority: P2) 📰

**Goal**: Implement "新聞" query to fetch latest US economic news

**Independent Test**: Input "新聞" and verify response contains 3-5 latest economic news articles (100-150 chars each in zh-TW), sorted by date

**Duration**: 1-2 days

**Dependencies**: Phase 2 ✓ + Phase 4 ✓ (news service)

### Handler Layer for US3

- [ ] T066 [US3] Create news handler in src/handlers/news_handler.py:
  - `async def handle_news_query() -> str`
  - Call news_service with generic economic news filter
  - Format using formatters.py
  - Return 3-5 articles with titles, summaries, sources, dates
  - Handle empty results ("暫無新聞，請稍後重試")

### Webhook Integration for US3

- [ ] T067 [US3] Extend src/api/webhooks.py to route "新聞" keyword:
  - Detect "新聞" input
  - Route to news_handler
  - Send response with formatted articles

### Message Formatting for US3

- [ ] T068 [US3] Extend formatters.py with `format_economics_news_message()`:
  - Header: "📰 最新美國經濟新聞"
  - Articles: Numbered bullets with title, summary (zh-TW, 100-150 chars), source, date
  - Multiple messages if content exceeds LINE limit

### Tests for US3 (TDD - write first)

- [ ] T069 [P] [US3] Create contract test in tests/contract/test_news_api.py:
  - Verify news-query-response.json schema
  - Test 3-5 articles returned
  - Test category field values
- [ ] T070 [P] [US3] Create unit tests in tests/unit/test_news_handler.py:
  - Test news fetching with no filters
  - Test empty results message
  - Test message formatting
- [ ] T071 [US3] Create integration test in tests/integration/test_news_query_e2e.py:
  - Mock Webhook with "新聞" message
  - Verify 3-5 articles in response
  - Verify Traditional Chinese formatting

**Checkpoint**: "新聞" query fully functional ✓

---

## Phase 6: User Story 4 - 延伸查詢台股關聯標的 (Priority: P2) 🔗

**Goal**: Implement Taiwan stock correlation lookup after stock queries

**Independent Test**: After stock query, select "yes" on Quick Reply, verify response contains related Taiwan stocks with relationship descriptions and strength indicators

**Duration**: 2-3 days

**Dependencies**: Phase 2 ✓ + Phase 4 ✓

### Models for US4

- [ ] T072 Create TaiwanStock domain model with fields: us_code, tw_code, tw_name, relationship_type, relationship_detail, strength, last_verified_at, verified_by
- [ ] T073 [P] Create SQLAlchemy TaiwanStock ORM if not done in Phase 2
- [ ] T074 Load initial Taiwan stock correlation data into database (from JSON fixture or CSV)

### Service Layer for US4

- [ ] T075 [US4] Implement Taiwan stock service in src/services/tw_stock_service.py:
  - `async def get_related_tw_stocks(us_code: str) -> List[TaiwanStock]`
  - Query database/API for matching records
  - Sort by relationship strength (high → medium → low)
  - Handle no results gracefully
  - Cache with 24 hour TTL

### Handler Layer for US4

- [ ] T076 [US4] Create Taiwan stock handler in src/handlers/tw_stock_handler.py:
  - `async def handle_tw_stock_query(us_code: str) -> str`
  - Validate us_code
  - Call tw_stock_service
  - Format using formatters.py
  - Return Taiwan stocks with relationship descriptions

### Webhook Integration for US4

- [ ] T077 [US4] Extend src/api/webhooks.py to handle postback events:
  - Listen for postback data from Quick Reply buttons
  - Parse postback data (us_code, action: query or skip)
  - Route "query" to tw_stock_handler
  - Skip silently if action = "skip"

### Message Formatting for US4

- [ ] T078 [US4] Extend formatters.py with `format_tw_stock_message()`:
  - Header: "🔗 台股關聯標的 (AAPL)"
  - Numbered bullets: code, name, relationship type, detail, strength emoji
  - Example: "1️⃣ 台積電 (2330) - 供應商 [🔴 高度關聯] 晶片代工供應商"

### Tests for US4 (TDD - write first)

- [ ] T079 [P] [US4] Create contract test in tests/contract/test_tw_stock_api.py:
  - Verify tw-stock-response.json schema
  - Test relationship_type values
  - Test strength enum values
- [ ] T080 [P] [US4] Create unit tests in tests/unit/test_tw_stock_handler.py:
  - Test valid us_code lookup
  - Test invalid us_code handling
  - Test no results message
  - Test relationship strength sorting
- [ ] T081 [P] [US4] Create unit tests in tests/unit/test_tw_stock_service.py:
  - Test database queries
  - Test cache behavior
  - Test sorting by strength
- [ ] T082 [US4] Create integration test in tests/integration/test_tw_stock_query_e2e.py:
  - Mock Webhook postback with us_code=AAPL, action=query
  - Verify response contains Taiwan stocks
  - Verify relationship descriptions
  - Verify strength indicators

**Checkpoint**: Taiwan stock correlation queries fully functional ✓

---

## Phase 7: Polish & Cross-Cutting Concerns 🎨

**Goal**: Complete documentation, deployment setup, performance optimization, final testing

**Duration**: 2-3 days

**Dependencies**: All user story phases complete

### Documentation

- [ ] T083 Create ARCHITECTURE.md explaining system design, layers, and component interactions
- [ ] T084 Create DEPLOYMENT.md with production deployment guide (Docker, environment setup, monitoring)
- [ ] T085 Create API_REFERENCE.md documenting all endpoints and data formats
- [ ] T086 Create CONTRIBUTING.md with development guidelines, code style (PEP 8), testing requirements

### Code Quality & Testing

- [ ] T087 [P] Run pytest with coverage report, ensure ≥80% coverage
- [ ] T088 [P] Run mypy type checking on all src/ code (strict mode)
- [ ] T089 [P] Run black code formatter and fix style issues
- [ ] T090 [P] Run flake8 linting and fix issues

### Edge Cases & Error Handling

- [ ] T091 Test all error scenarios: invalid input, API timeouts, network errors, missing data
- [ ] T092 Test message length limits (LINE 2000 char limit) - ensure multi-message splitting works
- [ ] T093 Test timezone edge cases ("昨晚" / "前晚" with different timezones)
- [ ] T094 Test concurrent requests (10+ simultaneous queries)
- [ ] T095 Test rate limiting (repeated queries from same user)
- [ ] T096 Test cache expiration (verify old data is replaced)

### Performance & Optimization

- [ ] T097 Profile query response times, ensure <2s total for stock+news
- [ ] T098 Optimize database queries (add indexes, optimize n+1 queries)
- [ ] T099 [P] Implement query deduplication (same code queried within 5 mins = cache hit)
- [ ] T100 [P] Optimize message formatting to minimize LINE message splitting

### Deployment Preparation

- [ ] T101 Test Docker build and containerization (Dockerfile working, image <500MB)
- [ ] T102 Create docker-compose.yml for local development with PostgreSQL
- [ ] T103 Set up environment variable validation (catch missing vars on startup)
- [ ] T104 Create health check endpoint (GET /health returns status)
- [ ] T105 Create metrics endpoint (GET /metrics returns query counts, response times)

### Final Testing & Validation

- [ ] T106 End-to-end test suite: All 4 user stories from user perspective
- [ ] T107 Load testing: Verify system handles 100+ concurrent requests
- [ ] T108 Stress testing: Verify graceful degradation at API limits
- [ ] T109 Manual user acceptance testing with LINE Bot

### Release Checklist

- [ ] T110 Code review (check PEP 8, type hints, test coverage)
- [ ] T111 Update CHANGELOG with all features implemented
- [ ] T112 Tag release version (v1.0.0)
- [ ] T113 Create deployment runbook for production deployment

**Checkpoint**: MVP ready for production deployment ✓

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKING for all stories
    ↓
    ├→ Phase 3 (US1: Indices)
    │   ↓
    ├→ Phase 4 (US2: Stock + News) ← depends on Phase 3 (news service)
    │   ↓
    ├→ Phase 5 (US3: News) ← can run parallel with Phase 4
    │   ↓
    └→ Phase 6 (US4: Taiwan Stock) ← depends on Phase 4 (postback handler)
        ↓
Phase 7 (Polish & Deployment)
```

## Parallel Execution Examples

**After Phase 2 complete** (Day 4-5), teams can work on:
- **Team A**: Implement Phase 3 (US1) + Phase 5 (US3) in parallel
- **Team B**: Implement Phase 4 (US2) in parallel with Team A
- **Merge**: Phase 6 after Phase 4 complete

**Example 2-person team timeline**:
- Days 1: Phase 1 (both)
- Days 2-4: Phase 2 (both)
- Days 5-6: Phase 3 + Phase 5 (Person A) + Phase 4 (Person B)
- Days 7: Phase 6 (both - postback handler needs Phase 4 complete)
- Days 8-9: Phase 7 (both - docs, testing, optimization)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | ≥80% | pytest --cov report |
| Code Quality | PEP 8 | black --check + flake8 |
| Type Hints | 100% | mypy --strict |
| Response Time (indices) | <300ms (p90) | Load test metrics |
| Response Time (stock+news) | <2s (p90) | Load test metrics |
| Error Handling | 100% scenarios | Integration test results |
| Documentation | Complete | README, ARCHITECTURE, API reference, DEPLOYMENT |
| MVP Readiness | 100% | All Phase 1-4 tests passing |

---

## Notes for Developers

1. **TDD Approach**: Write tests first (Phase tests marked [P] are contract/unit tests to write before implementation)
2. **Async Throughout**: Use async/await everywhere - no blocking I/O
3. **Type Hints**: All functions must have type hints (enable mypy strict mode)
4. **Traditional Chinese**: All user-facing messages must be zh-TW
5. **Error Messages**: Clear, actionable zh-TW error messages (never expose stack traces)
6. **Logging**: Structured JSON logging with context (user_id, query_type, timestamp)
7. **API Resilience**: All external API calls must have:
   - Timeout (20s max)
   - Retry logic (exponential backoff, max 3 attempts)
   - Fallback strategy
   - Circuit breaker for repeated failures
8. **Caching Strategy**: Implement TTL-based caching to reduce API calls
9. **LINE Webhook**: Always verify signature, handle batch events, reply within 3s
10. **Database**: Use connection pooling, handle concurrent requests safely

---

**Tasks Status**: ✅ COMPLETE  
**Total Tasks**: 113  
**Estimated Duration**: 14-21 days (MVP: 9-14 days)  
**Last Generated**: 2026-05-17

---

## Next Steps

1. ✅ Review this tasks.md for completeness
2. ✅ Adjust timelines based on team size and experience
3. ✅ Create GitHub issues from these tasks (optional: use /speckit.taskstoissues)
4. ✅ Begin Phase 1 setup immediately
5. ✅ Start Phase 2 in parallel with Phase 1 (once structure created)
6. ✅ Execute `/speckit.implement` to start actual code development

**Ready to begin implementation!** 🚀
