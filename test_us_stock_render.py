#!/usr/bin/env python3
"""
Quick test for "美股" query on Render.
Tests the entire flow: keyword detection → handler → response.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


async def test_美股_flow():
    """Test complete flow for '美股' query"""
    print("\n" + "=" * 60)
    print("🧪 Testing '美股' Query Flow")
    print("=" * 60 + "\n")
    
    # Test 1: Keyword detection
    print("1️⃣  Testing keyword detection...")
    from src.utils.validators import is_index_keyword, detect_query_type
    
    test_keywords = ["美股", "指數", "index", "AAPL", "新聞"]
    for keyword in test_keywords:
        is_index = is_index_keyword(keyword)
        query_type = detect_query_type(keyword)
        status = "✅" if (keyword in ["美股", "指數", "index"]) == is_index else "❌"
        print(f"   {status} '{keyword}': is_index={is_index}, type={query_type}")
    
    # Test 2: Index handler
    print("\n2️⃣  Testing index handler...")
    from src.db.database import get_async_session
    from src.handlers.index_handler import handle_index_query
    
    try:
        async with get_async_session() as db:
            result = await handle_index_query(db)
        
        print(f"   Result: {result.get('success')}")
        print(f"   Source: {result.get('source')}")
        if result.get("success"):
            message = result.get("message", "")
            print(f"   Message length: {len(message)} chars")
            print(f"   Contains emoji: {'✅' if '📈' in message else '❌'}")
            print(f"   Contains timestamp: {'✅' if '數據時間' in message else '❌'}")
            print(f"   First 100 chars:\n   {message[:100]}...")
        else:
            print(f"   Error: {result.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Market data service
    print("\n3️⃣  Testing market data service...")
    from src.services.market_data import MarketDataService
    
    try:
        async with get_async_session() as db:
            service = MarketDataService(db)
            indices_result = await service.get_indices()
            await service.close()
        
        print(f"   Success: {indices_result.get('success')}")
        print(f"   Source: {indices_result.get('source')}")
        if indices_result.get('success'):
            indices = indices_result.get('data', [])
            print(f"   Indices count: {len(indices)}")
            for idx in indices[:3]:
                print(f"     • {idx.code}: {idx.change_percent:.2f}%")
        else:
            print(f"   Error: {indices_result.get('error_message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Webhook message processing
    print("\n4️⃣  Testing webhook message processing...")
    from src.api.webhooks import WebhookEventHandler
    
    try:
        async with get_async_session() as db:
            handler = WebhookEventHandler(db)
            
            # Simulate message event
            message_event = {
                "type": "message",
                "source": {"userId": "test-user-123"},
                "replyToken": "test-reply-token",
                "message": {"type": "text", "text": "美股"}
            }
            
            response = await handler.process_message_event(message_event)
            
            if response:
                print(f"   ✅ Response generated")
                print(f"   Length: {len(response)} chars")
                print(f"   First 100 chars:\n   {response[:100]}...")
            else:
                print(f"   ❌ No response generated")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_美股_flow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
