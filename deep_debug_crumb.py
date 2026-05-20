#!/usr/bin/env python3
"""
Find the exact crumb pattern in Yahoo Finance HTML
"""
import requests
import re

print("🔍 深入檢查 Yahoo Finance Crumb 位置...\n")

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get("https://finance.yahoo.com", headers=headers, timeout=15)
    html = response.text
    
    # Search for any "crumb" mentions
    crumb_lines = []
    for i, line in enumerate(html.split('\n')):
        if 'crumb' in line.lower():
            crumb_lines.append((i, line[:200]))  # First 200 chars
    
    print(f"Found {len(crumb_lines)} lines containing 'crumb':")
    for line_num, line_content in crumb_lines[:10]:
        print(f"\nLine {line_num}: {line_content}...")
    
    # Try to find any JavaScript object with crumb property
    print("\n\n🔎 嘗試提取 crumb 相關的 JavaScript 代碼...")
    
    # Look for patterns like crumb: "something"
    patterns = [
        r'"crumb"\s*:\s*"([^"]+)"',
        r'crumb\s*:\s*"([^"]+)"',
        r'crumb["\']?\s*:\s*["\']([^"\']+)["\']',
        r'CRUMB["\']?\s*:\s*["\']([^"\']+)["\']',
        r'"crumb":"([^"]*)"',
    ]
    
    for idx, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"✅ 模式 {idx} 成功找到 {len(matches)} 個結果:")
            for m in matches[:3]:
                print(f"   {m[:80]}")
        else:
            print(f"❌ 模式 {idx} 無結果")
    
    # Check HTML size
    print(f"\n📊 HTML 統計:")
    print(f"   大小: {len(html) / 1024:.1f} KB")
    print(f"   行數: {len(html.split(chr(10)))}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
