import json
import logging
import os
import random
import re
import time
import sys
import threading
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from requests import Response, HTTPError
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/root/.env.citafast")

logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

HOST = "ais.usvisa-info.com"
REFERER = "Referer"
ACCEPT = "Accept"
SET_COOKIE = "set-cookie"
CONTENT_TYPE = "Content-Type"
CACHE_CONTROL_HEADERS = {"Cache-Control": "no-store"}
DEFAULT_HEADERS = {
    "Host": HOST,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
}
SEC_FETCH_USER_HEADERS = {"Sec-Fetch-User": "?1"}
DOCUMENT_HEADERS = {
    **DEFAULT_HEADERS,
    **CACHE_CONTROL_HEADERS,
    ACCEPT: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ru,en;q=0.9,de;q=0.8,bg;q=0.7",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Upgrade-Insecure-Requests": "1",
}
JSON_HEADERS = {
    **DEFAULT_HEADERS,
    ACCEPT: "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ru,en;q=0.9,de;q=0.8,bg;q=0.7",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}
X_CSRF_TOKEN_HEADER = "X-CSRF-Token"
COOKIE_HEADER = "Cookie"
COUNTRIES = {
    "ar": "Argentina", "ec": "Ecuador", "bs": "The Bahamas", "gy": "Guyana",
    "bb": "Barbados", "jm": "Jamaica", "bz": "Belize", "mx": "Mexico",
    "br": "Brazil", "py": "Paraguay", "bo": "Bolivia", "pe": "Peru",
    "ca": "Canada", "sr": "Suriname", "cl": "Chile", "tt": "Trinidad and Tobago",
    "co": "Colombia", "uy": "Uruguay", "cw": "Curacao",
    "do": "Dominican Republic", "zm": "Zambia",
}
HTML_PARSER = "html.parser"
LOG_FILE = "/root/log_nexus.txt"
LOG_FORMAT = "%(asctime)s [%(threadName)s] %(message)s"
TABLE_NAME = "cuentas_citafast"
DB_CHECK_INTERVAL = 45

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

active_threads = {}

def get_speed_mode():
    now = datetime.now()
    h, m = now.hour, now.minute
    weekday = now.weekday()
    is_wednesday = weekday == 2
    is_tuesday = weekday == 1
    is_thursday = weekday == 3
    if is_wednesday:
        if h == 7 and m >= 50: return "ULTRA", 0.1, 4
        if h == 8 and m <= 10: return "ULTRA", 0.1, 4
        if h == 7 and 45 <= m < 50: return "AGRESIVO", 0.3, 4
        if h == 7 and m < 45: return "PREPARACION", 5.0, 2
        if h == 8 and m > 10: return "INTERMEDIO", 10.0, 2
    if is_tuesday and h >= 20: return "PREPARACION", 30.0, 1
    if is_thursday: return "INTERMEDIO", 120.0, 1
    if 0 <= h < 4: return "DESCANSO", 240.0, 1
    return "NORMAL", 20.0, 1

class ThreadLogger:
    def __init__(self, log_file, log_format):
        log_formatter = logging.Formatter(log_format)
        root_logger = logging.getLogger()
        root_logger.setLevel("INFO")
        if not root_logger.handlers:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(log_formatter)
            root_logger.addHandler(file_handler)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            root_logger.addHandler(console_handler)
        self.root_logger = root_logger

    def __call__(self, message, account_id=None, email=None):
        prefix = f"[{email}] " if email else f"[Account:{account_id}] " if account_id else ""
        self.root_logger.info(f"{prefix}{message}")

class NoScheduleIdException(Exception):
    def __init__(self): super().__init__("No schedule id")

class AppointmentDateLowerMinDate(Exception):
    def __init__(self): super().__init__("Current appointment date lower than min date")

