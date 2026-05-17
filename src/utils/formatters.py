"""
Message formatting utilities for Traditional Chinese output.
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from src.models.domain import (
    Index, Stock, NewsArticle, TaiwanStock, 
    IndexQueryResponse, StockQueryResponse, NewsQueryResponse
)


def truncate_summary(text: str, max_length: int = 150) -> str:
    """
    Truncate summary text to max length while preserving sentence boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 150 chars for news summaries)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Truncate at word/sentence boundary
    truncated = text[:max_length].rsplit("。", 1)[0] + "。"
    if len(truncated) <= max_length:
        return truncated

    return text[:max_length - 1] + "…"


def format_price_change(price: Decimal, change_percent: Decimal, direction: str = "") -> str:
    """
    Format price change information.
    
    Args:
        price: Current price
        change_percent: Percentage change
        direction: Direction indicator (↑, ↓, →)
        
    Returns:
        Formatted string: "4500.25 ↑0.45%"
    """
    symbol = "+" if change_percent > 0 else ""
    return f"{price} {direction}{symbol}{change_percent}%"


def format_index_message(indices: List[Index]) -> str:
    """
    Format index data to Traditional Chinese bullet-point message.
    
    Args:
        indices: List of Index objects
        
    Returns:
        Formatted message
        
    Example:
        📈 美股三大指數 (2026-05-17)
        • S&P 500: 4500.25 ↑0.45% (昨晚: 4480.00)
        • 那斯達克: 14200.50 ↑0.62% (昨晚: 14110.00)
        • 費城半導體: 3820.75 ↓0.15% (昨晚: 3826.50)
    """
    lines = ["📈 美股三大指數"]

    # Add date from last_updated
    if indices:
        timestamp = indices[0].last_updated.strftime("%Y-%m-%d")
        lines.append(f"({timestamp})")
        lines.append("")

    for idx in indices:
        # Build line: • Name: Price Direction Change%
        line = f"• {idx.zh_name}: {idx.current_price} {idx.direction}{idx.change_percent}%"
        line += f" (前收: {idx.previous_close})"
        lines.append(line)

    # Add footer with data source
    if indices:
        lines.append("")
        lines.append(f"📊 資料來源：{indices[0].data_source.value}")

    return "\n".join(lines)


def format_stock_message(stock: Stock, news_articles: Optional[List[NewsArticle]] = None) -> str:
    """
    Format stock data with optional news articles.
    
    Args:
        stock: Stock object
        news_articles: Optional list of NewsArticle objects (max 5)
        
    Returns:
        Formatted message
        
    Example:
        📈 AAPL - 蘋果公司
        現價: $180.50 ↑0.70% (前收: $179.25)
        市值: $2,800B | PE比: 28.5 | 股息: 0.45%
        
        📰 相關新聞:
        • 蘋果新 iPhone 發佈會確認
          蘋果公司宣佈將在下月舉辦新品發佈會...
          來源: 科技新聞 | 2026-05-17
        
        • 蘋果股價創新高
          ...
    """
    lines = []

    # Header
    company_name = stock.zh_name or stock.company_name
    lines.append(f"📈 {stock.code} - {company_name}")
    lines.append("")

    # Price info
    price_line = f"現價: ${stock.current_price} {stock.direction}{stock.change_percent}% "
    price_line += f"(前收: ${stock.previous_close})"
    lines.append(price_line)

    # Additional info
    info_parts = []
    if stock.market_cap_billion:
        info_parts.append(f"市值: ${stock.market_cap_billion}B")
    if stock.pe_ratio:
        info_parts.append(f"PE比: {stock.pe_ratio}")
    if stock.dividend_yield:
        info_parts.append(f"股息: {stock.dividend_yield}%")

    if info_parts:
        lines.append(" | ".join(info_parts))

    # News section
    if news_articles:
        lines.append("")
        lines.append("📰 相關新聞:")
        lines.append("")

        for i, article in enumerate(news_articles[:5], 1):
            lines.append(f"• {article.title}")
            summary = truncate_summary(article.summary, 150)
            lines.append(f"  {summary}")
            
            source_date = f"{article.source}"
            if article.published_at:
                date_str = article.published_at.strftime("%Y-%m-%d")
                source_date += f" | {date_str}"
            
            lines.append(f"  🔗 {source_date}")
            
            if i < len(news_articles):
                lines.append("")

    # Footer
    lines.append("")
    lines.append(f"📊 資料來源：{stock.data_source.value}")

    return "\n".join(lines)


