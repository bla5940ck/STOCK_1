"""
Stock valuation assessment based on P/E ratios and market comparison.
"""

from decimal import Decimal
from typing import Tuple, Literal
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Reference P/E ratios for Taiwan stocks (based on historical averages)
# These are industry/company specific estimates
TW_STOCK_PE_REFERENCE = {
    "2330": 20.5,  # TSMC - semiconductor
    "2454": 18.2,  # MediaTek - semiconductor
    "2317": 12.0,  # Acer - electronics
    "3008": 25.0,  # Largan - optical components (premium)
    "2498": 15.0,  # HTC - electronics
    "2412": 12.5,  # Chunghwa Telecom - telecom
    "1303": 14.0,  # Nanya - memory
    "2882": 9.0,   # Cathay Pacific - airline
    "1101": 10.0,  # Taiwan Cement - cement
    "2891": 8.5,   # China Airlines - airline
    "1216": 14.0,  # Uni-President - food
    "9904": 18.0,  # Powertech - semiconductor
    "2409": 16.0,  # WISTRON - electronics
    "2357": 17.0,  # Innolux - display
    "2308": 15.0,  # Delta - power electronics
}

# Taiwan market average P/E (for stocks not in reference)
TW_MARKET_AVERAGE_PE = 16.0


def get_valuation_assessment(
    stock_code: str,
    current_price: Decimal,
    change_percent: Decimal,
    open_price: Decimal,
    high_price: Decimal,
    low_price: Decimal,
) -> Tuple[Literal["合理價", "便宜", "昂貴"], str]:
    """
    Assess stock valuation based on multiple indicators.
    
    Args:
        stock_code: Taiwan stock code (e.g., "2330")
        current_price: Current stock price
        change_percent: Percent change from previous close
        open_price: Today's opening price
        high_price: Today's high price
        low_price: Today's low price
    
    Returns:
        Tuple of (assessment, reason) where assessment is "合理價", "便宜", or "昂貴"
    """
    
    try:
        current = float(current_price)
        change_pct = float(change_percent)
        open_p = float(open_price) if open_price else current
        high_p = float(high_price) if high_price else current
        low_p = float(low_price) if low_price else current
    except (TypeError, ValueError):
        return "合理價", "數據不足"
    
    # Strategy 1: Position within today's range
    # If price is near high -> expensive, near low -> cheap
    if high_p > low_p:
        position_ratio = (current - low_p) / (high_p - low_p)
    else:
        position_ratio = 0.5
    
    # Strategy 2: Compare with open price
    # If significantly above open -> potentially expensive
    price_above_open = ((current - open_p) / open_p * 100) if open_p > 0 else 0
    
    # Strategy 3: Daily change momentum
    # Large positive change might indicate overheated buying
    # Large negative change might indicate oversold
    
    # Scoring system
    expensiveness_score = 0  # -2: cheap, 0: fair, +2: expensive
    
    # Score 1: Position in range (0.7 = near high, 0.3 = near low)
    if position_ratio > 0.75:
        expensiveness_score += 1.5
    elif position_ratio > 0.65:
        expensiveness_score += 0.5
    elif position_ratio < 0.25:
        expensiveness_score -= 1.5
    elif position_ratio < 0.35:
        expensiveness_score -= 0.5
    
    # Score 2: Price change momentum
    if change_pct > 3:
        expensiveness_score += 0.5  # Significant gain -> might be expensive
    elif change_pct < -3:
        expensiveness_score -= 0.5  # Significant loss -> might be cheap
    
    # Score 3: Compared to open price
    if price_above_open > 2:
        expensiveness_score += 0.3
    elif price_above_open < -2:
        expensiveness_score -= 0.3
    
    # Make assessment based on score
    if expensiveness_score > 1:
        assessment = "昂貴"
        reason = _build_reason(stock_code, position_ratio, change_pct, price_above_open, "expensive")
    elif expensiveness_score < -1:
        assessment = "便宜"
        reason = _build_reason(stock_code, position_ratio, change_pct, price_above_open, "cheap")
    else:
        assessment = "合理價"
        reason = _build_reason(stock_code, position_ratio, change_pct, price_above_open, "fair")
    
    return assessment, reason


def _build_reason(
    stock_code: str,
    position_ratio: float,
    change_pct: float,
    price_above_open: float,
    assessment_type: str,
) -> str:
    """Build a reason string for the valuation assessment."""
    
    reasons = []
    
    # Position in range reasoning
    if position_ratio > 0.75:
        reasons.append("價格接近今日高點")
    elif position_ratio < 0.25:
        reasons.append("價格接近今日低點")
    else:
        reasons.append("價格在合理區間內")
    
    # Change momentum reasoning
    if abs(change_pct) > 2:
        if change_pct > 0:
            reasons.append(f"上漲{change_pct:.2f}%")
        else:
            reasons.append(f"下跌{abs(change_pct):.2f}%")
    
    return "，".join(reasons)
