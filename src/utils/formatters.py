"""
Message formatting utilities for Traditional Chinese output.
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import re
from html import unescape
from urllib.parse import urlparse
from src.models.domain import (
    Index, Stock, NewsArticle, TaiwanStock, 
    IndexQueryResponse, StockQueryResponse, NewsQueryResponse
)


def clean_html(text: str) -> str:
    """
    Clean HTML tags and entities from text.
    
    Args:
        text: Text containing HTML
        
    Returns:
        Clean text without HTML tags
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    text = unescape(text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def extract_domain(url: str) -> str:
    """
    Extract domain name from URL.
    
    Args:
        url: Full URL (e.g., https://www.example.com/article)
        
    Returns:
        Domain name (e.g., example.com)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def translate_news_text(text: str) -> str:
    """
    Translate English news text to Chinese using keyword mapping.
    
    Args:
        text: English news text
        
    Returns:
        Translated Chinese text
    """
    if not text:
        return text
    
    # Clean HTML first
    text = clean_html(text)
    
    # Company mapping
    companies = {
        "apple": "蘋果",
        "microsoft": "微軟",
        "google": "谷歌",
        "alphabet": "字母表",
        "amazon": "亞馬遜",
        "tesla": "特斯拉",
        "meta": "Meta",
        "nvidia": "英偉達",
        "jpmorgan": "摩根大通",
        "jpm": "摩根大通",
        "visa": "Visa",
        "walmart": "沃爾瑪",
        "coca-cola": "可口可樂",
        "mcdonald's": "麥當勞",
        "mastercard": "萬事達卡",
    }
    
    # Action/Verb mapping
    actions = {
        "announces": "宣佈",
        "announced": "宣佈",
        "reported": "報告",
        "reports": "報告",
        "beat": "超越",
        "beats": "超越",
        "misses": "未達",
        "acquires": "併購",
        "acquired": "併購",
        "launches": "推出",
        "launched": "推出",
        "raises": "提高",
        "raised": "提高",
        "cuts": "下調",
        "lays off": "裁員",
        "hires": "招聘",
        "surges": "飆升",
        "plummets": "暴跌",
        "gains": "上漲",
        "falls": "下跌",
    }
    
    # Quality/Descriptor mapping
    descriptors = {
        "strong": "強勁",
        "weak": "疲弱",
        "record": "創紀錄",
        "highest": "最高",
        "lowest": "最低",
        "unexpected": "意外",
        "better than expected": "好於預期",
        "worse than expected": "差於預期",
        "better-than-expected": "好於預期",
        "worse-than-expected": "差於預期",
    }
    
    # Business term mapping
    business_terms = {
        "earnings": "盈利",
        "revenue": "營收",
        "profit": "利潤",
        "loss": "虧損",
        "dividend": "股息",
        "stock": "股票",
        "share": "股份",
        "price": "價格",
        "ipo": "首次公開募股",
        "acquisition": "併購",
        "merger": "合併",
        "partnership": "合作",
        "deal": "交易",
        "quarterly": "季度",
        "annual": "年度",
        "sales": "銷售",
        "growth": "增長",
        "decline": "下降",
        "market": "市場",
        "sector": "板塊",
        "product": "產品",
        "service": "服務",
        "customer": "客戶",
        "employee": "員工",
        "supply chain": "供應鏈",
        "innovation": "創新",
        "q1": "第一季度",
        "q2": "第二季度",
        "q3": "第三季度",
        "q4": "第四季度",
    }
    
    # Product mapping
    products = {
        "iphone": "iPhone",
        "ipad": "iPad",
        "mac": "Mac",
        "windows": "Windows",
        "azure": "Azure",
        "aws": "AWS",
        "cloud": "雲服務",
        "ai": "人工智能",
        "5g": "5G",
        "chip": "晶片",
    }
    
    # Process: Replace keywords with Chinese
    result = text.lower()
    
    # Replace multi-word phrases first
    multi_word_terms = [
        ("better-than-expected", "好於預期"),
        ("worse-than-expected", "差於預期"),
        ("better than expected", "好於預期"),
        ("worse than expected", "差於預期"),
        ("supply chain", "供應鏈"),
        ("stock split", "股票分割"),
        ("product launch", "產品發布"),
        ("lay off", "裁員"),
        ("lays off", "裁員"),
    ]
    
    for english, chinese in multi_word_terms:
        result = result.replace(english, f" {chinese} ")
    
    # Replace single words
    all_mappings = {**companies, **actions, **descriptors, **business_terms, **products}
    for english, chinese in all_mappings.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(english) + r'\b'
        result = re.sub(pattern, chinese, result, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    result = ' '.join(result.split())
    
    return result


def generate_chinese_summary(title: str, summary: str) -> str:
    """
    Generate a quick Chinese translation/summary of news headline and content.
    
    Args:
        title: News title (in English)
        summary: News summary (in English)
        
    Returns:
        Quick Chinese summary
    """
    text = (title + " " + summary).lower()
    
    # Company mapping
    companies = {
        "apple": "蘋果",
        "microsoft": "微軟",
        "google": "谷歌",
        "amazon": "亞馬遜",
        "tesla": "特斯拉",
        "meta": "Meta",
        "nvidia": "英偉達",
        "jpmorgan": "摩根大通",
        "visa": "Visa",
        "walmart": "沃爾瑪",
    }
    
    # Event keywords
    events = {
        "earnings": "盈利",
        "revenue": "營收",
        "profit": "利潤",
        "beat": "超越預期",
        "miss": "未達預期",
        "acquisition": "併購",
        "merger": "合併",
        "ipo": "上市",
        "stock split": "股票分割",
        "dividend": "股息",
        "layoff": "裁員",
        "hiring": "招聘",
        "product launch": "新品發布",
        "innovation": "創新",
        "partnership": "合作",
    }
    
    # Generate summary
    company_found = None
    event_found = None
    
    for company, zh_name in companies.items():
        if company in text:
            company_found = zh_name
            break
    
    for event, zh_event in events.items():
        if event in text:
            event_found = zh_event
            break
    
    # Build summary
    if company_found and event_found:
        return f"{company_found}{event_found}相關新聞"
    elif company_found:
        return f"{company_found}相關新聞"
    elif event_found:
        return f"{event_found}相關新聞"
    else:
        # Extract first few meaningful words
        words = title.split()[:3]
        return f"{' '.join(words)}..."


def truncate_summary(text: str, max_length: int = 150) -> str:
    """
    Truncate summary text to max length while preserving sentence boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 150 chars for news summaries)
        
    Returns:
        Truncated text
    """
    # Clean HTML first
    text = clean_html(text)
    
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
        # Build line: • Name: Price Color Direction Change% (with 2 decimal places)
        change_percent_str = f"{idx.change_percent:.2f}"
        
        if idx.change_percent > 0:
            color_indicator = "🔴"  # Red for up
            direction = "↑"
        elif idx.change_percent < 0:
            color_indicator = "🟢"  # Green for down
            direction = "↓"
        else:
            color_indicator = "⚪"  # White for no change
            direction = "→"
        
        line = f"• {idx.zh_name}: {idx.current_price} {color_indicator}{direction}{change_percent_str}%"
        line += f" (昨晚: {idx.previous_close})"
        lines.append(line)

    # Add footer with data source
    if indices:
        lines.append("")
        lines.append(f"📊 資料來源：{indices[0].data_source.value}")

    return "\n".join(lines)


def format_stock_message(
    stock: Stock,
    news_articles: Optional[List[NewsArticle]] = None,
    fundamentals: Optional[dict] = None,
    quarterly_earnings: Optional[dict] = None,
) -> str:
    """
    Format stock data with optional news articles and live fundamental data.
    
    Args:
        stock: Stock object
        news_articles: Optional list of NewsArticle objects (max 5)
        fundamentals: Optional dict with live fundamentals from API
                     - Keys: 'pe_ratio', 'eps', 'dividend_yield', 'analyst_target_price', etc.
        quarterly_earnings: Optional dict with quarterly earnings data
                           - Keys: 'latest_quarter_eps', 'prev_quarter_eps', 'ytd_eps', etc.
        
    Returns:
        Formatted message
        
    Example:
        📈 AAPL - 蘋果公司
        現價: $180.50 🔴↑0.70% (前收: $179.25)
        🔓 開盤價: $179.85
        📈 最高價: $182.10
        📉 最低價: $178.50
        💼 市值: $2,800B
        📊 PE比: 28.5 (來自 Alpha Vantage)
        💵 股息殖利率: 0.45%
        
        📰 相關新聞:
        • 蘋果新 iPhone 發佈會確認
    """
    lines = []

    # Header
    company_name = stock.zh_name or stock.company_name
    lines.append(f"📈 {stock.code} - {company_name}")
    
    # Data timestamp (as per spec requirement FR-009)
    if hasattr(stock, 'last_updated') and stock.last_updated:
        data_time = stock.last_updated.strftime("%Y-%m-%d %H:%M") if isinstance(stock.last_updated, datetime) else str(stock.last_updated)
        lines.append(f"📅 數據時間: {data_time} UTC")
    else:
        lines.append(f"📅 數據時間: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")

    # Price info with color indicator (red for up, green for down)
    change_percent_str = f"{stock.change_percent:.2f}"  # Only 2 decimal places
    
    if stock.change_percent > 0:
        color_indicator = "🔴"  # Red for up
        direction = "↑"
    elif stock.change_percent < 0:
        color_indicator = "🟢"  # Green for down
        direction = "↓"
    else:
        color_indicator = "⚪"  # White for no change
        direction = "→"
    
    price_line = f"💰 現價: ${stock.current_price} {color_indicator}{direction}{change_percent_str}%"
    lines.append(price_line)
    
    lines.append(f"📍 前收: ${stock.previous_close}")

    # Market status indicator for US stocks
    from src.utils.market_hours import is_us_market_open
    market_status = is_us_market_open()
    lines.append(market_status['display_status'])
    lines.append("")

    # Price range info (open, high, low) - one per line
    if stock.open_price:
        lines.append(f"🔓 開盤價: ${stock.open_price}")
    if stock.high_price:
        lines.append(f"📈 最高價: ${stock.high_price}")
    if stock.low_price:
        lines.append(f"📉 最低價: ${stock.low_price}")

    # Additional info - one per line
    if stock.market_cap_billion:
        lines.append(f"💼 市值: ${stock.market_cap_billion}B")
    
    # Use live fundamentals data if available, otherwise fall back to stock object
    if fundamentals:
        if "pe_ratio" in fundamentals:
            lines.append(f"📊 PE比: {fundamentals['pe_ratio']:.1f}x (實時)")
        if "eps" in fundamentals:
            lines.append(f"📈 EPS: ${fundamentals['eps']:.2f} (實時)")
        if "dividend_yield" in fundamentals:
            lines.append(f"💵 股息殖利率: {fundamentals['dividend_yield']:.2f}% (實時)")
        if "analyst_target_price" in fundamentals:
            lines.append(f"🎯 分析師目標價: ${fundamentals['analyst_target_price']:.2f}")
        if "week_52_high" in fundamentals:
            lines.append(f"📍 52週高: ${fundamentals['week_52_high']:.2f}")
        if "week_52_low" in fundamentals:
            lines.append(f"📍 52週低: ${fundamentals['week_52_low']:.2f}")
    else:
        # Fallback to stock object data if available
        if stock.pe_ratio:
            lines.append(f"📊 PE比: {stock.pe_ratio}")
        if stock.dividend_yield:
            lines.append(f"💵 股息殖利率: {stock.dividend_yield}%")
    
    # Add quarterly earnings data if available
    if quarterly_earnings:
        lines.append("")
        lines.append("📅 季度盈利:")
        if "latest_quarter_date" in quarterly_earnings:
            lines.append(f"  最新季度 ({quarterly_earnings['latest_quarter_date']}):")
        if "latest_quarter_eps" in quarterly_earnings:
            lines.append(f"    季度 EPS: ${quarterly_earnings['latest_quarter_eps']:.2f}")
        if "prev_quarter_eps" in quarterly_earnings:
            lines.append(f"  上季度 EPS: ${quarterly_earnings['prev_quarter_eps']:.2f}")
        if "ytd_eps" in quarterly_earnings:
            ytd_eps = quarterly_earnings['ytd_eps']
            quarters = quarterly_earnings.get('ytd_eps_quarters', 1)
            lines.append(f"  今年 YTD EPS: ${ytd_eps:.2f} ({quarters}個季度)")

    # Note: Remove inaccurate static valuation analysis
    lines.append("")
    lines.append("ℹ️ 💡提示: 所有基本面數據來自實時 API，請查詢最新投資研報以獲得準確分析")

    # News section
    if news_articles:
        lines.append("")
        lines.append("📰 相關新聞:")
        lines.append("")

        for i, article in enumerate(news_articles[:5], 1):
            # Translate title to Chinese
            zh_title = translate_news_text(article.title)
            lines.append(f"• {zh_title}")
            
            # Translate summary to Chinese
            summary = truncate_summary(article.summary, 150)
            zh_summary = translate_news_text(summary)
            lines.append(f"  {zh_summary}")
            
            source_date = f"來源: {article.source}"
            if article.published_at:
                date_str = article.published_at.strftime("%Y-%m-%d")
                source_date += f" | {date_str}"
            
            lines.append(f"  {source_date}")
            
            if article.url:
                # Show full URL for clicking
                lines.append(f"  🔗 {article.url}")
            
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
          https://example.com/news
    """
    lines = ["📰 最新美國經濟新聞", ""]

    for i, article in enumerate(articles[:5], 1):
        # Translate title to Chinese
        zh_title = translate_news_text(article.title)
        lines.append(f"• {zh_title}")
        
        # Translate summary to Chinese
        summary = truncate_summary(article.summary, 150)
        zh_summary = translate_news_text(summary)
        lines.append(f"  {zh_summary}")
        
        source_date = f"{article.source}"
        if article.published_at:
            date_str = article.published_at.strftime("%Y-%m-%d")
            source_date += f" | {date_str}"
        
        lines.append(f"  {source_date}")
        
        if article.url:
            # Show full URL for clicking
            lines.append(f"  🔗 {article.url}")
        
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
        📅 數據時間: 2026-05-23 14:30 UTC
        
        • 台積電 (2330) - 供應商
          TSLA 晶片製造商，相關度: 85%
          
        • 聯電 (2303) - 產業競爭者
          ...
    """
    lines = [f"🇹🇼 與 {us_code} 相關的台股標的"]
    # Add data timestamp (as per spec requirement FR-009)
    lines.append(f"📅 數據時間: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")

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


def format_tw_stock_price_message(
    stock_data: dict,
    news_articles: Optional[List[NewsArticle]] = None,
    fundamentals: Optional[dict] = None,
    analyst_ratings: Optional[dict] = None,
) -> str:
    """
    Format Taiwan stock data with optional news articles and live fundamental data.
    
    Args:
        stock_data: Dict with Taiwan stock info from integration
        news_articles: Optional list of NewsArticle objects
        fundamentals: Optional dict with live fundamentals from API
                     - Keys: 'pe_ratio', 'dividend_yield', etc.
        analyst_ratings: Optional dict with analyst ratings from CNYES
                        - Keys: 'buy_count', 'hold_count', 'sell_count', 'avg_target_price'
        
    Returns:
        Formatted message
        
    Example:
        🇹🇼 2330 - 台積電
        現價: NT$2500.00 🔴↑0.80% (前收: NT$2480.00)
        開盤: NT$2490.00
        最高: NT$2510.00
        最低: NT$2475.00
        成交量: 29,500,000
        
        📊 基本面 (實時):
        P/E比: 22.5x
        股息殖利率: 2.8%
    """
    from datetime import datetime
    
    lines = []
    
    # Header
    code = stock_data.get("code", "?")
    zh_name = stock_data.get("zh_name", code)
    lines.append(f"🇹🇼 {code} - {zh_name}")
    lines.append("")
    
    # Price info
    current_price = stock_data.get("current_price", 0)
    previous_close = stock_data.get("previous_close", 0)
    change_percent = stock_data.get("change_percent", 0)
    
    # Color indicator
    change_percent_str = f"{float(change_percent):.2f}"
    if change_percent > 0:
        color_indicator = "🔴"
        direction = "↑"
    elif change_percent < 0:
        color_indicator = "🟢"
        direction = "↓"
    else:
        color_indicator = "⚪"
        direction = "→"
    
    def fmt_price(val) -> str:
        """Format price with 2 decimal places with NT$ prefix."""
        try:
            return f"NT${float(val):.2f}"
        except (TypeError, ValueError):
            return str(val)

    lines.append(f"💰 現價: {fmt_price(current_price)}")
    lines.append(f"📊 漲幅: {color_indicator}{direction}{change_percent_str}%")
    lines.append(f"📍 前收: {fmt_price(previous_close)}")
    lines.append(f"🔓 開盤: {fmt_price(stock_data.get('open_price', 0))}")
    lines.append(f"📈 最高: {fmt_price(stock_data.get('high_price', 0))}")
    lines.append(f"📉 最低: {fmt_price(stock_data.get('low_price', 0))}")
    
    # Trading volume
    volume = stock_data.get("volume", 0)
    if volume > 0:
        volume_str = f"{volume:,.0f}" if volume >= 1000 else str(volume)
        lines.append(f"📋 成交量: {volume_str}")
    
    # Add fundamental data if available
    if fundamentals:
        lines.append("")
        lines.append("📊 基本面數據 (即時 GOODINFO):")
        if "pe_ratio" in fundamentals:
            lines.append(f"  本益比 (P/E): {fundamentals['pe_ratio']:.1f}x")
        if "eps" in fundamentals:
            lines.append(f"  每股盈餘 (EPS): NT${fundamentals['eps']:.2f}")
        if "dividend_yield" in fundamentals:
            lines.append(f"  股息殖利率: {fundamentals['dividend_yield']:.2f}%")
        if "payout_ratio" in fundamentals:
            lines.append(f"  配息率: {fundamentals['payout_ratio']:.1f}%")
        if "roe" in fundamentals:
            lines.append(f"  股東權益報酬率 (ROE): {fundamentals['roe']:.1f}%")
    
    # Add analyst ratings if available
    if analyst_ratings:
        lines.append("")
        lines.append("📈 分析師評等 (Yahoo Finance):")
        if "buy_count" in analyst_ratings:
            lines.append(f"  評等: 買進 {analyst_ratings['buy_count']} | 持有 {analyst_ratings.get('hold_count', 0)} | 賣出 {analyst_ratings.get('sell_count', 0)}")
        if "rating_score" in analyst_ratings:
            score = analyst_ratings['rating_score']
            stars = "★" * int(score / 2) + "☆" * (5 - int(score / 2))
            lines.append(f"  評分: {score}/10 {stars}")
        if "avg_target_price" in analyst_ratings:
            lines.append(f"  平均目標價: NT${int(analyst_ratings['avg_target_price']):,}")
        if "max_target_price" in analyst_ratings:
            lines.append(f"  最高目標價: NT${int(analyst_ratings['max_target_price']):,}")
        if "min_target_price" in analyst_ratings:
            lines.append(f"  最低目標價: NT${int(analyst_ratings['min_target_price']):,}")
    else:
        # Show message when analyst ratings are unavailable
        lines.append("")
        lines.append("📊 分析師評等: 暫無公開資料")
        lines.append("  (Yahoo Finance 對部分台股股票的分析師評等資料限制)")
    
    # Note: Remove inaccurate static valuation analysis for Taiwan stocks too
    lines.append("")
    lines.append("ℹ️ 💡提示: 台股數據為即時行情，建議查詢最新投資報告獲得準確分析")
    
    # News section
    if news_articles:
        lines.append("")
        lines.append("📰 相關新聞:")
        lines.append("")
        
        for i, article in enumerate(news_articles[:5], 1):
            # Translate title to Chinese
            zh_title = translate_news_text(article.title)
            lines.append(f"• {zh_title}")
            
            # Translate summary to Chinese
            summary = truncate_summary(article.summary, 150)
            zh_summary = translate_news_text(summary)
            lines.append(f"  {zh_summary}")
            
            source_date = f"來源: {article.source}"
            if article.published_at:
                date_str = article.published_at.strftime("%Y-%m-%d")
                source_date += f" | {date_str}"
            
            lines.append(f"  {source_date}")
            
            if article.url:
                lines.append(f"  🔗 {article.url}")
            
            if i < len(news_articles):
                lines.append("")
    
    # Data source
    lines.append("")
    lines.append(f"📊 資料來源：台灣股市")
    
    return "\n".join(lines)
