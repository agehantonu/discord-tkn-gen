import threading

_file_lock = threading.Lock()

def save_token(email, password, token, filepath):
    line = f"{email}:{password}:{token}"
    with _file_lock:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(line + "\n")

def count_tokens_file(filepath):
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r') as f:
            return sum(1 for line in f if line.strip() and ':' in line)
    except:
        return 0

def mask_token(token):
    if not token or len(token) < 10:
        return token
    return token[:20] + "*" * (len(token) - 20)
