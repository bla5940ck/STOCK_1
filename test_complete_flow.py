#!/usr/bin/env python3
"""
Test complete index query flow with fallback logic
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.services.market_data import MarketDataService
from src.utils.formatters import format_index_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_market_data():
    """Test market data service with fallback logic"""
    print("=" * 70)
    print("🧪 測試完整美股指數查詢流程（包含 fallback）")
    print("=" * 70)
    
    # Create async database session
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = MarketDataService(session)
        
        print("\n📊 Step 1: 調用 get_indices()（會自動嘗試 Yahoo Finance → Alpha Vantage fallback）...")
        try:
            result = await service.get_indices()
            
            if result.get("success"):
                indices = result.get("data", [])
                print(f"✅ 成功獲取指數數據！")
                print(f"   來源: {result.get('source')}")
                print(f"   數量: {len(indices)} 個指數")
                
                # Format message
                print("\n📱 Step 2: 格式化 LINE 訊息...")
                message = format_index_message(indices)
                print("✅ 訊息格式化成功:")
                print("\n" + message)
                
                return True
            else:
                print(f"❌ 查詢失敗: {result.get('error_message')}")
                return False
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await service.close()
            await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(test_market_data())
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 測試成功！應用能正確返回美股指數數據")
    else:
        print("❌ 測試失敗，應用無法返回美股指數數據")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
