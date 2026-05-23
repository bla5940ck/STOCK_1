#!/usr/bin/env python3
"""
Diagnostic script for LINE Bot "美股" query failure on Render.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

async def diagnose_all() -> Dict[str, Any]:
    """Run all diagnostics"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # 1. Test environment variables
    print("=" * 60)
    print("1️⃣  Checking Environment Variables...")
    print("=" * 60)
    
    env_test = await test_environment()
    results["tests"]["environment"] = env_test
    print(f"✅ LINE_CHANNEL_SECRET: {'✓' if env_test['has_secret'] else '✗'}")
    print(f"✅ LINE_CHANNEL_ACCESS_TOKEN: {'✓' if env_test['has_token'] else '✗'}")
    print(f"✅ ALPHA_VANTAGE_API_KEY: {'✓' if env_test['has_alpha_key'] else '✗'}")
    print(f"✅ DATABASE_URL: {env_test.get('db_url', 'Not set')[:30]}...")
    
    # 2. Test database connection
    print("\n" + "=" * 60)
    print("2️⃣  Testing Database Connection...")
    print("=" * 60)
    
    db_test = await test_database()
    results["tests"]["database"] = db_test
    if db_test["connected"]:
        print("✅ Database connection: OK")
    else:
        print(f"❌ Database connection failed: {db_test['error']}")
    
    # 3. Test Yahoo Finance API
    print("\n" + "=" * 60)
    print("3️⃣  Testing Yahoo Finance API...")
    print("=" * 60)
    
    yahoo_test = await test_yahoo_finance()
    results["tests"]["yahoo_finance"] = yahoo_test
    if yahoo_test["success"]:
        print(f"✅ Yahoo Finance: OK - Fetched {yahoo_test['index_count']} indices")
        for idx in yahoo_test.get("indices", []):
            print(f"   • {idx['symbol']}: {idx['change_percent']:.2f}%")
    else:
        print(f"❌ Yahoo Finance failed: {yahoo_test['error']}")
    
    # 4. Test Alpha Vantage API
    print("\n" + "=" * 60)
    print("4️⃣  Testing Alpha Vantage API...")
    print("=" * 60)
    
    alpha_test = await test_alpha_vantage()
    results["tests"]["alpha_vantage"] = alpha_test
    if alpha_test["success"]:
        print(f"✅ Alpha Vantage: OK - Fetched {alpha_test['index_count']} indices")
    else:
        print(f"⚠️  Alpha Vantage: {alpha_test['error']}")
    
    # 5. Test index handler
    print("\n" + "=" * 60)
    print("5️⃣  Testing Index Handler (模拟'美股'查询)...")
    print("=" * 60)
    
    handler_test = await test_index_handler()
    results["tests"]["index_handler"] = handler_test
    if handler_test["success"]:
        print(f"✅ Index handler: OK")
        print(f"   Response length: {len(handler_test['message'])} chars")
        print(f"   Contains '📈': {'✓' if '📈' in handler_test['message'] else '✗'}")
        print(f"   Contains timestamp: {'✓' if '數據時間' in handler_test['message'] else '✗'}")
    else:
        print(f"❌ Index handler failed: {handler_test['error']}")
    
    # 6. Test LINE API connection
    print("\n" + "=" * 60)
    print("6️⃣  Testing LINE API Connection...")
    print("=" * 60)
    
    line_test = await test_line_api()
    results["tests"]["line_api"] = line_test
    if line_test["reachable"]:
        print(f"✅ LINE API reachable: {line_test['status_code']}")
    else:
        print(f"❌ LINE API unreachable: {line_test['error']}")
    
    # 7. Summary and recommendations
    print("\n" + "=" * 60)
    print("📋 Diagnostic Summary")
    print("=" * 60)
    
    all_passed = all(
        test.get("success") or test.get("connected") or test.get("reachable")
        for test in results["tests"].values()
    )
    
    if all_passed:
        print("✅ All systems operational!")
        print("\nThe issue might be:")
        print("• Network timeout between Render and external APIs")
        print("• Rate limiting from data providers")
        print("• LINE webhook signature verification failure")
    else:
        print("❌ Issues detected:")
        for test_name, test_result in results["tests"].items():
            if not (test_result.get("success") or test_result.get("connected") or test_result.get("reachable")):
                print(f"   • {test_name}: {test_result.get('error', 'Unknown error')}")
    
    return results


async def test_environment() -> Dict[str, Any]:
    """Test environment variables"""
    return {
        "has_secret": bool(os.environ.get("LINE_CHANNEL_SECRET")),
        "has_token": bool(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")),
        "has_alpha_key": bool(os.environ.get("ALPHA_VANTAGE_API_KEY")),
        "db_url": os.environ.get("DATABASE_URL", "Not set"),
    }


async def test_database() -> Dict[str, Any]:
    """Test database connection"""
    try:
        from src.db.database import init_db, get_async_engine
        
        engine = get_async_engine()
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        return {"connected": True}
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


async def test_yahoo_finance() -> Dict[str, Any]:
    """Test Yahoo Finance API"""
    try:
        from src.integrations.yahoo_finance import YahooFinanceClient
        
        client = YahooFinanceClient()
        indices = await client.fetch_indices(["^GSPC", "^IXIC", "^SOX"])
        
        await client.close()
        
        if indices:
            return {
                "success": True,
                "index_count": len(indices),
                "indices": [
                    {
                        "symbol": idx.code,
                        "change_percent": idx.change_percent
                    }
                    for idx in indices.values()
                ]
            }
        else:
            return {
                "success": False,
                "error": "No data returned"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200]
        }


async def test_alpha_vantage() -> Dict[str, Any]:
    """Test Alpha Vantage API"""
    try:
        from src.integrations.alpha_vantage import AlphaVantageClient
        
        client = AlphaVantageClient()
        indices = await client.fetch_indices(["^GSPC", "^IXIC", "^SOX"])
        
        await client.close()
        
        if indices:
            return {
                "success": True,
                "index_count": len(indices)
            }
        else:
            return {
                "success": False,
                "error": "No data returned"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200]
        }


async def test_index_handler() -> Dict[str, Any]:
    """Test index handler (模拟'美股'查询)"""
    try:
        from src.db.database import get_async_session
        from src.handlers.index_handler import handle_index_query
        
        async with get_async_session() as db:
            result = await handle_index_query(db)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message", ""),
                "source": result.get("source")
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Handler failed")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200]
        }


async def test_line_api() -> Dict[str, Any]:
    """Test LINE API reachability"""
    try:
        import aiohttp
        
        url = "https://api.line.me/v2/bot/profile/me"
        headers = {
            "Authorization": f"Bearer {os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'test')}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return {
                    "reachable": True,
                    "status_code": response.status
                }
    except Exception as e:
        return {
            "reachable": False,
            "error": str(e)[:200]
        }


if __name__ == "__main__":
    print("\n🔍 LINE Bot Diagnostic Report")
    print(f"⏰ Time: {datetime.now().isoformat()}\n")
    
    try:
        results = asyncio.run(diagnose_all())
        
        print("\n" + "=" * 60)
        print("Generated diagnostic report")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
