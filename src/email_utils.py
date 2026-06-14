import re
import time
import requests

def extract_verification_link(body):
    import html as html_mod
    body = html_mod.unescape(body)

    # Try the standard Discord verify link format first
    match = re.search(r'https?://[^\s"\'<>]+?/verify\?token=[a-zA-Z0-9._=-]+', body)
    if match:
        return match.group(0)

    # Try click.discord.com tracking links (most common in Discord emails)
    tracking = re.findall(r'https?://click\.discord\.com/ls/click\?upn=[^"\'\s>]+', body)
    if tracking:
        tracking.sort(key=len, reverse=True)
        return tracking[0]

    # Broader search for any discord.com/verify links
    for link in re.findall(r'https?://[^\s"\'<>]+', body):
        if "discord.com/verify" in link or "click.discord.com" in link:
            return link

    # Search for verification token patterns in plain text
    token_match = re.search(r'token=([a-zA-Z0-9._=-]{20,})', body)
    if token_match:
        # If we find a token, look for a base URL nearby
        url_match = re.search(r'(https?://[^\s"\'<>]+?)\?token=', body)
        if url_match:
            return url_match.group(1) + "?token=" + token_match.group(1)

    # Look for any verification-related URLs
    verify_links = re.findall(r'https?://[^\s"\'<>]*(?:verify|confirm|activate)[^\s"\'<>]*', body, re.IGNORECASE)
    if verify_links:
        return verify_links[0]

    return None

def resolve_tracking_link(url, proxy_url=None):
    if not url or "click.discord.com" not in url:
        return url
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for _ in range(3):
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=20, allow_redirects=True)
            if "/verify" in resp.url and "token=" in resp.url:
                return resp.url
            meta = re.search(r'url=([^"\'\s>]+verify\?token=[^"\'\s>]+)', resp.text, re.I)
            if meta:
                return meta.group(1)
        except:
            time.sleep(1)
    return url

def extract_verify_token(url):
    if not url:
        return None
    match = re.search(r'[?&]token=([a-zA-Z0-9._=-]+)', url)
    return match.group(1) if match else None

def discord_verify_api(verify_token, account_token, proxy_url=None):
    headers = {
        "Authorization": account_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Origin": "https://discord.com",
        "Referer": "https://discord.com/",
    }
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    for _ in range(3):
        try:
            resp = requests.post("https://discord.com/api/v9/auth/verify",
                                 json={"token": verify_token},
                                 headers=headers, proxies=proxies, timeout=20)
            if resp.status_code == 200:
                return bool(resp.json().get("token") or resp.json().get("user_id"))
            if resp.status_code == 429:
                time.sleep(min(resp.json().get("retry_after", 5), 30))
                continue
            return False
        except:
            time.sleep(2)
    return False
