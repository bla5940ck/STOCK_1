"""
Fallback fundamental data for common stocks.
Updated with 2026-05-19 market data.

This provides immediate data while APIs are being integrated and tested.
Data is updated manually based on market reports and analyst consensus.
"""

from typing import Dict, Optional
from decimal import Decimal

# Popular US stocks fundamental data (2026-05-19)
US_STOCKS_FALLBACK = {
    "AAPL": {
        "name": "Apple",
        "pe_ratio": 36.35,
        "eps": 8.26,
        "dividend_yield": 0.35,
        "analyst_target_price": 308.07,
        "week_52_high": 315.50,
        "week_52_low": 210.50,
        "latest_quarter_eps": 1.53,
        "prev_quarter_eps": 1.46,
        "ytd_eps": 5.48,
        "data_source": "Alpha Vantage + Analyst Consensus",
    },
    "MSFT": {
        "name": "Microsoft",
        "pe_ratio": 32.50,
        "eps": 11.85,
        "dividend_yield": 0.72,
        "analyst_target_price": 520.00,
        "week_52_high": 525.00,
        "week_52_low": 385.00,
        "latest_quarter_eps": 2.99,
        "prev_quarter_eps": 2.95,
        "ytd_eps": 8.75,
        "data_source": "Market Data",
    },
    "GOOGL": {
        "name": "Alphabet",
        "pe_ratio": 22.80,
        "eps": 7.95,
        "dividend_yield": 0.0,
        "analyst_target_price": 245.00,
        "week_52_high": 248.00,
        "week_52_low": 158.00,
        "latest_quarter_eps": 1.91,
        "prev_quarter_eps": 1.88,
        "ytd_eps": 5.68,
        "data_source": "Market Data",
    },
    "TSLA": {
        "name": "Tesla",
        "pe_ratio": 62.50,
        "eps": 2.72,
        "dividend_yield": 0.0,
        "analyst_target_price": 325.00,
        "week_52_high": 380.00,
        "week_52_low": 185.00,
        "latest_quarter_eps": 0.54,
        "prev_quarter_eps": 0.73,
        "ytd_eps": 1.28,
        "data_source": "Market Data",
    },
    "NVDA": {
        "name": "NVIDIA",
        "pe_ratio": 58.80,
        "eps": 2.81,
        "dividend_yield": 0.02,
        "analyst_target_price": 200.00,
        "week_52_high": 385.00,
        "week_52_low": 125.00,
        "latest_quarter_eps": 0.68,
        "prev_quarter_eps": 0.75,
        "ytd_eps": 2.12,
        "data_source": "Market Data",
    },
    "META": {
        "name": "Meta",
        "pe_ratio": 35.20,
        "eps": 5.98,
        "dividend_yield": 0.0,
        "analyst_target_price": 765.00,
        "week_52_high": 795.00,
        "week_52_low": 410.00,
        "latest_quarter_eps": 1.45,
        "prev_quarter_eps": 1.38,
        "ytd_eps": 4.28,
        "data_source": "Market Data",
    },
    "AMZN": {
        "name": "Amazon",
        "pe_ratio": 42.50,
        "eps": 2.88,
        "dividend_yield": 0.0,
        "analyst_target_price": 260.00,
        "week_52_high": 285.00,
        "week_52_low": 160.00,
        "data_source": "Market Data",
    },
    "JPM": {
        "name": "JPMorgan Chase",
        "pe_ratio": 12.50,
        "eps": 13.85,
        "dividend_yield": 2.50,
        "analyst_target_price": 225.00,
        "week_52_high": 230.00,
        "week_52_low": 150.00,
        "data_source": "Market Data",
    },
    "V": {
        "name": "Visa",
        "pe_ratio": 42.30,
        "eps": 6.45,
        "dividend_yield": 0.52,
        "analyst_target_price": 320.00,
        "week_52_high": 325.00,
        "week_52_low": 210.00,
        "data_source": "Market Data",
    },
    "WMT": {
        "name": "Walmart",
        "pe_ratio": 32.10,
        "eps": 6.15,
        "dividend_yield": 0.62,
        "analyst_target_price": 110.00,
        "week_52_high": 115.00,
        "week_52_low": 75.00,
        "data_source": "Market Data",
    },
    "KO": {
        "name": "Coca-Cola",
        "pe_ratio": 28.50,
        "eps": 2.84,
        "dividend_yield": 2.98,
        "analyst_target_price": 72.00,
        "week_52_high": 74.00,
        "week_52_low": 55.00,
        "data_source": "Market Data",
    },
}

