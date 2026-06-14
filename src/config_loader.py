import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

BANNER = r"""
discord.gg/novahub
"""

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        MAGENTA = WHITE = CYAN = RED = GREEN = YELLOW = RESET = ""
    class Style:
        RESET_ALL = ""

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.MAGENTA}{BANNER}{Style.RESET_ALL}")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}
