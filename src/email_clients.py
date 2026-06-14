import os
import time
import random
import string
import imaplib
import email as email_lib
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MailcowClient:
    def __init__(self, host, api_key, domain):
        self.host = host
        self.domain = domain
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key, "Content-Type": "application/json"})

    def create_and_track(self):
        local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=16))
        email = f"{local}@{self.domain}"
        payload = {
            "local_part": local, "domain": self.domain, "name": local,
            "password": password, "password2": password,
            "quota": 100, "active": 1, "force_pw_update": 0,
            "tls_enforce_in": 0, "tls_enforce_out": 0
        }
        try:
            resp = self.session.post(f"{self.host}/api/v1/add/mailbox", json=payload, timeout=15,
                                     proxies={"http": None, "https": None})
            if resp.status_code == 200:
                return {"email": email, "password": password}
        except:
            pass
        return None

    def get_emails(self, email_addr, password, wait=True, timeout=120):
        start = time.time()
        auth_failures = 0
        while True:
            try:
                imap = imaplib.IMAP4_SSL(f"mail.{self.domain}", 993)
                imap.login(email_addr, password)
                auth_failures = 0
                imap.select("INBOX")
                status, messages = imap.search(None, "ALL")
                if status == "OK" and messages[0]:
                    mail_ids = messages[0].split()
                    emails = []
                    for mid in reversed(mail_ids):
                        status, data = imap.fetch(mid, "(RFC822)")
                        if status == "OK":
                            msg = email_lib.message_from_bytes(data[0][1])
                            body = ""
                            html_body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    ct = part.get_content_type()
                                    if ct == "text/plain" and not body:
                                        body = part.get_payload(decode=True).decode(errors="ignore")
                                    elif ct == "text/html" and not html_body:
                                        html_body = part.get_payload(decode=True).decode(errors="ignore")
                            else:
                                body = msg.get_payload(decode=True).decode(errors="ignore")
                            emails.append({
                                "subject": msg.get("subject", ""),
                                "body": html_body if html_body else body
                            })
                    imap.logout()
                    if emails:
                        return emails
                imap.logout()
            except Exception as e:
                err = str(e)
                if 'AUTHENTICATIONFAILED' in err:
                    auth_failures += 1
                    if auth_failures > 8:
                        return []
                    time.sleep(min(5, 2 + auth_failures))
                    continue
                time.sleep(2)
            if not wait or (time.time() - start) > timeout:
                break
            time.sleep(5)
        return []

class CyberTempClient:
    def __init__(self, api_key, domain=None):
        self.api_key = api_key
        self.base_url = "https://api.cybertemp.xyz"
        self.headers = {"X-API-KEY": api_key} if api_key else {}
        self.custom_domain = domain

    def get_domains(self, domain_type=None):
        try:
            params = {}
            if domain_type:
                params["type"] = domain_type
            resp = requests.get(f"{self.base_url}/getDomains", params=params,
                                headers=self.headers, timeout=10,
                                proxies={"http": None, "https": None})
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "domains" in data:
                    domains_list = data["domains"]
                elif isinstance(data, list):
                    domains_list = data
                else:
                    return []
                return [d.get("domain", d) if isinstance(d, dict) else d for d in domains_list]
        except:
            pass
        return []

    def create_and_track(self):
        if self.custom_domain:
            target_domain = self.custom_domain
        else:
            domains = self.get_domains(domain_type="discord")
            if not domains:
                domains = self.get_domains()
            if not domains:
                return None
            target_domain = random.choice(domains)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return {"email": f"{username}@{target_domain}", "password": "N/A"}

    def get_emails(self, email_addr, password=None, wait=True, timeout=60):
        start_time = time.time()
        while True:
            try:
                resp = requests.get(f"{self.base_url}/getMail",
                                    params={"email": email_addr},
                                    headers=self.headers, timeout=10,
                                    proxies={"http": None, "https": None})
                if resp.status_code == 200:
                    emails = resp.json()
                    if emails:
                        return [{"id": e.get("id", ""),
                                 "subject": e.get("subject", ""),
                                 "body": e.get("html") or e.get("text") or ""} for e in emails]
            except:
                pass
            if not wait or (time.time() - start_time) > timeout:
                break
            time.sleep(5)
        return []

    def delete_email(self, email_id):
        if not email_id:
            return False
        try:
            resp = requests.delete(f"{self.base_url}/email/{email_id}",
                                   headers=self.headers, timeout=10,
                                   proxies={"http": None, "https": None})
            return resp.ok
        except:
            return False

    def delete_inbox(self, email_address):
        if not email_address:
            return True
        try:
            resp = requests.delete(f"{self.base_url}/inbox/{email_address}",
                                   headers=self.headers, timeout=10,
                                   proxies={"http": None, "https": None})
            if resp.ok:
                return True
            if resp.status_code in (401, 403):
                return True
            return False
        except:
            return True

