import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVATARS_DIR = os.path.join(BASE_DIR, "data", "avatars")

_avatars_cache = None

def load_avatars():
    global _avatars_cache
    if _avatars_cache is not None:
        return _avatars_cache
    _avatars_cache = []
    if os.path.exists(AVATARS_DIR):
        try:
            for f in os.listdir(AVATARS_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    _avatars_cache.append(os.path.join(AVATARS_DIR, f))
        except:
            pass
    return _avatars_cache

def get_random_avatar():
    avatars = load_avatars()
    return random.choice(avatars) if avatars else None
