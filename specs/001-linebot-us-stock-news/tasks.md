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

- [x] T048 Stock domain model created in src/models/domain.py
- [x] T049 NewsArticle domain model created in src/models/domain.py
- [x] T050 SQLAlchemy Stock ORM in src/models/database.py
- [x] T051 SQLAlchemy NewsArticle ORM in src/models/database.py

### Integration Layer for US2

- [x] T052 Google News RSS client in src/integrations/google_news.py
  - `async def fetch_news()` with feedparser
  - RSS parsing, category detection, relevance scoring
  - 10 second timeout compliance
- [x] T053 Yahoo Finance extended for stock data
  - `async def fetch_stock(symbol)` returning Stock object
  - Market cap, PE ratio, dividend yield extraction
- [x] T054 News source extraction with URL & attribution

### Service Layer for US2

- [x] T055 Stock data service in market_data.py
  - `get_stock(code)` with fallback logic
  - 5 min TTL caching
  - Invalid code error handling
- [x] T056 News service in src/services/news_service.py
  - `fetch_related_news(code, limit=5)` with filtering
  - Relevance ranking & keyword matching
  - 150 char summary truncation
  - 1 hour TTL caching

### Handler Layer for US2

- [x] T057 Stock handler created in src/handlers/stock_handler.py
- [x] T058 News handler created in src/handlers/news_handler.py  
- [x] T059 Extended formatters with stock & news messaging
- [x] T060 Webhook routing for stock & news queries
- [x] T061 Unit tests in tests/integration/test_stock_handler.py
- [x] T062 E2E tests in tests/integration/test_stock_query_e2e.py

**Phase 4 Complete**: Stock + News queries fully functional with 80%+ test coverage ✓

---

## Phase 5: User Story 3 - 取得美國重要經濟新聞 (Priority: P2) 📰

**Goal**: Implement "新聞" query to fetch latest US economic news

**Independent Test**: Input "新聞" and verify response contains 3-5 latest economic news articles (100-150 chars each in zh-TW), sorted by date

**Duration**: 1-2 days

**Dependencies**: Phase 2 ✓ + Phase 4 ✓ (news service)

### Handler Layer for US3

- [x] T066 News handler in src/handlers/news_handler.py (已在Phase 4完成)
- [x] T067 Webhook routing for "新聞" keyword (已在Phase 4完成)

### Message Formatting for US3

- [x] T068 format_news_message() for economic news articles
  - Header: "📰 最新美國經濟新聞"
  - Numbered bullets with title, summary (150 chars), source, date
  - Multi-message handling for LINE 2000 char limit

### Tests for US3

- [x] T069 Unit tests in tests/unit/test_news_handler.py
  - News handler success/failure scenarios
  - Empty results handling
  - Message formatting (9+ test cases)
  
- [x] T070 E2E tests in tests/integration/test_news_query_e2e.py
  - Webhook signature verification
  - Economic news fetching
  - Message formatting with sources & dates
  - Keyword detection (Chinese "新聞", English "news")
  - Service integration tests (13+ test cases)

**Phase 5 Complete**: Economic news queries fully tested ✓

**Checkpoint**: "新聞" query fully functional ✓

---

## Phase 6: User Story 4 - 延伸查詢台股關聯標的 (Priority: P2) 🔗

**Goal**: Implement Taiwan stock correlation lookup after stock queries

**Independent Test**: After stock query, select "yes" on Quick Reply, verify response contains related Taiwan stocks with relationship descriptions and strength indicators

**Duration**: 2-3 days

**Dependencies**: Phase 2 ✓ + Phase 4 ✓

### Models for US4

- [x] T072 TaiwanStock domain model (Phase 2已建)
- [x] T073 TaiwanStock SQLAlchemy ORM (Phase 2已建)
- [x] T074 TaiwanStockRepository (Phase 2已建)

### Service Layer for US4

- [x] T075 Taiwan stock service in src/services/tw_stock_service.py
  - `async def get_related_tw_stocks(us_code, limit=10)`
  - Database query with strength sorting
  - 24 hour TTL caching
  - Graceful error handling

### Handler Layer for US4

- [x] T076 Taiwan stock handler in src/handlers/tw_stock_handler.py
  - `async def handle_tw_stock_query(db, us_code)`
  - Stock code validation
  - Service integration
  - Message formatting

### Webhook Integration for US4

- [x] T077 Postback event handling in src/api/webhooks.py
  - `async def process_postback_event()`
  - Parse postback data (action, code)
  - Route tw_stock_query action to handler
  - Support skip action

### Message Formatting for US4

- [x] T078 format_tw_stock_message() in formatters.py
  - Header: 🔗 與 {code} 相關的台股標的
  - Relationship types: 供應商, 客戶, 競爭者, 產業同業, 合作夥伴
  - Strength indicator with progress bar
  - Numbered bullets with code, name, type, detail

### Tests for US4

- [x] T079 Unit tests in tests/unit/test_tw_stock_handler.py
  - Handler success/failure scenarios (5 tests)
  - Service cache & sorting tests (4 tests)
  - Relationship strength sorting

- [x] T080 E2E tests in tests/integration/test_tw_stock_query_e2e.py
  - Postback signature verification (3 tests)
  - Message formatting (4 tests)
  - Postback data parsing (2 tests)
  - Code validation (1 test)
  - Total: 10+ E2E tests

**Phase 6 Complete**: Taiwan stock correlation queries fully functional, tested ✓

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
