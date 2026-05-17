# 開發者貢獻指南

## 📖 目錄

1. [歡迎](#歡迎)
2. [開發環境設置](#開發環境設置)
3. [代碼風格](#代碼風格)
4. [測試](#測試)
5. [提交指南](#提交指南)
6. [拉取請求流程](#拉取請求流程)
7. [架構指南](#架構指南)
8. [常見任務](#常見任務)

---

## 歡迎

感謝您有興趣為 LINE 美股助理貢獻代碼！本項目歡迎所有類型的貢獻：

- 🐛 **Bug 修複**: 報告和修複已知問題
- ✨ **新功能**: 提議和實現新功能
- 📚 **文檔**: 改進文檔和示例
- 🧪 **測試**: 增加測試覆蓋
- 🎨 **改進**: 代碼優化和重構

---

## 開發環境設置

### 先決條件

- Python 3.11+
- Git 2.0+
- PostgreSQL 13+ (可選，開發時可使用 SQLite)
- Docker & Docker Compose (可選)

### 1. 克隆並設置

```bash
# 克隆項目
git clone https://github.com/your-org/us-stock.git
cd us-stock

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. 配置環境

```bash
# 複製環境文件
cp .env.example .env

# 編輯 .env
nano .env

# 最小配置 (開發)
LINE_CHANNEL_SECRET=test_secret_for_dev
LINE_CHANNEL_ACCESS_TOKEN=test_token_for_dev
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=development
```

### 3. 初始化數據庫

```bash
# 創建表
python scripts/init_db.py

# 或使用 Alembic
alembic upgrade head
```

### 4. 運行開發服務器

```bash
# 使用 Uvicorn
uvicorn src.main:app --reload

# 或使用 make
make dev
```

訪問: `http://localhost:8000/docs` (Swagger UI)

---

## 代碼風格

### Python 風格指南

我們遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)，使用 [Black](https://github.com/psf/black) 進行自動格式化。

#### 自動格式化

```bash
# 格式化所有代碼
black src tests

# 檢查格式化 (不修改)
black --check src tests

# 快速檢查 (make 命令)
make format
```

#### 類型提示

所有函數必須有類型提示。使用 `mypy` 進行檢查:

```python
# ✅ 正確
async def handle_stock_query(
    db: AsyncSession,
    stock_code: str
) -> dict:
    """Handle stock query."""
    return {"success": True, "data": []}

# ❌ 錯誤 (缺少類型)
async def handle_stock_query(db, stock_code):
    return {"success": True}
```

檢查類型:
```bash
mypy src --strict
make check-types
```

#### 代碼長度

- **最大行長**: 100 個字符 (Black 默認)
- 長字符串和 URL 可以超過限制

```python
# ✅ 正確
message = (
    "This is a very long message that needs to be split "
    "across multiple lines for readability"
)

# ❌ 錯誤
message = "This is a very long message that needs to be split across multiple lines for readability and should be on one line"
```

#### 命名慣例

```python
# 常量: 全大寫
API_TIMEOUT = 5
MAX_RETRIES = 3

# 函數和變數: snake_case
def handle_stock_query():
    pass

stock_price = 100.50

# 類: PascalCase
class MarketDataService:
    pass

# 私有方法: 單下劃線前綴
def _internal_method():
    pass
```

#### 文檔字符串

所有模塊、類和公開函數必須有 docstring:

```python
"""
Module docstring: Brief description of the module.

Extended description if needed.
"""

def fetch_stock_data(code: str) -> dict:
    """
    Fetch stock data from Yahoo Finance.
    
    Args:
        code: Stock code (e.g., "AAPL")
        
    Returns:
        Dictionary with stock data:
        - "success": bool
        - "data": Stock object or None
        - "error_message": str or None
        
    Raises:
        TimeoutError: If API request times out
        ValueError: If stock code is invalid
        
    Example:
        >>> result = await fetch_stock_data("AAPL")
        >>> if result["success"]:
        ...     print(result["data"].current_price)
    """
    pass

class MarketDataService:
    """Service for fetching market data.
    
    This service handles all interactions with external
    market data APIs and manages caching.
    """
    pass
```

### 傳統中文

- 所有用戶消息使用 **繁體中文** (Traditional Chinese)
- 代碼註解可以使用英文或中文
- 數據庫字段名使用英文，顯示名稱使用中文

```python
# ✅ 正確
message = "📈 蘋果公司股價上漲 0.70%"

# ❌ 錯誤 (簡體中文)
message = "📈 苹果公司股价上涨 0.70%"
```

---

## 測試

### 測試結構

```
tests/
├── unit/              # 單元測試
│   ├── test_validators.py
│   ├── test_formatters.py
│   └── test_handlers.py
├── integration/       # 集成測試
│   ├── test_stock_query_e2e.py
│   └── test_news_query_e2e.py
└── contract/         # API 契約測試
    └── test_contracts.py
```

### 編寫測試

所有新代碼都必須包含測試。目標: **≥95% 覆蓋率**

```python
import pytest
from src.handlers.stock_handler import handle_stock_query

class TestStockHandler:
    """Test cases for stock query handler."""
    
    @pytest.fixture
    def sample_stock(self):
        """Fixture for sample stock data."""
        return {
            "code": "AAPL",
            "current_price": 180.50,
            "change_percent": 0.70,
        }
    
    @pytest.mark.asyncio
    async def test_handle_stock_query_success(self, test_db):
        """Test successful stock query."""
        with patch("src.handlers.stock_handler.MarketDataService"):
            result = await handle_stock_query(test_db, "AAPL")
            
            assert result["success"] is True
            assert "message" in result
    
    @pytest.mark.asyncio
    async def test_handle_stock_query_invalid_code(self, test_db):
        """Test with invalid stock code."""
        result = await handle_stock_query(test_db, "TOOLONG")
        
        assert result["success"] is False
        assert result["error_code"] == "E002_INVALID_INPUT"
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定文件
pytest tests/unit/test_validators.py

# 運行特定測試
pytest tests/unit/test_validators.py::test_validate_stock_code -v

# 帶覆蓋報告
pytest --cov=src --cov-report=html

# 監視文件更改自動運行
pytest-watch

# 快速測試 (make)
make test
```

### 測試最佳實踐

1. **測試應該獨立**: 每個測試應該獨立運行
2. **使用 Fixtures**: 共享設置代碼
3. **模擬外部調用**: 使用 `unittest.mock` 或 `pytest-mock`
4. **測試邊界情況**: 有效輸入、無效輸入、空結果、錯誤
5. **描述性名稱**: 測試名稱應該清楚地說明測試內容

```python
# ❌ 不好的測試名稱
def test_handler():
    pass

# ✅ 好的測試名稱
def test_handle_stock_query_with_invalid_code_returns_error():
    pass
```

---

## 提交指南

### Git 工作流

```
main branch (生產代碼)
    ↑
develop branch (開發分支)
    ↑
feature/your-feature (功能分支)
```

### 1. 創建功能分支

```bash
# 更新 main
git checkout main
git pull origin main

# 創建功能分支
git checkout -b feature/add-new-endpoint
```

分支命名約定:
- `feature/description`: 新功能
- `bugfix/description`: Bug 修複
- `docs/description`: 文檔更新
- `refactor/description`: 代碼重構

### 2. 進行更改

```bash
# 編輯文件
nano src/handlers/new_handler.py

# 添加和提交
git add src/handlers/new_handler.py
git commit -m "Add new handler for feature X"
```

### 3. 提交消息格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**類型**:
- `feat`: 新功能
- `fix`: Bug 修複
- `docs`: 文檔
- `style`: 代碼風格 (無邏輯更改)
- `refactor`: 代碼重構
- `perf`: 性能改進
- `test`: 測試

**示例**:

```bash
# 新功能
git commit -m "feat(handlers): add Taiwan stock query handler

- Implement handle_tw_stock_query function
- Add TaiwanStockService integration
- Support postback event routing

Closes #123"

# Bug 修複
git commit -m "fix(cache): resolve cache expiration issue

The cache was not properly expiring after TTL.
Changed cache check logic to validate timestamps.

Fixes #456"

# 文檔
git commit -m "docs(api): update API reference for new endpoint"
```

---

## 拉取請求流程

### 1. 推送分支

```bash
git push origin feature/add-new-endpoint
```

### 2. 創建 Pull Request

在 GitHub 上創建 PR，提供:

- **標題**: 清晰簡潔，遵循 Conventional Commits
- **描述**: 詳細說明更改內容、為什麼進行更改
- **相關 Issue**: 鏈接相關的 Issue (#123)
- **檢查清單**:

```markdown
## 描述
簡述本 PR 的目的和更改。

## 相關 Issue
Closes #123

## 更改類型
- [ ] 新功能
- [ ] Bug 修複
- [ ] 破壞性更改
- [ ] 文檔更新

## 測試清單
- [ ] 添加了新測試
- [ ] 現有測試通過 (`pytest`)
- [ ] 代碼格式正確 (`black`)
- [ ] 類型檢查通過 (`mypy`)
- [ ] 代碼 lint 通過 (`flake8`)

## 性能影響
- [ ] 無性能影響
- [ ] 改進性能
- [ ] 可能的性能下降 (詳見描述)
```

### 3. Code Review

- 至少一位維護者要求審核
- 解決反饋
- 推送修複 (新提交)

### 4. 合併

- 評論者批准
- CI/CD 測試通過
- 合併到 `develop`

---

## 架構指南

### 添加新功能的步驟

#### 示例: 添加新查詢類型 (例如："加密貨幣")

**第 1 步**: 定義數據模型

```python
# src/models/domain.py
class Cryptocurrency(BaseModel):
    """Cryptocurrency data model."""
    code: str = Field(..., regex=r"^[A-Z]{1,5}$")
    name: str
    zh_name: str
    current_price: Decimal
    change_percent: Decimal
```

**第 2 步**: 創建集成層

```python
# src/integrations/crypto_api.py
class CryptoAPIClient:
    """Client for cryptocurrency API."""
    
    async def fetch_crypto(self, code: str) -> dict:
        """Fetch crypto price."""
        pass
```

**第 3 步**: 創建服務層

```python
# src/services/crypto_service.py
class CryptoService:
    """Service for cryptocurrency queries."""
    
    async def get_crypto(self, code: str) -> dict:
        """Get cryptocurrency data."""
        pass
```

**第 4 步**: 創建 Handler

```python
# src/handlers/crypto_handler.py
async def handle_crypto_query(db: AsyncSession, code: str) -> dict:
    """Handle crypto query."""
    pass
```

**第 5 步**: 添加路由

```python
# src/api/webhooks.py
elif detect_query_type(text) == "crypto":
    result = await handle_crypto_query(db, code)
    return result.get("message")
```

**第 6 步**: 添加測試

```python
# tests/unit/test_crypto_handler.py
# tests/integration/test_crypto_e2e.py
```

**第 7 步**: 提交 PR

### 修改現有代碼的最佳實踐

1. **向後相容**: 不要破壞現有 API
2. **遵循模式**: 遵循現有的架構模式
3. **添加測試**: 為修改添加或更新測試
4. **更新文檔**: 更新相關文檔

---

## 常見任務

### 添加新的驗證器

```python
# src/utils/validators.py
def validate_crypto_code(code: str) -> str:
    """Validate crypto code format."""
    code = code.upper().strip()
    
    if not re.match(r"^[A-Z]{1,5}$", code):
        raise ValidationError(f"Invalid crypto code: {code}")
    
    return code
```

### 添加新的格式化器

```python
# src/utils/formatters.py
def format_crypto_message(crypto: Cryptocurrency) -> str:
    """Format crypto data for LINE message."""
    lines = [
        f"💰 {crypto.zh_name} ({crypto.code})",
        f"現價: ${crypto.current_price} {crypto.direction}{crypto.change_percent}%",
    ]
    return "\n".join(lines)
```

### 添加新的緩存類型

```python
# src/utils/cache.py
class CacheKeyBuilder:
    @staticmethod
    def crypto(code: str) -> str:
        return f"crypto_{code.lower()}"

class CachePolicies:
    CRYPTO_TTL_HOURS = 1  # 1 hour TTL
```

### 運行 Linter 和 Formatter

```bash
# 格式化
black src tests

# Lint
flake8 src tests --max-line-length=100

# 類型檢查
mypy src --strict

# 所有檢查 (make)
make check

# 自動修復 (autoflake)
autoflake --in-place --remove-all-unused-imports src/**/*.py
```

### 更新依賴

```bash
# 列出過期包
pip list --outdated

# 更新包
pip install --upgrade package-name

# 更新 requirements
pip freeze > requirements.txt
```

---

## 常見問題

### Q: 如何添加環境變數?

A: 編輯 `.env.example` 並添加到 `src/config.py`:

```python
class Settings(BaseSettings):
    new_var: str = Field(default="default_value")
```

### Q: 如何添加數據庫遷移?

A: 使用 Alembic:

```bash
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

### Q: 如何運行特定的測試?

A: 使用 pytest:

```bash
pytest tests/unit/test_file.py::test_function -v
```

### Q: 如何修復代碼格式問題?

A: 運行 Black:

```bash
black src tests
```

---

## 聯絡與支持

- **問題**: 開啟 GitHub Issue
- **討論**: 使用 GitHub Discussions
- **緊急**: 提交 PR 帶 `[URGENT]` 標籤

---

感謝您的貢獻！🎉

更多信息:
- [架構文檔](./ARCHITECTURE.md)
- [API 參考](./API_REFERENCE.md)
- [部署指南](./DEPLOYMENT.md)
