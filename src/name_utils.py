import os
import re
import unicodedata
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES_FILE = os.path.join(BASE_DIR, "data", "names.txt")

_names_cache = None

def load_names():
    global _names_cache
    if _names_cache is not None:
        return _names_cache
    _names_cache = []
    if os.path.exists(NAMES_FILE):
        try:
            with open(NAMES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                _names_cache = [l.strip() for l in f if l.strip() and len(l.strip()) > 1]
        except:
            pass
    if not _names_cache:
        _names_cache = ["Frost", "Shadow", "Nova", "Crystal", "Storm", "Void",
                        "Luna", "Pulse", "Echo", "Drift", "Neon", "Zenith"]
    return _names_cache

def sanitize_display_name(raw_name):
    if not raw_name or not raw_name.strip():
        return "user_" + str(random.randint(100, 999))
    name = raw_name.strip()
    name = unicodedata.normalize('NFKD', name)
    result = []
    for ch in name:
        cat = unicodedata.category(ch)
        if cat.startswith('L') or cat.startswith('N'):
            try:
                ascii_ch = unicodedata.normalize('NFKD', ch).encode('ascii', 'ignore').decode('ascii')
                if ascii_ch:
                    result.append(ascii_ch.lower())
            except:
                pass
        elif ch in ' _-.':
            result.append('_')
    cleaned = ''.join(result)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if len(cleaned) < 2:
        latin = re.findall(r'[a-zA-Z]+', raw_name)
        cleaned = ''.join(latin).lower() if latin else "user"
    if len(cleaned) > 15:
        cleaned = cleaned[:15]
    return f"{cleaned}_{random.randint(100, 9999)}"

def get_random_identity():
    names = load_names()
    raw_name = random.choice(names)
    display_name = raw_name
    username = sanitize_display_name(raw_name)
    return display_name, username
