"""
Stock fundamental data and valuation analysis.
DEPRECATED: Static values removed - use real-time APIs only.
"""

from decimal import Decimal
from typing import Dict, Tuple, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# EMPTY: All static fundamentals data removed
# Reason: Static data was outdated and displayed inaccurate EPS and target prices
# Solution: Use real-time APIs instead
US_STOCK_FUNDAMENTALS = {}
TW_STOCK_FUNDAMENTALS = {}


def get_fundamental_data(stock_code: str, market: str = "us") -> Optional[Dict]:
    """
    Get fundamental data - DEPRECATED
    Now returns None to prevent displaying outdated data.
    """
    logger.warning(f"get_fundamental_data() called for {stock_code} - use real-time APIs instead")
    return None


def build_valuation_analysis(stock_code: str, current_price: Decimal) -> str:
    """
    Build valuation analysis - DEPRECATED
    This function is no longer used. Static analyst data has been removed
    to avoid displaying outdated information.
    """
    logger.warning(f"build_valuation_analysis() deprecated for {stock_code}")
    return "⚠️ 靜態估值數據已移除，請查詢最新投資研報以獲得準確信息"


def get_future_outlook(stock_code: str, market: str = "us") -> str:
    """Get future outlook - returns generic message."""
    return "請查詢最新投資研報以獲得準確信息"


DEFAULT_FUNDAMENTALS = {
    "name": "N/A",
    "industry": "Unknown",
    "outlook": "Please check latest investment research.",
}


def get_stock_fundamentals(stock_code: str) -> Dict:
    """Get fundamental data for a stock."""
    return DEFAULT_FUNDAMENTALS.copy()