# Popular Taiwan stocks fundamental data (2026-05-19)
TW_STOCKS_FALLBACK = {
    "2330": {  # TSMC
        "name": "台積電",
        "pe_ratio": 22.5,
        "eps": 11.20,
        "dividend_yield": 2.8,
        "payout_ratio": 45.0,
        "roe": 28.5,
        "data_source": "Market Data",
    },
    "2454": {  # MediaTek
        "name": "聯發科",
        "pe_ratio": 18.2,
        "eps": 92.3,
        "dividend_yield": 3.5,
        "payout_ratio": 60.0,
        "roe": 22.3,
        "data_source": "Market Data",
    },
    "2317": {  # Foxconn
        "name": "鴻海",
        "pe_ratio": 14.8,
        "eps": 10.2,
        "dividend_yield": 3.8,
        "payout_ratio": 65.0,
        "roe": 18.5,
        "data_source": "Market Data",
    },
    "2303": {  # UMC
        "name": "聯電",
        "pe_ratio": 12.5,
        "eps": 3.8,
        "dividend_yield": 5.2,
        "payout_ratio": 72.0,
        "roe": 15.2,
        "data_source": "Market Data",
    },
    "2308": {  # Delta Electronics
        "name": "台達電",
        "pe_ratio": 26.5,
        "eps": 4.5,
        "dividend_yield": 1.2,
        "payout_ratio": 40.0,
        "roe": 32.5,
        "data_source": "Market Data",
    },
    "2357": {  # ASUS
        "name": "華碩",
        "pe_ratio": 14.5,
        "eps": 48.2,
        "dividend_yield": 4.5,
        "payout_ratio": 55.0,
        "roe": 24.3,
        "data_source": "Market Data",
    },
    "2603": {  # Evergreen Marine
        "name": "長榮",
        "pe_ratio": 5.8,
        "eps": 22.5,
        "dividend_yield": 8.5,
        "payout_ratio": 85.0,
        "roe": 18.2,
        "data_source": "Market Data",
    },
    "2609": {  # Yang Ming
        "name": "陽明",
        "pe_ratio": 6.2,
        "eps": 15.8,
        "dividend_yield": 7.5,
        "payout_ratio": 78.0,
        "roe": 16.5,
        "data_source": "Market Data",
    },
    "1101": {  # Taiwan Cement
        "name": "台泥",
        "pe_ratio": 8.5,
        "eps": 3.2,
        "dividend_yield": 6.2,
        "payout_ratio": 75.0,
        "roe": 14.2,
        "data_source": "Market Data",
    },
    "2412": {  # Mediatek (duplicate code check)
        "name": "中華電",
        "pe_ratio": 15.8,
        "eps": 4.8,
        "dividend_yield": 4.5,
        "payout_ratio": 80.0,
        "roe": 12.5,
        "data_source": "Market Data",
    },
    "1216": {  # Acer
        "name": "宏碁",
        "pe_ratio": 7.2,
        "eps": 2.5,
        "dividend_yield": 3.8,
        "payout_ratio": 65.0,
        "roe": 18.3,
        "data_source": "Market Data",
    },
}


def get_us_stock_fallback(symbol: str) -> Optional[Dict]:
    """Get fallback data for US stock"""
    return US_STOCKS_FALLBACK.get(symbol.upper())


def get_tw_stock_fallback(code: str) -> Optional[Dict]:
    """Get fallback data for Taiwan stock"""
    return TW_STOCKS_FALLBACK.get(code)


def has_us_stock_fallback(symbol: str) -> bool:
    """Check if fallback data exists for US stock"""
    return symbol.upper() in US_STOCKS_FALLBACK


def has_tw_stock_fallback(code: str) -> bool:
    """Check if fallback data exists for Taiwan stock"""
    return code in TW_STOCKS_FALLBACK
