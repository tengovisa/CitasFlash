import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
import logging
import os
import random
import re
import time
import sys
import threading
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from requests import Response, HTTPError


# ================= SILENCIAR LOGS TÉCNICOS =================
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ================= CONFIGURACIÓN OPTIMIZADA PARA I7 =================
DB_CHECK_INTERVAL = 45
PROXY_CHECK_INTERVAL = 90
BOOKING_DELAY = 0.05  # ⚡ Optimizado

# ================= CONFIGURACIÓN GLOBAL =================
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
    "co": "Colombia", "uy": "Uruguay", "cw": "Curacao", "us": "United States (Domestic Visa Renewal)",
    "al": "Albania", "ie": "Ireland", "am": "Armenia", "kv": "Kosovo",
    "az": "Azerbaijan", "mk": "North Macedonia", "be": "Belgium", "nl": "The Netherlands",
    "ba": "Bosnia and Herzegovina", "pt": "Portugal", "hr": "Croatia", "cy": "Cyprus",
    "rs": "Serbia", "es": "Spain and Andorra", "fr": "France", "tr": "Turkiye",
    "gr": "Greece", "gb": "United Kingdom", "it": "Italy", "il": "Israel, Jerusalem, The West Bank, and Gaza",
    "ae": "United Arab Emirates", "ir": "Iran", "ao": "Angola", "rw": "Rwanda",
    "cm": "Cameroon", "sn": "Senegal", "cv": "Cabo Verde", "tz": "Tanzania",
    "cd": "The Democratic Republic of the Congo", "za": "South Africa", "et": "Ethiopia",
    "ug": "Uganda", "ke": "Kenya", "do": "Dominican Republic", "zm": "Zambia",
}
DATE_TIME_FORMAT = "%H:%M %Y-%m-%d"
DATE_FORMAT = "%d.%m.%Y"
HTML_PARSER = "html.parser"
LOG_FILE = "log_multihilo.txt"
LOG_FORMAT = "%(asctime)s [%(threadName)s] %(message)s"

# ================= SUPABASE CONFIG =================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan variables SUPABASE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= VARIABLES GLOBALES =================
active_threads = {}

# ================= LOGGER MULTITHREAD =================
class ThreadLogger:
    def __init__(self, log_file: str, log_format: str):
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

    def __call__(self, message: str | Exception, account_id: Optional[int] = None, email: Optional[str] = None):
        prefix = ""
        if email:
            prefix = f"[{email}] "
        elif account_id:
            prefix = f"[Account:{account_id}] "
        self.root_logger.info(f"{prefix}{message}")

# ================= CLASES DE EXCEPCIÓN =================
class NoScheduleIdException(Exception):
    def __init__(self):
        super().__init__("No schedule id")

class AppointmentDateLowerMinDate(Exception):
    def __init__(self):
        super().__init__("Current appointment date and time lower than specified minimal date")

