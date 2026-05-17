"""
Custom exception types for the application.
"""


class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, error_code: str = "E000_UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class APIError(ApplicationError):
    """External API call error"""
    def __init__(self, message: str, error_code: str = "E001_API_ERROR"):
        super().__init__(message, error_code)


class SignatureError(ApplicationError):
    """HMAC signature verification error"""
    def __init__(self, message: str = "無法驗證簽名"):
        super().__init__(message, "E002_SIGNATURE_ERROR")


class ValidationError(ApplicationError):
    """Input validation error"""
    def __init__(self, message: str, field: str = ""):
        super().__init__(message, f"E003_VALIDATION_ERROR_{field.upper()}")


class TimeoutError(ApplicationError):
    """API timeout error"""
    def __init__(self, message: str = "API 響應超時"):
        super().__init__(message, "E004_TIMEOUT")


class DatabaseError(ApplicationError):
    """Database operation error"""
    def __init__(self, message: str):
        super().__init__(message, "E005_DATABASE_ERROR")


class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, message: str, error_code: str = "E006_NOT_FOUND"):
        super().__init__(message, error_code)


class StockNotFoundError(NotFoundError):
    """Stock code not found error"""
    def __init__(self, code: str):
        super().__init__(
            f"無法找到股票代碼 {code}，請確認代碼是否正確。",
            "E006_STOCK_NOT_FOUND"
        )


class NewsError(ApplicationError):
    """News fetching error"""
    def __init__(self, message: str = "無法獲取新聞數據"):
        super().__init__(message, "E007_NEWS_ERROR")


class ConfigError(ApplicationError):
    """Configuration error"""
    def __init__(self, message: str):
        super().__init__(message, "E008_CONFIG_ERROR")
