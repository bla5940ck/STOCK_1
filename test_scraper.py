#!/usr/bin/env python3
"""Test scraping Taiwan stock data from CNYES and WantGoo"""

import requests
from bs4 import BeautifulSoup
import json
import re

print("=== Testing CNYES ===")
url = "https://www.cnyes.com/twstock/board/ratediff.aspx"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Look for table data
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    # Try to find rating/price target data
    if tables:
        # Print first table structure
        for i, table in enumerate(tables[:3]):
            rows = table.find_all('tr')
            print(f"Table {i}: {len(rows)} rows")
            if len(rows) > 1:
                print(f"  Header: {rows[0].get_text()[:100]}")
                print(f"  Sample: {rows[1].get_text()[:100]}")
            
except Exception as e:
    print(f"Error: {e}")

print("\n=== Testing WantGoo ===")
url2 = "https://www.wantgoo.com/stock/ranking/most-recent-quarter-eps"
try:
    resp = requests.get(url2, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Look for data - WantGoo might use JSON in window object
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    # Look for JSON data in script tags
    for i, script in enumerate(scripts):
        if script.string:
            text = script.string
            # Look for stock data patterns
            if 'stock' in text.lower() or 'data' in text.lower():
                print(f"Script {i}: {text[:150]}")
                # Try to extract JSON
                json_matches = re.findall(r'\{[^{}]*\}', text)
                if json_matches:
                    print(f"  Found JSON patterns: {len(json_matches)}")
            
except Exception as e:
    print(f"Error: {e}")

print("\n✅ Test complete")