# ================= MODELO DE CUENTA =================
class AccountConfig:
    def __init__(self, db_record: dict):
        self.id: int = db_record['id']
        self.email: str = db_record['email']
        self.password: str = db_record['password']
        self.country: str = db_record['country']
        self.facility_id: Optional[str] = db_record.get('facility_id')
        self.schedule_id: Optional[str] = db_record.get('schedule_id')
        self.min_date: date = datetime.strptime(db_record['min_date'], "%Y-%m-%d").date()
        self.max_date: Optional[date] = None
        if db_record.get('max_date'):
            self.max_date = datetime.strptime(db_record['max_date'], "%Y-%m-%d").date()
        self.proxies_list: List[str] = [p.strip() for p in db_record.get('proxies', '').split(',') if p.strip()] if db_record.get('proxies') else []
        self.need_asc: bool = db_record.get('need_asc', False) in [True, 'true', 'True', 1]
        self.asc_facility_id: Optional[str] = db_record.get('asc_facility_id')
        self.second: int = int(db_record.get('second', 0)) if db_record.get('second') else 0
        self.telegram_token: str = db_record.get('telegram_token', '')
        self.telegram_chat_id: str = db_record.get('telegram_chat_id', '')
        self.is_active: bool = db_record.get('is_active', True) in [True, 'true', 'True', 1]
        self.status: str = db_record.get('status', 'Activo')

    def update_status_in_db(self, is_active: bool, status: str, appointment_date: Optional[str] = None):
        update_data = {
            "is_active": is_active,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        if appointment_date:
            update_data["last_appointment_date"] = appointment_date
        
        try:
            print(f"\n🔄 ACTUALIZANDO BD...")
            print(f"   Email: {self.email}")
            print(f"   is_active: {is_active}")
            print(f"   status: {status}")
            
            response = supabase.table("cuentas_bot").update(update_data).eq("id", self.id).execute()
            
            if response.data and len(response.data) > 0:
                print(f"✅ BD ACTUALIZADA - {self.email}")
                return True
            else:
                print(f"⚠️ Reintentando - {self.email}")
                response = supabase.table("cuentas_bot").update(update_data).eq("id", self.id).execute()
                if response.data and len(response.data) > 0:
                    print(f"✅ BD ACTUALIZADA EN SEGUNDO INTENTO - {self.email}")
                    return True
                else:
                    print(f"❌ FALLO - {self.email}")
                    return False
            
        except Exception as e:
            print(f"❌ ERROR - {self.email}: {e}")
            return False

# ================= CLASE APPOINTMENT =================
class Appointment:
    def __init__(self, schedule_id: str, description: str, appointment_datetime: Optional[datetime]):
        self.schedule_id = schedule_id
        self.description = description
        self.appointment_datetime = appointment_datetime

# ================= CLASE BOT (OPTIMIZADA) =================
class Bot:
    def __init__(self, config: AccountConfig, logger: ThreadLogger, account_id: int):
        self.logger = logger
        self.config = config
        self.account_id = account_id
        self.url = f"https://{HOST}/en-{config.country}/niv"
        self.appointment_datetime: Optional[datetime] = None
        self.csrf: Optional[str] = None
        self.cookie: Optional[str] = None
        self.proxies_list = config.proxies_list
        self.current_proxy_index = 0
        self.current_proxy_url: Optional[str] = None
        self.session = requests.Session()
        self.session.timeout = 12  # ⚡ Optimizado
        self.asc_dates = {}
        self._initialize_proxy_session()
        self.cita_programada = False
        self.last_proxy_check = time.time()
        self.executor = ThreadPoolExecutor(max_workers=6)  # ⚡ Optimizado

    @staticmethod
    def get_csrf(response: Response) -> str:
        return BeautifulSoup(response.text, HTML_PARSER).find("meta", {"name": "csrf-token"})["content"]

    def headers(self) -> dict[str, str]:
        headers = {}
        if self.cookie:
            headers[COOKIE_HEADER] = self.cookie
        if self.csrf:
            headers[X_CSRF_TOKEN_HEADER] = self.csrf
        return headers

    def _initialize_proxy_session(self):
        try:
            self.session.close()
        except:
            pass
        self.session = requests.Session()
        self.session.timeout = 12
        
        if self.proxies_list:
            self.current_proxy_url = self.proxies_list[self.current_proxy_index]
            proxy_dict = {
                "http": f"http://{self.current_proxy_url}",
                "https": f"http://{self.current_proxy_url}",
            }
            self.session.proxies = proxy_dict
        else:
            self.current_proxy_url = None
            self.session.proxies = {}

    def change_proxy(self):
        if not self.proxies_list:
            self.logger("ERROR: No hay proxies disponibles", self.account_id, self.config.email)
            return
        
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies_list)
        self.current_proxy_url = self.proxies_list[self.current_proxy_index]
        proxy_display = self.current_proxy_url.split('@')[-1] if '@' in self.current_proxy_url else self.current_proxy_url
        self.logger(f"🔄 ROTACIÓN PROXY → {proxy_display}", self.account_id, self.config.email)
        self._initialize_proxy_session()

    def check_account_updates_from_db(self):
        """✅ VERSIÓN LIGERA - Solo proxies"""
        try:
            response = supabase.table("cuentas_bot").select("proxies").eq("id", self.account_id).execute()
            if response.data and len(response.data) > 0:
                db_record = response.data[0]
                
                db_proxies_str = db_record.get('proxies', '')
                db_proxies_list = [p.strip() for p in db_proxies_str.split(',') if p.strip()] if db_proxies_str else []
                
                if set(db_proxies_list) != set(self.proxies_list):
                    self.logger(f"📦 Proxies actualizados: {len(db_proxies_list)}", self.account_id, self.config.email)
                    self.proxies_list = db_proxies_list
                    self._initialize_proxy_session()
                
                self.last_proxy_check = time.time()
        except Exception as e:
            self.logger(f"Error consultando proxies: {e}", self.account_id, self.config.email)

    def is_account_active_in_db(self) -> bool:
        try:
            response = supabase.table("cuentas_bot").select("is_active").eq("id", self.account_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('is_active', False)
            return False
        except Exception as e:
            self.logger(f"Error verificando estado: {e}", self.account_id, self.config.email)
            return True

    def init(self):
        self._initialize_proxy_session()
        self.login()
        self.init_current_data()
        self.init_csrf_and_cookie()

    def login(self):
        self.logger("🔐 LOGIN", self.account_id, self.config.email)
        try:
            response = self.session.get(
                f"{self.url}/users/sign_in",
                headers={COOKIE_HEADER: "", REFERER: f"{self.url}/users/sign_in", **DOCUMENT_HEADERS},
                timeout=12
            )
            response.raise_for_status()
        except Exception as e:
            self.logger(f"❌ Login GET falló: {type(e).__name__}", self.account_id, self.config.email)
            raise
        cookies = response.headers.get(SET_COOKIE)
        try:
            response = self.session.post(
                f"{self.url}/users/sign_in",
                headers={
                    **DEFAULT_HEADERS,
                    X_CSRF_TOKEN_HEADER: Bot.get_csrf(response),
                    COOKIE_HEADER: cookies,
                    ACCEPT: "*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript",
                    REFERER: f"{self.url}/users/sign_in",
                    CONTENT_TYPE: "application/x-www-form-urlencoded; charset=UTF-8",
                },
                data=urlencode({
                    "user[email]": self.config.email,
                    "user[password]": self.config.password,
                    "policy_confirmed": "1",
                    "commit": "Sign In",
                }),
                timeout=12
            )
            response.raise_for_status()
            self.logger("✅ Login exitoso", self.account_id, self.config.email)
        except Exception as e:
            self.logger(f"❌ Login POST falló: {type(e).__name__}", self.account_id, self.config.email)
            raise
        self.cookie = response.headers.get(SET_COOKIE)

    def init_current_data(self):
        self.logger("Get current appointment", self.account_id, self.config.email)
        response = self.session.get(self.url, headers={**self.headers(), **DOCUMENT_HEADERS}, timeout=12)
        response.raise_for_status()
        applications = BeautifulSoup(response.text, HTML_PARSER).find_all("div", {"class": "application"})
        if not applications:
            raise NoScheduleIdException()
        schedule_ids = {}
        for application in applications:
            schedule_id_match = re.search(r"\d+", str(application.find("a")))
            if not schedule_id_match:
                continue
            schedule_id = schedule_id_match.group(0)
            description = "  ".join([x.get_text() for x in application.find_all("td")][0:4])
            appointment_datetime = application.find("p", {"class": "consular-appt"})
            if appointment_datetime:
                appointment_match = re.search(r"\d{1,2} \w+?, \d{4}, \d{1,2}:\d{1,2}", appointment_datetime.get_text())
                if appointment_match:
                    appointment_datetime = datetime.strptime(appointment_match.group(0), "%d %B, %Y, %H:%M")
                else:
                    appointment_datetime = None
            else:
                appointment_datetime = None
            schedule_ids[schedule_id] = Appointment(schedule_id, description, appointment_datetime)
        if not self.config.schedule_id and schedule_ids:
            self.config.schedule_id = next(iter(schedule_ids))
        if self.config.schedule_id and self.config.schedule_id in schedule_ids:
            self.appointment_datetime = schedule_ids[self.config.schedule_id].appointment_datetime
        if self.appointment_datetime and self.appointment_datetime.date() <= self.config.min_date:
            raise AppointmentDateLowerMinDate()

    def init_csrf_and_cookie(self):
        self.logger("Init csrf", self.account_id, self.config.email)
        response = self.load_change_appointment_page()
        self.cookie = response.headers.get(SET_COOKIE)
        self.csrf = Bot.get_csrf(response)

    def get_available_locations(self, element_id: str) -> dict[str, str]:
        locations = (
            BeautifulSoup(self.load_change_appointment_page().text, HTML_PARSER)
            .find("select", {"id": element_id})
            .find_all("option")
        )
        facility_id_to_location = {}
        for location in locations:
            if location["value"]:
                facility_id_to_location[location["value"]] = location.text
        return facility_id_to_location

    def load_change_appointment_page(self) -> Response:
        response = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={
                **self.headers(),
                **DOCUMENT_HEADERS,
                **SEC_FETCH_USER_HEADERS,
                REFERER: f"{self.url}/schedule/{self.config.schedule_id}/continue_actions",
            },
            timeout=12
        )
        response.raise_for_status()
        return response

    def get_available_dates(self) -> list[str]:
        # ✅ MOSTRAR EMAIL CUANDO BUSCA FECHAS
        self.logger("📅 CONSULTANDO FECHAS...", self.account_id, self.config.email)
        response = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.facility_id}.json?appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12
        )
        response.raise_for_status()
        data = response.json()
        dates = [x["date"] for x in data]
        dates.sort()
        if dates:
            # ✅ MOSTRAR EMAIL Y CANTIDAD DE FECHAS
            self.logger(f"✓ Fechas encontradas: {len(dates)} disponibles", self.account_id, self.config.email)
        return dates

    def get_available_times(self, available_date: str) -> list[str]:
        # ✅ MOSTRAR EMAIL CUANDO BUSCA HORARIOS
        self.logger(f"⏰ Buscando horarios para {available_date}", self.account_id, self.config.email)
        response = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.facility_id}.json?date={available_date}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12
        )
        response.raise_for_status()
        data = response.json()
        times = data["available_times"] or data["business_times"]
        times.sort()
        if times:
            # ✅ MOSTRAR EMAIL Y HORARIOS ENCONTRADOS
            self.logger(f"✓ Horarios: {len(times)} disponibles para {available_date}", self.account_id, self.config.email)
        return times

    def get_available_times_parallel(self, available_dates: List[str]) -> Dict[str, List[str]]:
        results = {}
        futures = {}
        
        for date_str in available_dates:
            future = self.executor.submit(self.get_available_times, date_str)
            futures[future] = date_str
        
        for future in as_completed(futures):
            date_str = futures[future]
            try:
                results[date_str] = future.result()
            except Exception as e:
                self.logger(f"Error obteniendo tiempos para {date_str}: {e}", self.account_id, self.config.email)
                results[date_str] = []
        
        return results

    def get_asc_available_dates(self, available_date: Optional[str] = None, available_time: Optional[str] = None) -> list[str]:
        self.logger(f"📸 Buscando fechas ASC...", self.account_id, self.config.email)
        response = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/days/{self.config.asc_facility_id}.json?&consulate_id={self.config.facility_id}&consulate_date={available_date if available_date else ''}&consulate_time={available_time if available_time else ''}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12
        )
        response.raise_for_status()
        data = response.json()
        dates = [x["date"] for x in data]
        dates.sort()
        return dates

    def get_asc_available_times(self, asc_available_date: str, available_date: Optional[str] = None, available_time: Optional[str] = None) -> list[str]:
        response = self.session.get(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment/times/{self.config.asc_facility_id}.json?date={asc_available_date}&consulate_id={self.config.schedule_id}&consulate_date={available_date if available_date else ''}&consulate_time={available_time if available_time else ''}&appointments[expedite]=false",
            headers={**self.headers(), **JSON_HEADERS, REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment"},
            timeout=12
        )
        response.raise_for_status()
        data = response.json()
        times = data["available_times"] or data["business_times"]
        times.sort()
        return times

    def book(self, available_date: str, available_time: str, asc_available_date: Optional[str], asc_available_time: Optional[str]):
        # ✅ MOSTRAR EMAIL CUANDO INTENTA RESERVAR
        self.logger(f"🎯 INTENTO RESERVA: {available_date} {available_time}", self.account_id, self.config.email)
        body = {
            "authenticity_token": self.csrf,
            "confirmed_limit_message": "1",
            "use_consulate_appointment_capacity": "true",
            "appointments[consulate_appointment][facility_id]": self.config.facility_id,
            "appointments[consulate_appointment][date]": available_date,
            "appointments[consulate_appointment][time]": available_time,
        }
        if self.config.need_asc and asc_available_date and asc_available_time:
            body.update({
                "appointments[asc_appointment][facility_id]": self.config.asc_facility_id,
                "appointments[asc_appointment][date]": asc_available_date,
                "appointments[asc_appointment][time]": asc_available_time,
            })
        
        return self.session.post(
            f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            headers={
                **self.headers(),
                **DOCUMENT_HEADERS,
                **SEC_FETCH_USER_HEADERS,
                CONTENT_TYPE: "application/x-www-form-urlencoded",
                "Origin": f"https://{HOST}",
                REFERER: f"{self.url}/schedule/{self.config.schedule_id}/appointment",
            },
            data=urlencode(body),
            timeout=12
        )

    def send_telegram_message(self, token: str, chat_id: str, message: str):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger(f"Telegram error: {e}", self.account_id, self.config.email)
            return False

    def process(self):
        """⚡ ULTRA AGRESIVO - OPTIMIZADO PARA I7"""
        self.logger("=" * 70, self.account_id, self.config.email)
        self.logger(f"🚀 INICIANDO - {self.config.email}", self.account_id, self.config.email)
        self.logger(f"📋 ID: {self.account_id} | País: {self.config.country.upper()}", self.account_id, self.config.email)
        self.logger(f"📦 Proxies: {len(self.proxies_list)}", self.account_id, self.config.email)
        self.logger("=" * 70, self.account_id, self.config.email)
        
        self.last_proxy_check = time.time()
        last_db_check = time.time()
        
        while not self.cita_programada:
            try:
                current_time = time.time()
                
                if current_time - last_db_check >= 60:
                    if not self.is_account_active_in_db():
                        self.logger("⚠️ Cuenta desactivada. Deteniendo...", self.account_id, self.config.email)
                        return
                    self.check_account_updates_from_db()
                    last_db_check = current_time
                
                self.init()
                
                while not self.cita_programada:
                    current_time = time.time()
                    if current_time - last_db_check >= 60:
                        if not self.is_account_active_in_db():
                            self.logger("⚠️ Cuenta desactivada. Deteniendo...", self.account_id, self.config.email)
                            return
                        self.check_account_updates_from_db()
                        last_db_check = current_time
                    
                    time.sleep(BOOKING_DELAY)
                    
                    try:
                        available_dates = self.get_available_dates()
                    except Exception as err:
                        self.logger(f"❌ Error en fechas: {type(err).__name__}. Rotando...", self.account_id, self.config.email)
                        self.change_proxy()
                        break
                    
                    if not available_dates:
                        continue
                    
                    valid_dates = [
                        d for d in available_dates
                        if datetime.strptime(d, "%Y-%m-%d").date() > self.config.min_date
                        and (not self.config.max_date or datetime.strptime(d, "%Y-%m-%d").date() <= self.config.max_date)
                        and (not self.appointment_datetime or datetime.strptime(d, "%Y-%m-%d").date() < self.appointment_datetime.date())
                    ]
                    
                    if not valid_dates:
                        continue
                    
                    times_by_date = self.get_available_times_parallel(valid_dates)
                    
                    for available_date_str in valid_dates:
                        available_times = times_by_date.get(available_date_str, [])
                        if not available_times:
                            continue
                        
                        for available_time_str in available_times:
                            asc_available_date_str = None
                            asc_available_time_str = None
                            
                            if self.config.need_asc:
                                available_date = datetime.strptime(available_date_str, "%Y-%m-%d").date()
                                min_asc_date = available_date - timedelta(days=7)
                                found_asc = False
                                
                                for k, v in self.asc_dates.items():
                                    if min_asc_date <= datetime.strptime(k, "%Y-%m-%d").date() < available_date and len(v) > 0:
                                        asc_available_date_str = k
                                        asc_available_time_str = random.choice(v)
                                        found_asc = True
                                        break
                                
                                if not found_asc:
                                    try:
                                        asc_dates = self.get_asc_available_dates(available_date_str, available_time_str)
                                        if asc_dates:
                                            asc_available_date_str = asc_dates[0]
                                            asc_times = self.get_asc_available_times(asc_available_date_str, available_date_str, available_time_str)
                                            if asc_times:
                                                asc_available_time_str = random.choice(asc_times)
                                    except Exception as e:
                                        self.logger(f"Error ASC: {e}", self.account_id, self.config.email)
                                        continue
                            
                            try:
                                response_book = self.book(available_date_str, available_time_str, asc_available_date_str, asc_available_time_str)
                                
                                if "appointment/instructions" in response_book.url:
                                    self.logger("✓ Redirección OK", self.account_id, self.config.email)
                                    self.init_current_data()
                                    
                                    if self.appointment_datetime and self.appointment_datetime.date() == datetime.strptime(available_date_str, "%Y-%m-%d").date():
                                        self.logger("✅✅✅ ¡¡¡CITA AGENDADA!!! ✅✅✅", self.account_id, self.config.email)
                                        nombre_pais = COUNTRIES.get(self.config.country, self.config.country.upper())
                                        
                                        try:
                                            loc_consulado = self.get_available_locations("appointments_consulate_appointment_facility_id")
                                            sede_consular = loc_consulado.get(self.config.facility_id, self.config.facility_id)
                                        except:
                                            sede_consular = f"ID: {self.config.facility_id}"
                                        
                                        log_telegram = (
                                            "✅ **¡CITA PROGRAMADA!**\n\n"
                                            f"🌎 **País**: {nombre_pais}\n"
                                            f"👤 **Usuario**: `{self.config.email}`\n"
                                            f"🏛️ **Sede**: {sede_consular}\n"
                                            f"📅 **Fecha**: {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}\n"
                                        )
                                        if self.config.need_asc and asc_available_date_str:
                                            log_telegram += f"📸 **CAS**: {asc_available_date_str} {asc_available_time_str}\n"
                                        
                                        if self.config.telegram_token and self.config.telegram_chat_id:
                                            self.send_telegram_message(self.config.telegram_token, self.config.telegram_chat_id, log_telegram)
                                        
                                        print("\n" + "="*70)
                                        print("ACTUALIZANDO BD - DESACTIVANDO CUENTA")
                                        print("="*70)
                                        
                                        success = self.config.update_status_in_db(
                                            is_active=False,
                                            status="Cita Agendada",
                                            appointment_date=self.appointment_datetime.strftime("%Y-%m-%d %H:%M")
                                        )
                                        
                                        if success:
                                            self.logger("✅✅✅ CUENTA DESACTIVADA CORRECTAMENTE", self.account_id, self.config.email)
                                        else:
                                            self.logger("⚠️⚠️⚠️ FALLO AL DESACTIVAR", self.account_id, self.config.email)
                                        
                                        self.cita_programada = True
                                        break
                                    else:
                                        continue
                                else:
                                    self.logger("❌ Redirección falló", self.account_id, self.config.email)
                                    continue
                            
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

# ================= FUNCIÓN PRINCIPAL =================
def run_account_thread_standalone(account_data: dict, logger: ThreadLogger):
    account_id = account_data['id']
    email = account_data.get('email', 'Unknown')
    try:
        config = AccountConfig(account_data)
        if not config.is_active:
            logger(f"Cuenta no está activa", account_id, email)
            return
        bot = Bot(config, logger, account_id)
        bot.process()
    except Exception as e:
        logger(f"❌ Error: {e}", account_id, email)
        try:
            supabase.table("cuentas_bot").update({"status": "Error", "updated_at": datetime.now().isoformat()}).eq("id", account_id).execute()
        except:
            pass

def get_active_accounts(logger):
    try:
        response = supabase.table("cuentas_bot").select("*").eq("is_active", True).execute()
        return response.data if response.data else []
    except Exception as e:
        logger(f"❌ Error Supabase: {e}")
        return []

def main():
    global active_threads
    logger = ThreadLogger(LOG_FILE, LOG_FORMAT)
    
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger("=" * 80)
        logger(f"🔄 CICLO: {current_time}")
        logger("=" * 80)
        
        accounts = get_active_accounts(logger)
        
        if accounts:
            logger(f"✅ Cuentas activas: {len(accounts)}")
            new_accounts = [acc for acc in accounts if acc['id'] not in active_threads]
            
            if new_accounts:
                logger(f"🆕 Nuevas cuentas: {len(new_accounts)}")
                for acc in new_accounts:
                    account_id = acc['id']
                    email = acc.get('email', 'Unknown')
                    
                    thread = threading.Thread(
                        target=run_account_thread_standalone,
                        args=(acc, logger),
                        name=f"Account-{account_id}",
                        daemon=True
                    )
                    thread.start()
                    
                    active_threads[account_id] = {
                        'thread': thread,
                        'email': email,
                        'started_at': datetime.now()
                    }
                    logger(f"🚀 Hilo iniciado: {email}")
            
            finished = []
            for acc_id, info in list(active_threads.items()):
                if not info['thread'].is_alive():
                    elapsed = datetime.now() - info['started_at']
                    logger(f"✅ Finalizado: {info['email']} - {elapsed}")
                    finished.append(acc_id)
            
            for acc_id in finished:
                del active_threads[acc_id]
            
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
