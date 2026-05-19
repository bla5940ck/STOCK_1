#!/usr/bin/env python3
"""Update Taiwan stocks list from FinMind API"""

import asyncio
import aiohttp
import json
import os

async def fetch_taiwan_stocks():
    """Fetch all Taiwan stocks from FinMind API"""
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://api.finmindtrade.com/api/v4/data'
            params = {'dataset': 'TaiwanStockInfo'}
            print("🔄 Connecting to FinMind API...")
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        stocks = []
                        for item in data['data']:
                            try:
                                stock = {
                                    'code': str(item.get('stock_id', '')).strip(),
                                    'zh_name': item.get('stock_name', '').strip(),
                                    'market': item.get('market_type', 'TSE').strip(),
                                    'type': item.get('industry_category', '').strip()
                                }
                                if stock['code'] and stock['zh_name']:
                                    stocks.append(stock)
                            except Exception as e:
                                pass
                        return stocks
                else:
                    print(f"❌ API returned status {response.status}")
        except asyncio.TimeoutError:
            print("❌ Timeout connecting to FinMind API")
        except Exception as e:
            print(f"❌ Error: {e}")
    return None

async def main():
    stocks = await fetch_taiwan_stocks()
    if stocks:
        print(f'✅ Successfully fetched {len(stocks)} Taiwan stocks')
        
        # Update file
        output_path = os.path.join(os.path.dirname(__file__), 'src/data/tw_stocks.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'stocks': stocks}, f, ensure_ascii=False, indent=2)
        print(f'✅ Updated {output_path}')
        
        # Show first 15 stocks
        print('\n📊 First 15 stocks:')
        for i, stock in enumerate(stocks[:15], 1):
            print(f"  {i:2}. {stock['code']}: {stock['zh_name']:12} ({stock['market']})")
        
        # Check if 尚茂 is in the list
        for stock in stocks:
            if '尚茂' in stock['zh_name']:
                print(f"\n✅ Found 尚茂: {stock}")
        
        print(f'\n📈 Total stocks in database: {len(stocks)}')
    else:
        print('❌ Failed to fetch Taiwan stocks')

if __name__ == '__main__':
    asyncio.run(main())
