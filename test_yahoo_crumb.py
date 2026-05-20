import aiohttp
import asyncio
import re

async def test_yahoo_with_crumb():
    async with aiohttp.ClientSession() as session:
        try:
            print("[STEP 1] 從 finance.yahoo.com 提取 crumb...")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with session.get('https://finance.yahoo.com', headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    print(f"[ERROR] Status {resp.status}")
                    return
                    
                html = await resp.text()
                crumb_match = re.search(r'"crumb":"([^"]+)"', html)
                
                if not crumb_match:
                    print("[ERROR] 無法從 HTML 中提取 crumb")
                    print(f"[DEBUG] HTML 長度: {len(html)} bytes")
                    # 嘗試其他正則模式
                    print("[DEBUG] 嘗試其他模式...")
                    patterns = [
                        r'crumb["\']?\s*:\s*["\']([^"\']+)["\']',
                        r'"crumb":"([^"]*)"',
                        r"'crumb':'([^']*)'",
                    ]
                    for pattern in patterns:
                        m = re.search(pattern, html)
                        if m:
                            print(f"[DEBUG] 找到 crumb (pattern {patterns.index(pattern)}): {m.group(1)[:30]}...")
                    return
                
                crumb = crumb_match.group(1)
                print(f"[SUCCESS] 獲得 crumb: {crumb[:30]}...")
                
                # 測試 API 調用
                print("\n[STEP 2] 使用 crumb 查詢 ^GSPC...")
                
                api_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/^GSPC"
                params = {'modules': 'price', 'crumb': crumb}
                api_headers = {'User-Agent': headers['User-Agent'], 'Referer': 'https://finance.yahoo.com'}
                
                async with session.get(api_url, params=params, headers=api_headers, timeout=aiohttp.ClientTimeout(total=15)) as api_resp:
                    print(f"[INFO] API Status: {api_resp.status}")
                    
                    if api_resp.status == 200:
                        data = await api_resp.json()
                        if 'quoteSummary' in data and data['quoteSummary'].get('result'):
                            result = data['quoteSummary']['result'][0]
                            if 'price' in result:
                                print("[SUCCESS] ✅ Yahoo Finance 工作正常！")
                                price = result['price'].get('regularMarketPrice', {}).get('raw')
                                print(f"[DATA] ^GSPC 當前價格: {price}")
                            else:
                                print(f"[DEBUG] 回應結構: {result.keys()}")
                        else:
                            print(f"[ERROR] 回應結構不正確: {data.keys()}")
                    else:
                        text = await api_resp.text()
                        print(f"[ERROR] API 返回 {api_resp.status}: {text[:300]}")
                        
        except asyncio.TimeoutError as e:
            print(f"[ERROR] 超時: {e}")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == '__main__':
    asyncio.run(test_yahoo_with_crumb())
