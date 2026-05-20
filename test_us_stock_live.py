#!/usr/bin/env python3
"""
Test US stock index query directly without webhook
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from src.integrations.yahoo_finance import YahooFinanceClient
from src.utils.formatters import format_index_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_yahoo_finance():
    """Test Yahoo Finance crumb and index fetching"""
    print("=" * 60)
    print("🧪 測試 Yahoo Finance 美股指數查詢")
    print("=" * 60)
    
    client = YahooFinanceClient()
    
    # Test 1: Get crumb
    print("\n📝 Step 1: 獲取 Crumb Token...")
    try:
        crumb = await client._get_crumb()
        print(f"✅ Crumb 獲取成功: {crumb[:30]}...")
    except Exception as e:
        print(f"❌ Crumb 獲取失敗: {e}")
        return
    
    # Test 2: Fetch S&P 500
    print("\n📊 Step 2: 查詢 S&P 500...")
    try:
        sp500 = await client.fetch_index("^GSPC")
        print(f"✅ S&P 500: ${sp500.current_price:.2f}")
        print(f"   變化: {sp500.change_percent:+.2f}%")
        print(f"   52周高: ${sp500.high_52w:.2f}")
        print(f"   52周低: ${sp500.low_52w:.2f}")
    except Exception as e:
        print(f"❌ S&P 500 查詢失敗: {e}")
        return
    
    # Test 3: Fetch NASDAQ
    print("\n📊 Step 3: 查詢 NASDAQ...")
    try:
        nasdaq = await client.fetch_index("^IXIC")
        print(f"✅ NASDAQ: ${nasdaq.current_price:.2f}")
        print(f"   變化: {nasdaq.change_percent:+.2f}%")
    except Exception as e:
        print(f"❌ NASDAQ 查詢失敗: {e}")
        return
    
    # Test 4: Fetch Philadelphia Semiconductor
    print("\n📊 Step 4: 查詢費城半導體指數...")
    try:
        sox = await client.fetch_index("^SOX")
        print(f"✅ 費城半導體: ${sox.current_price:.2f}")
        print(f"   變化: {sox.change_percent:+.2f}%")
    except Exception as e:
        print(f"❌ 費城半導體查詢失敗: {e}")
        return
    
    # Test 5: Format message
    print("\n📱 Step 5: 格式化 LINE 訊息...")
    indices = [sp500, nasdaq, sox]
    message = format_index_message(indices)
    print("✅ 訊息格式化成功:")
    print(message)
    
    print("\n" + "=" * 60)
    print("🎉 所有測試通過！美股指數查詢功能正常")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_yahoo_finance())
