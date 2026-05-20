#!/usr/bin/env python3
"""
Debug Yahoo Finance crumb extraction
"""
import requests
import re

print("🔍 檢查 Yahoo Finance 頁面結構...")

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get("https://finance.yahoo.com", headers=headers, timeout=15)
    print(f"✅ 頁面獲取成功 (Status: {response.status_code})")
    print(f"   Content-Length: {len(response.text)} bytes")
    print(f"   Headers: {dict(response.headers)}")
    
    # Check for crumb patterns
    patterns = [
        r'"crumb":"([^"]+)"',
        r'crumb["\']?\s*:\s*["\']?([^"\']+)["\']?',
        r'CRUMB["\']?\s*:\s*["\']?([^"\']+)["\']?',
    ]
    
    print("\n🔎 嘗試多種 Crumb 提取方式...")
    
    for i, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, response.text)
        if matches:
            print(f"✅ 模式 {i} 成功: {matches[0][:40]}...")
        else:
            print(f"❌ 模式 {i} 無結果")
    
    # Show a sample of the HTML
    print("\n📄 HTML 樣本 (前 2000 字元):")
    print(response.text[:2000])
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
