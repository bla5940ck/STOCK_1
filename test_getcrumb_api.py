#!/usr/bin/env python3
"""
Test getting crumb directly from getcrumb API endpoint
"""
import requests
import json

print("🧪 測試 getcrumb API 端點...\n")

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.yahoo.com"
    }
    
    # First, let's get cookies from finance.yahoo.com
    print("1️⃣ 獲取 finance.yahoo.com cookies...")
    resp1 = requests.get("https://finance.yahoo.com", headers=headers, timeout=15)
    print(f"   Status: {resp1.status_code}")
    print(f"   Cookies: {resp1.cookies}")
    
    # Now try to get crumb from the API
    print("\n2️⃣ 嘗試從 getcrumb API 獲取...")
    resp2 = requests.get(
        "https://query1.finance.yahoo.com/v1/test/getcrumb?lang=en-US&region=US",
        headers=headers,
        cookies=resp1.cookies,
        timeout=15
    )
    print(f"   Status: {resp2.status_code}")
    print(f"   Response: {resp2.text[:200]}")
    
    if resp2.status_code == 200:
        try:
            data = resp2.json()
            crumb = data.get('crumb') or data
            print(f"   ✅ Crumb: {crumb}")
        except:
            print(f"   Response (raw): {resp2.text}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