class OrifyClient:
    ORIFY_DOMAINS = ["sptech.io.vn", "antdev.org", "epmtyfl.me"]
    BASE_URL = "https://orifymail.com/api"

    def create_and_track(self):
        try:
            domain = random.choice(self.ORIFY_DOMAINS)
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            email = f"{username}@{domain}"
            return {"email": email, "password": "N/A"}
        except:
            return None

    def get_emails(self, email_addr, password=None, wait=True, timeout=120):
        start = time.time()
        while True:
            try:
                resp = requests.get(f"{self.BASE_URL}/email/{email_addr}", timeout=15)
                if resp.status_code == 200:
                    mails = resp.json()
                    if isinstance(mails, list) and mails:
                        results = []
                        for m in mails:
                            msg_id = m.get("id")
                            try:
                                r2 = requests.get(f"{self.BASE_URL}/inbox/{msg_id}", timeout=15)
                                if r2.status_code == 200:
                                    data = r2.json()
                                    results.append({
                                        "id": msg_id,
                                        "subject": data.get("subject", m.get("subject", "")),
                                        "body": data.get("htmlContent", "") or data.get("textContent", "")
                                    })
                                else:
                                    results.append({
                                        "id": msg_id,
                                        "subject": m.get("subject", ""),
                                        "body": ""
                                    })
                            except:
                                results.append({
                                    "id": msg_id,
                                    "subject": m.get("subject", ""),
                                    "body": ""
                                })
                        if results:
                            return results
            except:
                pass
            if not wait or (time.time() - start) > timeout:
                break
            time.sleep(3)
        return []

