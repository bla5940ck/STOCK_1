"""
Input validation utilities.
"""

import re
from typing import Optional
from src.exceptions import ValidationError


def validate_stock_code(code: str) -> str:
    """
    Validate stock code format (1-5 uppercase letters).
    
    Args:
        code: Stock code to validate
        
    Returns:
        Uppercase stock code
        
    Raises:
        ValidationError: If code format is invalid
    """
    if not code or not isinstance(code, str):
        raise ValidationError("股票代碼不能為空", "code")

    # Convert to uppercase
    code_upper = code.strip().upper()

    # Validate format: 1-5 uppercase letters
    if not re.match(r"^[A-Z]{1,5}$", code_upper):
        raise ValidationError(
            f"股票代碼格式無效：{code}。請輸入 1-5 個英文字母。",
            "code"
        )

    return code_upper


def validate_tw_stock_code(code: str) -> str:
    """
    Validate Taiwan stock code format (4 digits).
    
    Args:
        code: Taiwan stock code
        
    Returns:
        Validated Taiwan stock code
        
    Raises:
        ValidationError: If code format is invalid
    """
    if not code or not isinstance(code, str):
        raise ValidationError("台股代碼不能為空", "tw_code")

    code_clean = code.strip()

    if not re.match(r"^[0-9]{4}$", code_clean):
        raise ValidationError(
            f"台股代碼格式無效：{code}。請輸入 4 個數字。",
            "tw_code"
        )

    return code_clean


def validate_query_text(text: str) -> str:
    """
    Validate user query text.
    
    Args:
        text: Query text
        
    Returns:
        Validated and normalized query text
        
    Raises:
        ValidationError: If text is invalid
    """
    if not text or not isinstance(text, str):
        raise ValidationError("查詢文本不能為空", "query_text")

    text_clean = text.strip()

    # Check length
    if len(text_clean) < 1 or len(text_clean) > 100:
        raise ValidationError(
            "查詢文本長度必須在 1-100 個字符之間",
            "query_text"
        )

    # Check for valid characters (alphanumeric, Chinese, basic punctuation)
    if not re.search(r"[\w\u4e00-\u9fff]", text_clean):
        raise ValidationError(
            "查詢文本必須包含有效的字符",
            "query_text"
        )

    return text_clean


def is_index_keyword(text: str) -> bool:
    """Check if text is index query keyword"""
    keywords = ["美股", "指數", "index", "indices"]
    return text.lower() in keywords


def is_news_keyword(text: str) -> bool:
    """Check if text is news query keyword"""
    keywords = ["新聞", "news", "經濟新聞", "economic"]
    return text.lower() in keywords


def is_tw_stock_keyword(text: str) -> bool:
    """Check if text is Taiwan stock query keyword"""
    keywords = ["台股", "tw", "taiwan", "台灣股票"]
    text_lower = text.lower().strip()
    
    # Direct keyword match
    if text_lower in keywords:
        return True
    
    # Check if it's a Taiwan stock name or code
    if is_tw_stock_code_or_name(text_lower):
        return True
    
    return False


def is_tw_stock_code_or_name(text: str) -> bool:
    """
    Check if text is a Taiwan stock code or company name.
    
    Args:
        text: Stock code (e.g., "2330") or company name (e.g., "台積電")
        
    Returns:
        True if it's a valid Taiwan stock code or name
    """
    from src.integrations.tw_stock_integration import TaiwanStockClient
    
    resolved = TaiwanStockClient.resolve_tw_stock_code(text)
    return resolved is not None


def detect_query_type(text: str) -> Optional[str]:
    """
    Detect query type from user text.
    
    Args:
        text: User input text
        
    Returns:
        Query type: "index", "stock", "news", "tw_stock", or None if not recognized
    """
    text_lower = text.lower().strip()

    if is_index_keyword(text_lower):
        return "index"

    if is_news_keyword(text_lower):
        return "news"

    # Check for Taiwan stock before US stock
    if is_tw_stock_keyword(text_lower):
        return "tw_stock"

    # Try to validate as US stock code
    try:
        validate_stock_code(text_lower)
        return "stock"
    except ValidationError:
        pass

    return None