class AccountConfig:
    def __init__(self, db_record):
        self.id = db_record['id']
        self.email = db_record['email']
        self.password = db_record['password']
        self.country = db_record['country']
        self.facility_id = db_record.get('facility_id')
        self.schedule_id = db_record.get('schedule_id')
        self.min_date = datetime.strptime(db_record['min_date'], "%Y-%m-%d").date()
        self.max_date = datetime.strptime(db_record['max_date'], "%Y-%m-%d").date() if db_record.get('max_date') else None
        raw_proxies = db_record.get('proxies', '') or ''
        self.proxies_list = [p.strip() for p in raw_proxies.split(',') if p.strip()]
        self.need_asc = db_record.get('need_asc', False) in [True, 'true', 'True', 1]
        self.asc_facility_id = db_record.get('asc_facility_id')
        self.second = int(db_record.get('second', 0) or 0)
        self.telegram_token = db_record.get('telegram_token', '') or ''
        self.telegram_chat_id = db_record.get('telegram_chat_id', '') or ''
        self.is_active = db_record.get('is_active', True) in [True, 'true', 'True', 1]
        self.status = db_record.get('status', 'Activo')

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

class Appointment:
    def __init__(self, schedule_id, description, appointment_datetime):
        self.schedule_id = schedule_id
        self.appointment_datetime = appointment_datetime