class SutemeadoClient:
    """Client for sutemeado.com temporary email API."""

    def __init__(self, base_url="https://sutemeado.com"):
        self.base_url = base_url.rstrip("/")
        self._password = None

    def _api_request(self, method, endpoint, json_data=None, params=None):
        """Helper to make API requests with error handling and debug logging."""
        import traceback
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"    [Sutemeado API] {method} {url}")
            if method == "GET":
                resp = requests.get(url, params=params, timeout=15,
                                    proxies={"http": None, "https": None})
            elif method == "POST":
                resp = requests.post(url, json=json_data, timeout=15,
                                     proxies={"http": None, "https": None})
            elif method == "DELETE":
                resp = requests.delete(url, json=json_data, timeout=15,
                                       proxies={"http": None, "https": None})
            elif method == "PUT":
                resp = requests.put(url, json=json_data, timeout=15,
                                    proxies={"http": None, "https": None})
            else:
                return None
            print(f"    [Sutemeado API] Response status: {resp.status_code}")
            if resp.status_code in (200, 201, 204):
                try:
                    data = resp.json()
                    print(f"    [Sutemeado API] Response data: {data}")
                    return data
                except Exception as e:
                    print(f"    [Sutemeado API] JSON parse error: {e}")
                    return {"success": True}
            else:
                print(f"    [Sutemeado API] Error response: {resp.text[:500]}")
                return None
        except Exception as e:
            print(f"    [Sutemeado API] Request failed: {e}")
            traceback.print_exc()
            return None

    def create_and_track(self):
        """Create a new temporary email address."""
        data = self._api_request("GET", "/api/new-address")
        if data and data.get("success"):
            self._password = data.get("password", "")
            return {
                "email": data.get("address", ""),
                "password": data.get("password", ""),
                "domain": data.get("domain", "")
            }
        return None

    def get_emails(self, email_addr, password, wait=True, timeout=120):
        """Get emails for an address. Password must be provided."""
        start = time.time()
        check_count = 0
        while True:
            check_count += 1
            elapsed = int(time.time() - start)
            try:
                data = self._api_request(
                    "POST",
                    f"/api/mailbox/{email_addr}",
                    json_data={"password": password}
                )
                if data and data.get("success"):
                    mails = data.get("mails", [])
                    print(f"    [Sutemeado Mail] Check #{check_count} ({elapsed}s): {len(mails)} mail(s) found")
                    if mails:
                        results = []
                        for m in mails:
                            results.append({
                                "id": m.get("id", ""),
                                "subject": m.get("subject", ""),
                                "body": m.get("html") or m.get("body") or "",
                                "from": m.get("from", ""),
                                "receivedAt": m.get("receivedAt", 0)
                            })
                        if results:
                            return results
                else:
                    print(f"    [Sutemeado Mail] Check #{check_count} ({elapsed}s): API returned no success")
            except Exception as e:
                print(f"    [Sutemeado Mail] Check #{check_count} ({elapsed}s): Error - {e}")
            if not wait or (time.time() - start) > timeout:
                print(f"    [Sutemeado Mail] Timeout after {timeout}s ({check_count} checks)")
                break
            time.sleep(5)
        return []

    def get_email_detail(self, email_addr, password, mail_id):
        """Get a specific email by ID."""
        data = self._api_request(
            "POST",
            f"/api/mailbox/{email_addr}/{mail_id}",
            json_data={"password": password}
        )
        if data and data.get("success"):
            return {
                "id": data.get("id", mail_id),
                "subject": data.get("subject", ""),
                "body": data.get("html") or data.get("body") or "",
                "from": data.get("from", ""),
                "receivedAt": data.get("receivedAt", 0)
            }
        return None

    def delete_email(self, email_addr, password, mail_id):
        """Delete a specific email."""
        if not mail_id or not email_addr or not password:
            return False
        data = self._api_request(
            "DELETE",
            f"/api/mailbox/{email_addr}/{mail_id}",
            json_data={"password": password}
        )
        if data and data.get("success"):
            return True
        return False

    def delete_inbox(self, email_addr, password=None):
        """Delete all emails in an address."""
        pwd = password or self._password
        if not email_addr or not pwd:
            return True
        data = self._api_request(
            "DELETE",
            f"/api/mailbox/{email_addr}",
            json_data={"password": pwd}
        )
        if data and data.get("success"):
            return True
        return False

    def delete_address(self, email_addr, password):
        """Delete an address (all emails will be deleted)."""
        if not email_addr or not password:
            return True
        data = self._api_request(
            "DELETE",
            f"/api/address/{email_addr}",
            json_data={"password": password}
        )
        if data and data.get("success"):
            return True
        return False

    def get_otp(self, email_addr, password, limit=5):
        """Extract OTP from recent emails."""
        data = self._api_request(
            "GET",
            f"/api/mailbox/{email_addr}/otp",
            params={"password": password, "limit": limit}
        )
        if data and data.get("success") and data.get("found"):
            return data.get("otp", "")
        return None

def get_email_client(config):
    providers = config.get("email_providers", {})
    active = config.get("email_provider", "sutemeado")
    if active == "sutemeado" and providers.get("sutemeado", {}).get("enabled"):
        se = providers["sutemeado"]
        return SutemeadoClient(se.get("base_url", "https://sutemeado.com"))
    elif active == "mailcow" and providers.get("mailcow", {}).get("enabled"):
        mc = providers["mailcow"]
        return MailcowClient(mc["host_url"], mc["api_key"], mc["domain"])
    elif active == "cybertemp" and providers.get("cybertemp", {}).get("enabled"):
        ct = providers["cybertemp"]
        return CyberTempClient(ct["api_key"], ct.get("domain"))
    elif active == "orify" and providers.get("orify", {}).get("enabled"):
        return OrifyClient()
    for name in ["sutemeado", "mailcow", "cybertemp", "orify"]:
        p = providers.get(name, {})
        if p.get("enabled"):
            if name == "sutemeado":
                return SutemeadoClient(p.get("base_url", "https://sutemeado.com"))
            elif name == "mailcow":
                return MailcowClient(p["host_url"], p["api_key"], p["domain"])
            elif name == "cybertemp":
                return CyberTempClient(p["api_key"], p.get("domain"))
            elif name == "orify":
                return OrifyClient()
    return None