def format_news_message(articles: List[NewsArticle]) -> str:
    """
    Format news articles in bullet-point style.
    
    Args:
        articles: List of NewsArticle objects
        
    Returns:
        Formatted message
        
    Example:
        📰 最新美國經濟新聞
        
        • 聯準會宣佈升息決定
          美國聯邦準備委員會在今日宣佈升息 0.5%，以控制通脹...
          路透社 | 2026-05-17
    """
    lines = ["📰 最新美國經濟新聞", ""]

    for i, article in enumerate(articles[:5], 1):
        lines.append(f"• {article.title}")
        summary = truncate_summary(article.summary, 150)
        lines.append(f"  {summary}")
        
        source_date = f"{article.source}"
        if article.published_at:
            date_str = article.published_at.strftime("%Y-%m-%d")
            source_date += f" | {date_str}"
        
        lines.append(f"  🔗 {source_date}")
        
        if i < len(articles):
            lines.append("")

    return "\n".join(lines)


def format_tw_stock_message(us_code: str, tw_stocks: List[TaiwanStock]) -> str:
    """
    Format Taiwan stock correlations.
    
    Args:
        us_code: US stock code
        tw_stocks: List of TaiwanStock correlations
        
    Returns:
        Formatted message
        
    Example:
        🇹🇼 與 TSLA 相關的台股標的
        
        • 台積電 (2330) - 供應商
          TSLA 晶片製造商，相關度: 85%
          
        • 聯電 (2303) - 產業競爭者
          ...
    """
    lines = [f"🇹🇼 與 {us_code} 相關的台股標的", ""]

    if not tw_stocks:
        lines.append("目前暫無相關台股資訊")
        return "\n".join(lines)

    for i, tw_stock in enumerate(tw_stocks[:10], 1):  # Max 10 stocks
        # Title line
        title = f"• {tw_stock.tw_name} ({tw_stock.tw_code})"
        
        # Relationship type mapping
        rel_type_map = {
            "supplier": "供應商",
            "customer": "客戶",
            "competitor": "競爭者",
            "industry_peer": "產業同業",
            "partner": "合作夥伴"
        }
        
        rel_type_cn = rel_type_map.get(tw_stock.relationship_type, tw_stock.relationship_type)
        title += f" - {rel_type_cn}"
        lines.append(title)
        
        # Relationship detail
        lines.append(f"  {tw_stock.relationship_detail}")
        
        # Strength indicator
        strength_pct = int(tw_stock.strength * 100)
        strength_bar = "█" * (strength_pct // 10) + "░" * (10 - strength_pct // 10)
        lines.append(f"  相關度: [{strength_bar}] {strength_pct}%")
        
        if i < len(tw_stocks):
            lines.append("")

    return "\n".join(lines)


def format_error_message(error_code: str, error_message: str, request_id: Optional[str] = None) -> str:
    """
    Format error message in Traditional Chinese.
    
    Args:
        error_code: Error code (e.g., "E001_TIMEOUT")
        error_message: Error message in Traditional Chinese
        request_id: Optional request ID for debugging
        
    Returns:
        Formatted error message
        
    Example:
        ⚠️ 查詢出錯
        
        無法連接資料來源，請稍後重試。
        
        若問題持續發生，請重新嘗試或聯絡客服。
    """
    lines = ["⚠️ 查詢出錯", ""]
    lines.append(error_message)
    lines.append("")
    lines.append("若問題持續發生，請重新嘗試或聯絡客服。")

    if request_id:
        lines.append(f"(ID: {request_id})")

    return "\n".join(lines)


def format_suggestion_message() -> str:
    """Format suggestion message with available commands"""
    lines = [
        "👋 歡迎使用美股助理！",
        "",
        "可用的查詢指令:",
        "• 「美股」- 獲得三大指數",
        "• 「AAPL」等股票代碼 - 查詢股票價格與新聞",
        "• 「新聞」- 獲得最新經濟新聞",
        "",
        "請輸入以上任一指令開始查詢。"
    ]
    return "\n".join(lines)