class Bot:
    def __init__(self, config, logger, account_id):
        self.logger = logger
        self.config = config
        self.account_id = account_id
        self.url = f"https://{HOST}/en-{config.country}/niv"
        self.appointment_datetime = None
        self.csrf = None
        self.cookie = None
        self.proxies_list = config.proxies_list
        self.current_proxy_index = 0
        self.current_proxy_url = None
        self.session = requests.Session()
        self.session.timeout = 12
        self.asc_dates = {}
        self._initialize_proxy_session()
        self.cita_programada = False
        self.last_proxy_check = time.time()
        self.executor = ThreadPoolExecutor(max_workers=1)

    @staticmethod
    def get_csrf(response):
        return BeautifulSoup(response.text, HTML_PARSER).find("meta", {"name": "csrf-token"})["content"]

    def headers(self):
        h = {}
        if self.cookie: h[COOKIE_HEADER] = self.cookie
        if self.csrf: h[X_CSRF_TOKEN_HEADER] = self.csrf
        return h

    def _initialize_proxy_session(self):
        try: self.session.close()
        except: pass
        self.session = requests.Session()
        self.session.timeout = 12
        if self.proxies_list:
            self.current_proxy_url = self.proxies_list[self.current_proxy_index]
            p = self.current_proxy_url
            if not p.startswith("http"): p = f"http://{p}"
            self.session.proxies = {"http": p, "https": p}
        else:
            self.current_proxy_url = None
            self.session.proxies = {}

    def change_proxy(self):
        if not self.proxies_list:
            self.logger("⚠️ Sin proxies", self.account_id, self.config.email)
            return
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies_list)
        self.current_proxy_url = self.proxies_list[self.current_proxy_index]
        display = self.current_proxy_url.split('@')[-1] if '@' in self.current_proxy_url else self.current_proxy_url
        self.logger(f"🔄 Proxy → {display}", self.account_id, self.config.email)
        self._initialize_proxy_session()

    def check_account_updates_from_db(self):
        try:
            r = supabase.table(TABLE_NAME).select("proxies").eq("id", self.account_id).execute()
            if r.data:
                raw = r.data[0].get('proxies', '') or ''
                new_list = [p.strip() for p in raw.split(',') if p.strip()]
                if set(new_list) != set(self.proxies_list):
                    self.logger(f"📦 Proxies: {len(new_list)}", self.account_id, self.config.email)
                    self.proxies_list = new_list
                    self._initialize_proxy_session()
        except Exception as e:
            self.logger(f"Error proxies: {e}", self.account_id, self.config.email)

    def is_account_active_in_db(self):
        try:
            r = supabase.table(TABLE_NAME).select("is_active").eq("id", self.account_id).execute()
            return r.data[0].get('is_active', False) if r.data else False
        except:
            return True

    def init(self):
        self._initialize_proxy_session()
        self.login()
        self.init_current_data()
        self.init_csrf_and_cookie()

    def login(self):
        self.logger("🔐 LOGIN", self.account_id, self.config.email)
        r = self.session.get(f"{self.url}/users/sign_in",
            headers={COOKIE_HEADER: "", REFERER: f"{self.url}/users/sign_in", **DOCUMENT_HEADERS}, timeout=12)
        r.raise_for_status()
        cookies = r.headers.get(SET_COOKIE)
        r2 = self.session.post(f"{self.url}/users/sign_in",
            headers={**DEFAULT_HEADERS, X_CSRF_TOKEN_HEADER: Bot.get_csrf(r),
                COOKIE_HEADER: cookies,
                ACCEPT: "*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript",
                REFERER: f"{self.url}/users/sign_in",
                CONTENT_TYPE: "application/x-www-form-urlencoded; charset=UTF-8"},
            data=urlencode({"user[email]": self.config.email, "user[password]": self.config.password,
                "policy_confirmed": "1", "commit": "Sign In"}), timeout=12)
        r2.raise_for_status()
        self.cookie = r2.headers.get(SET_COOKIE)
        self.logger("✅ Login OK", self.account_id, self.config.email)

    def init_current_data(self):
        r = self.session.get(self.url, headers={**self.headers(), **DOCUMENT_HEADERS}, timeout=12)
        r.raise_for_status()
        apps = BeautifulSoup(r.text, HTML_PARSER).find_all("div", {"class": "application"})
        if not apps: raise NoScheduleIdException()
        schedule_ids = {}
        for app in apps:
            m = re.search(r"\d+", str(app.find("a")))
            if not m: continue
            sid = m.group(0)
            appt = app.find("p", {"class": "consular-appt"})
            appt_dt = None
            if appt:
                am = re.search(r"\d{1,2} \w+?, \d{4}, \d{1,2}:\d{1,2}", appt.get_text())
                if am:
                    try: appt_dt = datetime.strptime(am.group(0), "%d %B, %Y, %H:%M")
                    except: pass
            schedule_ids[sid] = Appointment(sid, "", appt_dt)
        if not self.config.schedule_id and schedule_ids:
            self.config.schedule_id = next(iter(schedule_ids))
        if self.config.schedule_id in schedule_ids:
            self.appointment_datetime = schedule_ids[self.config.schedule_id].appointment_datetime
        if self.appointment_datetime and self.appointment_datetime.date() <= self.config.min_date:
            raise AppointmentDateLowerMinDate()

    def init_csrf_and_cookie(self):
        r = self.load_change_appointment_page()
        self.cookie = r.headers.get(SET_COOKIE) or self.cookie
        self.csrf = Bot.get_csrf(r)

    def load_change_appointment_page(self):
        r = self.session.get(f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={**self.headers(), **DOCUMENT_HEADERS, **SEC_FETCH_USER_HEADERS,
                REFERER: f"{self.url}/schedule/{self.config.schedule_id}/continue_actions"}, timeout=12)
        r.raise_for_status()
        return r

    def get_available_dates(self):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.facility_id}.json?appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12)
        r.raise_for_status()
        dates = sorted([x["date"] for x in r.json()])
        if dates: self.logger(f"📅 Fechas: {len(dates)}", self.account_id, self.config.email)
        return dates

    def get_available_times(self, date_str):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.facility_id}.json?date={date_str}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12)
        r.raise_for_status()
        data = r.json()
        times = sorted(data.get("available_times") or data.get("business_times") or [])
        return times

    def get_available_times_parallel(self, dates):
        results = {}
        futures = {self.executor.submit(self.get_available_times, d): d for d in dates}
        for f in as_completed(futures):
            try: results[futures[f]] = f.result()
            except: results[futures[f]] = []
        return results

    def get_asc_available_dates(self, avail_date=None, avail_time=None):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.asc_facility_id}.json?&consulate_id={self.config.facility_id}&consulate_date={avail_date or ''}&consulate_time={avail_time or ''}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12)
        r.raise_for_status()
        return sorted([x["date"] for x in r.json()])

    def get_asc_available_times(self, asc_date, avail_date=None, avail_time=None):
        r = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.asc_facility_id}.json?date={asc_date}&consulate_id={self.config.schedule_id}&consulate_date={avail_date or ''}&consulate_time={avail_time or ''}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12)
        r.raise_for_status()
        data = r.json()
        return sorted(data.get("available_times") or data.get("business_times") or [])

    def book(self, avail_date, avail_time, asc_date=None, asc_time=None):
        self.logger(f"🎯 RESERVANDO: {avail_date} {avail_time}", self.account_id, self.config.email)
        body = {"authenticity_token": self.csrf, "confirmed_limit_message": "1",
            "use_consulate_appointment_capacity": "true",
            "appointments[consulate_appointment][facility_id]": self.config.facility_id,
            "appointments[consulate_appointment][date]": avail_date,
            "appointments[consulate_appointment][time]": avail_time}
        if self.config.need_asc and asc_date and asc_time:
            body.update({"appointments[asc_appointment][facility_id]": self.config.asc_facility_id,
                "appointments[asc_appointment][date]": asc_date,
                "appointments[asc_appointment][time]": asc_time})
        return self.session.post(f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={**self.headers(), **DOCUMENT_HEADERS, **SEC_FETCH_USER_HEADERS,
                CONTENT_TYPE: "application/x-www-form-urlencoded",
                "Origin": f"https://{HOST}",
                REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            data=urlencode(body), timeout=12)

    def send_telegram(self, token, chat_id, message):
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except: pass

    def process(self):
        self.logger("=" * 70, self.account_id, self.config.email)
        self.logger(f"🚀 NEXUS — {self.config.email}", self.account_id, self.config.email)
        self.logger(f"📋 ID: {self.account_id} | País: {self.config.country.upper()}", self.account_id, self.config.email)
        self.logger(f"📦 Proxies: {len(self.proxies_list)}", self.account_id, self.config.email)
        self.logger("=" * 70, self.account_id, self.config.email)
        last_db_check = time.time()

        while not self.cita_programada:
            try:
                if time.time() - last_db_check >= 300:
                    if not self.is_account_active_in_db():
                        self.logger("⚠️ Cuenta desactivada.", self.account_id, self.config.email)
                        return
                    self.check_account_updates_from_db()
                    last_db_check = time.time()

                self.init()

                while not self.cita_programada:
                    if time.time() - last_db_check >= 300:
                        if not self.is_account_active_in_db():
                            self.logger("⚠️ Cuenta desactivada.", self.account_id, self.config.email)
                            return
                        self.check_account_updates_from_db()
                        last_db_check = time.time()

                    mode, delay, workers = get_speed_mode()
                    if workers != self.executor._max_workers:
                        self.executor.shutdown(wait=False)
                        self.executor = ThreadPoolExecutor(max_workers=workers)
                    time.sleep(delay)

                    try:
                        available_dates = self.get_available_dates()
                    except Exception as err:
                        self.logger(f"❌ Error fechas: {type(err).__name__}. Rotando...", self.account_id, self.config.email)
                        self.change_proxy()
                        break

                    if not available_dates:
                        continue

                    valid_dates = [d for d in available_dates
                        if datetime.strptime(d, "%Y-%m-%d").date() > self.config.min_date
                        and (not self.config.max_date or datetime.strptime(d, "%Y-%m-%d").date() <= self.config.max_date)
                        and (not self.appointment_datetime or datetime.strptime(d, "%Y-%m-%d").date() < self.appointment_datetime.date())]

                    if not valid_dates:
                        continue

                    times_by_date = self.get_available_times_parallel(valid_dates)

                    for date_str in valid_dates:
                        times = times_by_date.get(date_str, [])
                        if not times:
                            continue
                        for time_str in times:
                            asc_date_str = None
                            asc_time_str = None
                            if self.config.need_asc:
                                avail_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                min_asc = avail_date - timedelta(days=7)
                                found = False
                                for k, v in self.asc_dates.items():
                                    if min_asc <= datetime.strptime(k, "%Y-%m-%d").date() < avail_date and v:
                                        asc_date_str = k
                                        asc_time_str = random.choice(v)
                                        found = True
                                        break
                                if not found:
                                    try:
                                        asc_dates = self.get_asc_available_dates(date_str, time_str)
                                        if asc_dates:
                                            asc_date_str = asc_dates[0]
                                            asc_times = self.get_asc_available_times(asc_date_str, date_str, time_str)
                                            if asc_times:
                                                asc_time_str = random.choice(asc_times)
                                    except Exception as e:
                                        self.logger(f"Error ASC: {e}", self.account_id, self.config.email)
                                        continue
                            try:
                                rb = self.book(date_str, time_str, asc_date_str, asc_time_str)
                                if "appointment/instructions" in rb.url:
                                    self.init_current_data()
                                    if self.appointment_datetime and self.appointment_datetime.date() == datetime.strptime(date_str, "%Y-%m-%d").date():
                                        self.logger("✅✅✅ ¡¡¡CITA AGENDADA!!! ✅✅✅", self.account_id, self.config.email)
                                        nombre_pais = COUNTRIES.get(self.config.country, self.config.country.upper())
                                        msg = (f"✅ **¡CITA PROGRAMADA!**\n\n"
                                            f"🌎 **País**: {nombre_pais}\n"
                                            f"👤 **Usuario**: `{self.config.email}`\n"
                                            f"📅 **Fecha**: {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}\n")
                                        if self.config.need_asc and asc_date_str:
                                            msg += f"📸 **CAS**: {asc_date_str} {asc_time_str}\n"
                                        if self.config.telegram_token and self.config.telegram_chat_id:
                                            self.send_telegram(self.config.telegram_token, self.config.telegram_chat_id, msg)
                                        self.config.update_status_in_db(False, "Cita Agendada",
                                            self.appointment_datetime.strftime("%Y-%m-%d %H:%M"))
                                        self.cita_programada = True
                                        break
                                else:
                                    self.logger("❌ Reserva falló", self.account_id, self.config.email)
                            except Exception as e:
                                self.logger(f"❌ Error BOOK: {type(e).__name__}", self.account_id, self.config.email)
                                self.change_proxy()
                                continue
                        if self.cita_programada:
                            break
                    if self.cita_programada:
                        break

            except Exception as err:
                self.logger(f"❌ Error: {type(err).__name__}", self.account_id, self.config.email)
                self.change_proxy()
                time.sleep(0.5)

        self.logger(f"✅ HILO TERMINADO: {self.config.email}", self.account_id, self.config.email)
        self.executor.shutdown(wait=False)


def run_account_thread(account_data, logger):
    account_id = account_data['id']
    email = account_data.get('email', 'Unknown')
    try:
        config = AccountConfig(account_data)
        if not config.is_active:
            return
        Bot(config, logger, account_id).process()
    except Exception as e:
        logger(f"❌ Error: {e}", account_id, email)
        try:
            supabase.table(TABLE_NAME).update({"status": "Error", "updated_at": datetime.now().isoformat()}).eq("id", account_id).execute()
        except:
            pass


def get_active_accounts(logger):
    try:
        r = supabase.table(TABLE_NAME).select("*").eq("is_active", True).execute()
        return r.data if r.data else []
    except Exception as e:
        logger(f"❌ Error Supabase: {e}")
        return []


def main():
    global active_threads
    logger = ThreadLogger(LOG_FILE, LOG_FORMAT)
    logger("=" * 70)
    logger("🚀 NEXUS CONSOLA — INICIANDO")
    logger("=" * 70)

    while True:
        mode, delay, workers = get_speed_mode()
        logger(f"⚡ Modo: {mode} | Delay: {delay}s | Workers: {workers}")
        accounts = get_active_accounts(logger)

        if accounts:
            logger(f"✅ Cuentas activas: {len(accounts)}")
            new_accounts = [a for a in accounts if a['id'] not in active_threads]
            if new_accounts:
                logger(f"🆕 Nuevas cuentas: {len(new_accounts)}")
                for acc in new_accounts:
                    account_id = acc['id']
                    email = acc.get('email', 'Unknown')
                    t = threading.Thread(target=run_account_thread, args=(acc, logger),
                        name=f"CF-{account_id}", daemon=True)
                    t.start()
                    active_threads[account_id] = {'thread': t, 'email': email, 'started_at': datetime.now()}
                    logger(f"🚀 Iniciado: {email}")

            finished = [aid for aid, info in list(active_threads.items()) if not info['thread'].is_alive()]
            for aid in finished:
                del active_threads[aid]
            logger(f"📊 Hilos activos: {len(active_threads)}")
        else:
            logger("⚠️ Sin cuentas activas")

        logger("-" * 80)
        time.sleep(DB_CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción. Cerrando...")
        sys.exit(0)
