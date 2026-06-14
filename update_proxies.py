#!/usr/bin/env python3
"""
無料プロキシを自動取得して proxies.txt に保存するスクリプト
使い方:
    python update_proxies.py
    # または有効なプロキシのみをテストして保存
    python update_proxies.py --validate
"""

import argparse
import requests
import sys
import os

# 無料プロキシAPIのURL
PROXY_SOURCES = {
    "proxyscrape_http": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "proxyscrape_https": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=10000&country=all&ssl=all&anonymity=all",
    "proxyscrape_socks4": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all",
    "proxyscrape_socks5": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
}

# HTTPプロキシのみを使用（SOCKSは追加ライブラリが必要）
DEFAULT_SOURCES = ["proxyscrape_http", "proxyscrape_https"]

def fetch_proxies(source_urls):
    """APIからプロキシリストを取得"""
    all_proxies = []
    for name, url in source_urls.items():
        if name not in DEFAULT_SOURCES:
            continue
        try:
            print(f"[*] Fetching from {name}...")
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                proxies = [p.strip() for p in resp.text.strip().split('\n') if p.strip()]
                print(f"[+] Got {len(proxies)} proxies from {name}")
                all_proxies.extend(proxies)
            else:
                print(f"[-] Failed: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[-] Error fetching {name}: {e}")
    
    # 重複削除
    unique_proxies = list(dict.fromkeys(all_proxies))
    return unique_proxies

def validate_proxy(proxy_str, timeout=8):
    """プロキシがDiscordに接続できるかテスト"""
    proxy_url = f"http://{proxy_str}" if "://" not in proxy_str else proxy_str
    try:
        resp = requests.get(
            "https://discord.com",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return resp.status_code in (200, 301, 302, 403, 429)
    except:
        return False

def save_proxies(proxies, filepath="proxies.txt"):
    """プロキシをファイルに保存"""
    with open(filepath, 'w') as f:
        f.write('\n'.join(proxies) + '\n')
    print(f"[+] Saved {len(proxies)} proxies to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Update free proxy list")
    parser.add_argument("--validate", action="store_true", help="Test each proxy before saving (slower but more reliable)")
    parser.add_argument("--output", default="proxies.txt", help="Output file path")
    parser.add_argument("--max", type=int, default=100, help="Maximum number of proxies to save")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Free Proxy Updater")
    print("=" * 50)
    
    # プロキシ取得
    proxies = fetch_proxies(PROXY_SOURCES)
    if not proxies:
        print("[-] No proxies fetched. Exiting.")
        sys.exit(1)
    
    print(f"[*] Total unique proxies: {len(proxies)}")
    
    # 有効性テスト（オプション）
    if args.validate:
        print(f"[*] Testing proxies (this may take a while)...")
        valid_proxies = []
        for i, proxy in enumerate(proxies[:args.max * 3]):  # テスト対象を増やす
            if i % 10 == 0:
                print(f"    Testing {i+1}/{min(len(proxies), args.max * 3)}...")
            if validate_proxy(proxy):
                valid_proxies.append(proxy)
                if len(valid_proxies) >= args.max:
                    break
        proxies = valid_proxies
        print(f"[+] Valid proxies: {len(proxies)}")
    else:
        proxies = proxies[:args.max]
    
    # 保存
    save_proxies(proxies, args.output)
    
    print("=" * 50)
    print("Done! Set proxies.enabled = true in config.json to use them.")
    print("=" * 50)

if __name__ == "__main__":
    main()
