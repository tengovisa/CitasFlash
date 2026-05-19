import logging
import os
import random
import re
import time
import threading
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/root/.env.citafast")

logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

DB_CHECK_INTERVAL = 2
BOOKING_DELAY     = 0.02
TIMES_CACHE_TTL   = 8
SESSION_TIMEOUT   = 15
CYCLE_WAIT        = 30  # segundos entre ciclos login/logout
JSON_TIMEOUT      = 20
TABLE_NAME        = "cuentas_citafast"
LOG_FILE          = "/root/log_nexus.txt"

HOST = "ais.usvisa-info.com"
DEFAULT_HEADERS = {
    "Host": HOST,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
}
DOCUMENT_HEADERS = {
    **DEFAULT_HEADERS,
    "Cache-Control": "no-store",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es,en;q=0.9",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}
JSON_HEADERS = {
    **DEFAULT_HEADERS,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es,en;q=0.9",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}
COUNTRIES = {
    "ar": "Argentina", "ec": "Ecuador", "mx": "Mexico", "br": "Brazil",
    "co": "Colombia", "pe": "Peru", "cl": "Chile", "do": "Dominican Republic",
    "es": "Spain and Andorra", "fr": "France", "gb": "United Kingdom",
    "it": "Italy", "pt": "Portugal", "gr": "Greece", "tr": "Turkiye",
    "ae": "United Arab Emirates", "ca": "Canada", "us": "United States",
}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan variables SUPABASE en .env.citafast")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

active_threads: Dict = {}


# ─────────────────────────────────────────────
# PROXY HELPERS
# Prioridad: residential → datacenter
# ─────────────────────────────────────────────

def get_proxy(exclude_proxy: str = None):
    """Toma el mejor proxy disponible de BD. Prioridad: residential → datacenter."""
    try:
        for proxy_type in ["residential", "rotating", "datacenter"]:
            q = supabase.table("proxies") \
                .select("*") \
                .eq("status", "free") \
                .eq("type", proxy_type) \
                .order("fail_count") \
                .limit(10) \
                .execute()
            rows = q.data or []
            if exclude_proxy:
                rows = [r for r in rows if r.get("proxy") != exclude_proxy]
            if rows:
                return rows[0]
        # Fallback a proxies_pool rotativos
        try:
            q2 = supabase.table("proxies_pool").select("*").eq("status","free").limit(1).execute()
            rows2 = q2.data or []
            if rows2:
                return rows2[0]
        except: pass
        return None
    except Exception:
        return None


def mark_proxy_ok(proxy_value: str):
    """Reset fail_count cuando el proxy funciona."""
    try:
        supabase.table("proxies").update({
            "fail_count": 0,
            "status": "free",
            "last_used": datetime.utcnow().isoformat()
        }).eq("proxy", proxy_value).execute()
    except Exception:
        pass


def mark_proxy_fail(proxy_value: str):
    """Incrementa fail_count. Rotativos NUNCA mueren. Datacenter/residential mueren a 15 fallos."""
    try:
        # Rotativos y residenciales NUNCA mueren
        if "webshare.io" in proxy_value or "iproyal.com" in proxy_value:
            return
        row = supabase.table("proxies").select("fail_count,type").eq("proxy", proxy_value).limit(1).execute()
        if not row.data:
            return
        proxy_type = row.data[0].get("type", "datacenter")
        # Residenciales nunca mueren — son dedicados
        if proxy_type == "residential":
            return
        # Solo datacenter puede morir, limite 15
        fail_count = int(row.data[0].get("fail_count") or 0) + 1
        new_status = "dead" if fail_count >= 15 else "free"
        supabase.table("proxies").update({
            "fail_count": fail_count,
            "status": new_status,
            "last_used": datetime.utcnow().isoformat()
        }).eq("proxy", proxy_value).execute()
    except Exception:
        pass


def proxy_to_dict(proxy_str: str) -> dict:
    p = proxy_str.strip()
    if not p.startswith("http"):
        p = f"http://{p}"
    return {"http": p, "https": p}


# ─────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────


def get_speed_mode():
    """
    Modos de velocidad:
    - Miercoles 7:45am+     → AGRESIVO (0.5s) workers=4
    - Martes 20:00+         → PREPARACION (30s) workers=1
    - Jueves todo el dia    → INTERMEDIO (120s) workers=1
    - Madrugada 0-4am       → DESCANSO (240s) workers=1
    - Resto dias/horas      → NORMAL (240s) workers=1
    """
    from datetime import datetime
    now = datetime.now()
    h, m = now.hour, now.minute
    weekday = now.weekday()  # 0=lun, 1=mar, 2=mie, 3=jue
    is_wednesday = weekday == 2
    is_tuesday = weekday == 1
    is_thursday = weekday == 3

    # Miercoles modo agresivo desde 7:45am
    if is_wednesday and (h > 7 or (h == 7 and m >= 45)):
        return 0.5, 4

    # Martes desde 20:00 — preparacion
    if is_tuesday and h >= 20:
        return 30.0, 1

    # Jueves — intermedio
    if is_thursday:
        return 5.0, 1

    # Madrugada 0-4am — descanso
    if h < 4:
        return 240.0, 1

    # Resto — normal
    return 240.0, 1



def send_push_alert(title: str, message: str):
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging as fcm_msg
        if not firebase_admin._apps:
            cred = credentials.Certificate("/root/firebase-adminsdk.json")
            firebase_admin.initialize_app(cred)
        tokens = supabase.table("fcm_tokens").select("token").execute().data
        if not tokens: return
        for row in tokens:
            try:
                msg = fcm_msg.Message(
                    notification=fcm_msg.Notification(title=title, body=message),
                    webpush=fcm_msg.WebpushConfig(
                        fcm_options=fcm_msg.WebpushFCMOptions(link="https://vps.citaflash.com/panel/")
                    ),
                    token=row["token"]
                )
                fcm_msg.send(msg)
            except: pass
    except: pass

class ThreadLogger:
    def __init__(self):
        fmt = logging.Formatter("%(asctime)s,%(msecs)03d [%(threadName)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        if not root.handlers:
            fh = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
            fh.setFormatter(fmt)
            root.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            root.addHandler(ch)
        self.root = root

    def __call__(self, msg, account_id=None, email=None):
        prefix = f"[{email}] " if email else (f"[Account-{account_id}] " if account_id else "")
        self.root.info(f"{prefix}{msg}")
        if email or account_id:
            try:
                supabase.table("bot_logs").insert({
                    "cuenta_id": account_id,
                    "email": email,
                    "mensaje": str(msg)[:500],
                    "nivel": "ERROR" if "❌" in str(msg) else "INFO"
                }).execute()
            except:
                pass


class NoScheduleIdException(Exception): pass
class AppointmentDateLowerMinDate(Exception): pass


# ─────────────────────────────────────────────
# ACCOUNT CONFIG
# ─────────────────────────────────────────────

class AccountConfig:
    def __init__(self, r: dict):
        self.id               = r['id']
        self.email            = r['email']
        self.password         = r['password']
        self.country          = r['country']
        self.facility_id      = r.get('facility_id')
        self.schedule_id      = r.get('schedule_id')
        self.min_date         = datetime.strptime(r['min_date'], "%Y-%m-%d").date()
        self.max_date         = datetime.strptime(r['max_date'], "%Y-%m-%d").date() if r.get('max_date') else None
        self.need_asc         = r.get('need_asc', False) in [True, 'true', 'True', 1]
        self.asc_facility_id  = r.get('asc_facility_id')
        self.second           = int(r.get('second', 0) or 0)
        self.telegram_token   = r.get('telegram_token', '')
        self.telegram_chat_id = r.get('telegram_chat_id', '')
        self.is_active        = r.get('is_active', True) in [True, 'true', 'True', 1]
        self.status           = r.get('status', 'Activo')
        self.proxy_id         = r.get('proxy_id', None)

    def update_status_in_db(self, is_active, status, appointment_date=None):
        data = {"is_active": is_active, "status": status, "updated_at": datetime.now().isoformat()}
        if appointment_date:
            data["last_appointment_date"] = appointment_date
        try:
            r = supabase.table(TABLE_NAME).update(data).eq("id", self.id).execute()
            return bool(r.data)
        except Exception as e:
            print(f"Error BD: {e}")
            return False


# ─────────────────────────────────────────────
# BOT
# ─────────────────────────────────────────────

class Servicio:
    def __init__(self, config: AccountConfig, logger: ThreadLogger, account_id: int):
        self.config               = config
        self.logger               = logger
        self.account_id           = account_id
        self.url                  = f"https://{HOST}/en-{config.country}/niv"
        self.appointment_datetime = None
        self.csrf                 = None
        self.cookie               = None
        self.session              = requests.Session()
        self.cita_programada      = False
        self.last_db_check        = time.time()
        self.times_cache: Dict[str, List[str]] = {}
        self.times_cache_ts: Dict[str, float]  = {}
        self.executor             = ThreadPoolExecutor(max_workers=4)
        self.current_proxy        = None   # string del proxy activo
        self._init_proxy()

    # ── PROXY ──────────────────────────────────

    def _init_proxy(self, exclude: str = None):
        """Usa proxy dedicado (proxy_id) o fallback al pool."""
        try:
            self.session.close()
        except:
            pass
        self.session = requests.Session()
        self.session.trust_env = False
        proxy_str = None
        # 1. Proxy dedicado de la cuenta
        if self.config.proxy_id and self.config.proxy_id != exclude:
            proxy_str = self.config.proxy_id.strip()
            ip = proxy_str.split("@")[-1] if "@" in proxy_str else proxy_str
            if not exclude:
                self.logger(f"🌐 Proxy [dedicado] {ip}", self.account_id, self.config.email)
        else:
            # 2. Fallback pool (rotating)
            row = get_proxy(exclude_proxy=exclude)
            if row and row.get("proxy"):
                proxy_str = row["proxy"].strip()
                proxy_type = row.get("type", "unknown")
                ip = proxy_str.split("@")[-1] if "@" in proxy_str else proxy_str
                if not exclude:
                    self.logger(f"🌐 Proxy [{proxy_type}] {ip}", self.account_id, self.config.email)
        if proxy_str:
            self.current_proxy = proxy_str
            self.session.proxies = proxy_to_dict(proxy_str)
        else:
            self.current_proxy = None
            self.session.proxies = {}
            self.logger("⚠️ Sin proxies disponibles — esperando 2s", self.account_id, self.config.email)
            time.sleep(2)

    def _rotate_proxy(self):
        """Si es proxy dedicado, reintenta el mismo. Si es pool, marca fallido y rota."""
        if self.config.proxy_id and self.current_proxy == self.config.proxy_id.strip():
            # Proxy dedicado — no marcar dead, solo reintentar
            self.logger(f"🔄 Reintentando proxy dedicado: {self.current_proxy.split('@')[-1]}", self.account_id, self.config.email)
            time.sleep(2)
            self._init_proxy()
        elif self.current_proxy:
            # Pool compartido — marcar fallido y rotar
            mark_proxy_fail(self.current_proxy)
            self.logger(f"🔄 Proxy fallido: {self.current_proxy.split('@')[-1]}", self.account_id, self.config.email)
            self._init_proxy(exclude=self.current_proxy)
        else:
            self._init_proxy()

    def _mark_proxy_ok(self):
        if self.current_proxy:
            mark_proxy_ok(self.current_proxy)

    # ── HEADERS ────────────────────────────────

    def _h(self):
        h = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document"
        }
        if self.cookie:
            h["Cookie"] = self.cookie
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        return h

    # ── LOGIN ──────────────────────────────────

    def login(self):
        self.logger("🔐 LOGIN", self.account_id, self.config.email)
        url = f"{self.url}/users/sign_in"

        try:
            r = self.session.get(
                url,
                headers={**DOCUMENT_HEADERS, "Cookie": "", "Referer": url},
                timeout=SESSION_TIMEOUT
            )
            r.raise_for_status()
            self._mark_proxy_ok()
        except Exception:
            self._rotate_proxy()
            raise

        csrf = BeautifulSoup(r.text, "html.parser").find("meta", {"name": "csrf-token"})["content"]
        cookies = r.headers.get("set-cookie")

        try:
            r2 = self.session.post(
                url,
                headers={
                    **DEFAULT_HEADERS,
                    "X-CSRF-Token": csrf,
                    "Cookie": cookies,
                    "Accept": "*/*;q=0.5, text/javascript, application/javascript",
                    "Referer": url,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
                data=urlencode({
                    "user[email]": self.config.email,
                    "user[password]": self.config.password,
                    "policy_confirmed": "1",
                    "commit": "Sign In"
                }),
                timeout=SESSION_TIMEOUT
            )
            r2.raise_for_status()
            self._mark_proxy_ok()
        except Exception:
            self._rotate_proxy()
            raise

        self.cookie = r2.headers.get("set-cookie")
        self.logger("✅ Login OK", self.account_id, self.config.email)

    # ── INIT DATA ──────────────────────────────

    def init_current_data(self):
        r = self.session.get(self.url, headers={**self._h(), **DOCUMENT_HEADERS}, timeout=SESSION_TIMEOUT)
        r.raise_for_status()
        apps = BeautifulSoup(r.text, "html.parser").find_all("div", {"class": "application"})
        if not apps:
            raise NoScheduleIdException()
        schedule_ids = {}
        for app in apps:
            m = re.search(r"\d+", str(app.find("a")))
            if not m:
                continue
            sid = m.group(0)
            appt = app.find("p", {"class": "consular-appt"})
            appt_dt = None
            if appt:
                am = re.search(r"\d{1,2} \w+?, \d{4}, \d{1,2}:\d{1,2}", appt.get_text())
                if am:
                    try:
                        appt_dt = datetime.strptime(am.group(0), "%d %B, %Y, %H:%M")
                    except:
                        pass
            schedule_ids[sid] = appt_dt
        if not self.config.schedule_id and schedule_ids:
            self.config.schedule_id = next(iter(schedule_ids))
        if self.config.schedule_id in schedule_ids:
            self.appointment_datetime = schedule_ids[self.config.schedule_id]
        if self.appointment_datetime and self.appointment_datetime.date() <= self.config.min_date:
            raise AppointmentDateLowerMinDate()

    def refresh_csrf(self):
        proxies = self.session.proxies.copy() if self.current_proxy else {}
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={**self._h(), **DOCUMENT_HEADERS, "Sec-Fetch-User": "?1",
                     "Referer": f"{self.url}/schedule/{self.config.schedule_id}/continue_actions"},
            timeout=SESSION_TIMEOUT,
            proxies=proxies
        )
        r.raise_for_status()
        self.cookie = r.headers.get("set-cookie") or self.cookie
        self.csrf = BeautifulSoup(r.text, "html.parser").find("meta", {"name": "csrf-token"})["content"]

    def init(self):
        self._init_proxy()
        self.login()
        self.init_current_data()
        self.refresh_csrf()

    # ── FECHAS Y HORARIOS ──────────────────────

    def get_available_dates(self):
        proxies = self.session.proxies.copy() if self.current_proxy else {}
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.facility_id}.json?appointments[expedite]=false",
            headers={**self._h(), **JSON_HEADERS, "Referer": f"{self.url}/schedule/{self.config.schedule_id}/appointment", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            timeout=JSON_TIMEOUT,
            proxies=proxies
        )
        r.raise_for_status()
        dates = sorted([x["date"] for x in r.json()])
        if dates:
            self.logger(f"📅 {len(dates)} fechas: {dates[:3]}", self.account_id, self.config.email)
        return dates

    def _fetch_times(self, date_str):
        try:
            time.sleep(0.3)  # delay entre requests para no saturar proxy
            proxies = self.session.proxies.copy() if self.current_proxy else {}
            r = self.session.get(
                f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.facility_id}.json?date={date_str}&appointments[expedite]=false",
                headers={**self._h(), **JSON_HEADERS, "Referer": f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
                timeout=SESSION_TIMEOUT,
                proxies=proxies
            )
            r.raise_for_status()
            data = r.json()
            times = sorted(data.get("available_times") or data.get("business_times") or [])
            if times:
                self.logger(f"⏰ {len(times)} horarios {date_str}", self.account_id, self.config.email)
            return times
        except Exception as e:
            self.logger(f"⚠️ Error tiempos {date_str}: {type(e).__name__}", self.account_id, self.config.email)
            return []

    def get_times_parallel(self, dates):
        now = time.time()
        to_fetch = [d for d in dates if d not in self.times_cache or (now - self.times_cache_ts.get(d, 0)) >= TIMES_CACHE_TTL]
        result   = {d: self.times_cache[d] for d in dates if d not in to_fetch}
        if to_fetch:
            futures = {self.executor.submit(self._fetch_times, d): d for d in to_fetch}
            for f in as_completed(futures):
                d = futures[f]
                try:
                    t = f.result()
                    self.times_cache[d] = t
                    self.times_cache_ts[d] = time.time()
                    result[d] = t
                except:
                    result[d] = []
        return result

    def get_asc_dates(self, cons_date, cons_time):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.asc_facility_id}.json?&consulate_id={self.config.facility_id}&consulate_date={cons_date}&consulate_time={cons_time}&appointments[expedite]=false",
            headers={**self._h(), **JSON_HEADERS, "Referer": f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=SESSION_TIMEOUT
        )
        r.raise_for_status()
        return sorted([x["date"] for x in r.json()])

    def get_asc_times(self, asc_date, cons_date, cons_time):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.asc_facility_id}.json?date={asc_date}&consulate_id={self.config.schedule_id}&consulate_date={cons_date}&consulate_time={cons_time}&appointments[expedite]=false",
            headers={**self._h(), **JSON_HEADERS, "Referer": f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=SESSION_TIMEOUT
        )
        r.raise_for_status()
        data = r.json()
        return sorted(data.get("available_times") or data.get("business_times") or [])

    # ── BOOKING ────────────────────────────────

    def book(self, date_str, time_str, asc_date, asc_time):
        self.logger(f"🎯 RESERVANDO: {date_str} {time_str}", self.account_id, self.config.email)
        body = {
            "authenticity_token": self.csrf,
            "confirmed_limit_message": "1",
            "use_consulate_appointment_capacity": "true",
            "appointments[consulate_appointment][facility_id]": self.config.facility_id,
            "appointments[consulate_appointment][date]": date_str,
            "appointments[consulate_appointment][time]": time_str,
        }
        if self.config.need_asc and asc_date and asc_time:
            body.update({
                "appointments[asc_appointment][facility_id]": self.config.asc_facility_id,
                "appointments[asc_appointment][date]": asc_date,
                "appointments[asc_appointment][time]": asc_time,
            })
        return self.session.post(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={
                **self._h(), **DOCUMENT_HEADERS, "Sec-Fetch-User": "?1",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": f"https://{HOST}",
                "Referer": f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            },
            data=urlencode(body), timeout=SESSION_TIMEOUT
        )

    def send_telegram(self, msg):
        if not self.config.telegram_token or not self.config.telegram_chat_id:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage",
                json={"chat_id": self.config.telegram_chat_id, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except:
            pass

    # ── CHECK BD ───────────────────────────────

    def _check_db(self):
        now = time.time()
        if now - self.last_db_check < 2:
            return True
        try:
            r = supabase.table(TABLE_NAME).select("is_active").eq("id", self.account_id).execute()
            if r.data and not r.data[0].get('is_active', False):
                return False
            self.last_db_check = now
        except:
            pass
        return True

    # ── PROCESO PRINCIPAL ──────────────────────

    def process(self):
        self.logger(f"🚀 NEXUS — {self.config.email}", self.account_id, self.config.email)
        self.logger(f"📋 País: {self.config.country.upper()} | Facility: {self.config.facility_id}", self.account_id, self.config.email)

        while not self.cita_programada:
            try:
                self.init()

                while not self.cita_programada:
                    if not self._check_db():
                        self.logger("⚠️ Cuenta desactivada", self.account_id, self.config.email)
                        return

                    delay, workers = get_speed_mode()
                    if self.executor._max_workers != workers:
                        self.executor._max_workers = workers
                    # Refresh CSRF cada 60s para mantener sesion viva
                    if not hasattr(self, '_last_csrf') or time.time() - self._last_csrf > 60:
                        try:
                            self.refresh_csrf()
                            self._last_csrf = time.time()
                        except: pass
                    time.sleep(delay)

                    try:
                        all_dates = self.get_available_dates()
                    except Exception as e:
                        err = type(e).__name__
                        self.logger(f"❌ Error fechas: {err}", self.account_id, self.config.email)
                        if err in ("HTTPError", "ConnectionError", "ReadTimeout"):
                            # Intentar solo refresh_csrf primero (mas rapido que re-login)
                            try:
                                self.refresh_csrf()
                                self.logger(f"🔁 CSRF refrescado", self.account_id, self.config.email)
                            except:
                                try:
                                    self.logger(f"🔁 Re-login completo...", self.account_id, self.config.email)
                                    self.init()
                                except Exception as le:
                                    self.logger(f"⚠️ Re-login falló: {type(le).__name__}", self.account_id, self.config.email)
                                    self._rotate_proxy()
                        else:
                            self._rotate_proxy()
                        time.sleep(0.5)
                        continue

                    if not all_dates:
                        self.times_cache.clear()
                        self.times_cache_ts.clear()
                        continue

                    valid_dates = []
                    for d in all_dates:
                        dt = datetime.strptime(d, "%Y-%m-%d").date()
                        if dt < self.config.min_date:
                            continue
                        if self.config.max_date and dt > self.config.max_date:
                            continue
                        if self.appointment_datetime and dt >= self.appointment_datetime.date():
                            continue
                        valid_dates.append(d)

                    for cd in list(self.times_cache.keys()):
                        if cd not in all_dates:
                            self.times_cache.pop(cd, None)
                            self.times_cache_ts.pop(cd, None)

                    if not valid_dates:
                        continue

                    # Tomar solo las primeras 3 fechas para máxima velocidad
                    times_by_date = self.get_times_parallel(valid_dates[:3])

                    for date_str in valid_dates:
                        times = times_by_date.get(date_str, [])
                        if not times:
                            continue
                        # Booking inmediato al primer slot

                        for time_str in times:
                            asc_date = asc_time = None

                            if self.config.need_asc:
                                try:
                                    asc_dates = self.get_asc_dates(date_str, time_str)
                                    if not asc_dates:
                                        continue
                                    asc_date = asc_dates[0]
                                    asc_times = self.get_asc_times(asc_date, date_str, time_str)
                                    if not asc_times:
                                        continue
                                    asc_time = random.choice(asc_times)
                                except Exception as e:
                                    self.logger(f"⚠️ ASC: {type(e).__name__}", self.account_id, self.config.email)
                                    continue

                            try:
                                resp = self.book(date_str, time_str, asc_date, asc_time)

                                if "appointment/instructions" in resp.url:
                                    self.logger("✓ Redirección OK", self.account_id, self.config.email)
                                    try:
                                        self.init_current_data()
                                    except:
                                        self.appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

                                    if self.appointment_datetime:
                                        fecha = self.appointment_datetime.date()
                                        if fecha >= self.config.min_date and (not self.config.max_date or fecha <= self.config.max_date):
                                            self.logger("✅✅✅ ¡CITA AGENDADA! ✅✅✅", self.account_id, self.config.email)
                                            send_push_alert("✅ ¡CITA AGENDADA!", f"{self.config.email} - {date_str} {time_str}")
                                            # Capturar HTML de instrucciones
                                            try:
                                                r_print = self.session.get(
                                                    f"{self.url}/schedule/{self.config.schedule_id}/appointment/print_instructions",
                                                    headers={**self._h(), **DOCUMENT_HEADERS},
                                                    timeout=15
                                                )
                                                supabase.table("citas_confirmaciones").insert({
                                                    "cuenta_id": self.account_id,
                                                    "email": self.config.email,
                                                    "schedule_id": str(self.config.schedule_id),
                                                    "fecha_cita": f"{date_str} {time_str}",
                                                    "html_instrucciones": r_print.text[:50000]
                                                }).execute()
                                            except: pass
                                            # Capturar HTML de instrucciones
                                            try:
                                                r_print = self.session.get(
                                                    f"{self.url}/schedule/{self.config.schedule_id}/appointment/print_instructions",
                                                    headers={**self._h(), **DOCUMENT_HEADERS},
                                                    timeout=15
                                                )
                                                supabase.table("citas_confirmaciones").insert({
                                                    "cuenta_id": self.account_id,
                                                    "email": self.config.email,
                                                    "schedule_id": str(self.config.schedule_id),
                                                    "fecha_cita": f"{date_str} {time_str}",
                                                    "html_instrucciones": r_print.text[:50000]
                                                }).execute()
                                            except: pass
                                            send_push_alert("✅ ¡CITA AGENDADA!", f"{self.config.email} - {date_str} {time_str}")
                                            pais = COUNTRIES.get(self.config.country, self.config.country.upper())
                                            self.send_telegram(
                                                f"✅ *¡CITA PROGRAMADA!*\n\n"
                                                f"🌎 *País*: {pais}\n"
                                                f"👤 *Usuario*: `{self.config.email}`\n"
                                                f"📅 *Fecha*: {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}\n"
                                                + (f"📸 *CAS*: {asc_date} {asc_time}\n" if self.config.need_asc and asc_date else "")
                                            )
                                            self.config.update_status_in_db(
                                                is_active=False, status="Cita Agendada",
                                                appointment_date=self.appointment_datetime.strftime("%Y-%m-%d %H:%M")
                                            )
                                            self.cita_programada = True
                                            break
                                        else:
                                            try:
                                                self.refresh_csrf()
                                            except:
                                                break
                                            continue
                                else:
                                    self.logger("❌ Redirección falló", self.account_id, self.config.email)
                                    self.times_cache.pop(date_str, None)
                                    self.times_cache_ts.pop(date_str, None)
                                    try:
                                        self.refresh_csrf()
                                    except:
                                        break
                                    continue

                            except Exception as e:
                                self.logger(f"❌ BOOK: {type(e).__name__}", self.account_id, self.config.email)
                                self._rotate_proxy()
                                continue

                        if self.cita_programada:
                            break
                    if self.cita_programada:
                        break

            except AppointmentDateLowerMinDate:
                self.logger("⚠️ Cita actual < min_date. Deteniendo.", self.account_id, self.config.email)
                return
            except Exception as e:
                import traceback
                self.logger(f"❌ Sesión: {type(e).__name__} :: {traceback.format_exc()}", self.account_id, self.config.email)
                self._rotate_proxy()
                time.sleep(0.5)

        self.logger(f"✅ TERMINADO: {self.config.email}", self.account_id, self.config.email)
        self.executor.shutdown(wait=False)


# ─────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────

def run_account(account_data: dict, logger: ThreadLogger):
    aid   = account_data['id']
    email = account_data.get('email', 'Unknown')
    try:
        config = AccountConfig(account_data)
        if not config.is_active:
            return
        Servicio(config, logger, aid).process()
    except Exception as e:
        import traceback
        logger(f"❌ Fatal: {e} :: {traceback.format_exc()}", aid, email)
        try:
            supabase.table(TABLE_NAME).update({"status": "Error", "updated_at": datetime.now().isoformat()}).eq("id", aid).execute()
        except:
            pass


def get_active_accounts(logger):
    try:
        r = supabase.table(TABLE_NAME).select("*").eq("is_active", True).execute()
        return r.data or []
    except Exception as e:
        logger(f"❌ Supabase: {e}")
        return []


def main():
    global active_threads
    logger = ThreadLogger()
    logger("=" * 70)
    logger("🚀 NEXUS CONSOLA — INICIANDO")
    logger("=" * 70)
    # Reset proxies al arrancar
    try:
        supabase.table("proxies").update({"status": "free", "fail_count": 0}).neq("id", 0).execute()
        logger("✅ Proxies reseteados al arrancar")
    except Exception as e:
        logger(f"⚠️ Error reseteando proxies: {e}")

    while True:
        logger(f"🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        accounts = get_active_accounts(logger)

        if accounts:
            new_accounts = [a for a in accounts if a['id'] not in active_threads]
            for acc in new_accounts:
                aid = acc['id']
                t = threading.Thread(target=run_account, args=(acc, logger), name=f"CF-{aid}", daemon=True)
                t.start()
                active_threads[aid] = {'thread': t, 'email': acc.get('email'), 'started_at': datetime.now()}
                logger(f"🚀 Iniciado: {acc.get('email')}")

            for aid in [k for k, v in list(active_threads.items()) if not v['thread'].is_alive()]:
                logger(f"✅ Finalizado: {active_threads[aid]['email']}")
                del active_threads[aid]

            pass  # logger(f"📊 Hilos activos: {len(active_threads)}")
        else:
            logger("⚠️ Sin cuentas activas")

        time.sleep(DB_CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Detenido.")
