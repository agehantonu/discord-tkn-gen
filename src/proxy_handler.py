import os
import requests
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_proxy_lock = threading.Lock()
_bad_proxies = set()

def test_proxy(proxy_str, timeout=8):
    if not proxy_str:
        return False
    proxy_url = f"http://{proxy_str}" if "://" not in proxy_str else proxy_str
    try:
        resp = requests.get("https://discord.com", proxies={"http": proxy_url, "https": proxy_url},
                            timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        return resp.status_code in (200, 301, 302, 403, 429)
    except:
        return False

def pop_proxy(file_path, validate=False, timeout=5):
    global _bad_proxies
    if not file_path:
        return None
    full_path = file_path
    if not os.path.isabs(full_path):
        full_path = os.path.join(BASE_DIR, full_path)
    if not os.path.exists(full_path):
        return None
    with _proxy_lock:
        try:
            with open(full_path, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                return None
            for _ in range(min(len(lines), 10)):
                if not lines:
                    break
                proxy = lines.pop(0)
                if proxy in _bad_proxies:
                    continue
                if validate and not test_proxy(proxy, timeout=timeout):
                    _bad_proxies.add(proxy)
                    continue
                with open(full_path, 'w') as f:
                    f.write('\n'.join(lines))
                return proxy
        except:
            pass
    return None
