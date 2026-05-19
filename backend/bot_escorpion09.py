#!/usr/bin/env python3
"""Bot rápido para AIS – busca y agenda la mejor cita en un rango (cuenta escorpion09)"""
from curl_cffi import requests
from bs4 import BeautifulSoup
import time
import sys
from datetime import datetime

# ========== CONFIGURACIÓN ==========
EMAIL = "Maireni2412@gmail.com"
PASSWORD = "escorpion09"
SCHEDULE_ID = "74026176"
FACILITY_ID = "138"
MIN_DATE = "2027-01-01"    # Fecha mínima (cambia si quieres)
MAX_DATE = "2027-12-31"    # Fecha máxima
# ===================================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}", flush=True)

def login(session):
    log("🔐 Logging in...")
    url = "https://ais.usvisa-info.com/en-do/niv/users/sign_in"
    r = session.get(url, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find('meta', {'name': 'csrf-token'})['content']
    data = {
        'user[email]': EMAIL,
        'user[password]': PASSWORD,
        'policy_confirmed': '1',
        'commit': 'Sign In'
    }
    session.post(url, data=data, headers={'X-CSRF-Token': csrf}, timeout=15)
    log("✅ Login OK")

def get_dates(session):
    url = f"https://ais.usvisa-info.com/en-do/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
    r = session.get(url, headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    return sorted([x['date'] for x in data if 'date' in x])

def get_times(session, date_str):
    url = f"https://ais.usvisa-info.com/en-do/niv/schedule/{SCHEDULE_ID}/appointment/times/{FACILITY_ID}.json?date={date_str}&appointments[expedite]=false"
    r = session.get(url, headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    return sorted(data.get('available_times', []) or data.get('business_times', []))

def book(session, date_str, time_str):
    # Obtener CSRF fresco desde la página de appointment
    appt_url = f"https://ais.usvisa-info.com/en-do/niv/schedule/{SCHEDULE_ID}/appointment"
    r = session.get(appt_url, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find('meta', {'name': 'csrf-token'})['content']
    data = {
        'authenticity_token': csrf,
        'confirmed_limit_message': '1',
        'use_consulate_appointment_capacity': 'true',
        f'appointments[consulate_appointment][facility_id]': FACILITY_ID,
        f'appointments[consulate_appointment][date]': date_str,
        f'appointments[consulate_appointment][time]': time_str,
    }
    headers = {
        'X-CSRF-Token': csrf,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://ais.usvisa-info.com',
        'Referer': appt_url,
    }
    resp = session.post(appt_url, data=data, headers=headers, allow_redirects=False, timeout=20)
    # Éxito si redirige a /appointment/instructions
    return resp.status_code == 302 and 'instructions' in resp.headers.get('Location', '')

def main():
    log("🚀 Iniciando bot (cuenta Maireni2412)")
    session = requests.Session(impersonate="chrome120")
    session.timeout = 30
    try:
        login(session)
    except Exception as e:
        log(f"❌ Error en login: {e}")
        return

    ciclo = 0
    while True:
        inicio = time.time()
        try:
            dates = get_dates(session)
            if not dates:
                log("⏳ Sin fechas disponibles")
                time.sleep(max(0, 0.7 - (time.time() - inicio)))
                continue

            # Filtrar por rango
            valid = [d for d in dates if MIN_DATE <= d <= MAX_DATE]
            if not valid:
                log(f"📅 Rango {MIN_DATE}..{MAX_DATE} no alcanzado. Primera disponible: {dates[0]}")
                time.sleep(max(0, 0.7 - (time.time() - inicio)))
                continue

            best_date = valid[0]
            log(f"🎯 Mejor fecha en rango: {best_date}")

            times = get_times(session, best_date)
            if not times:
                log(f"⏰ No hay horarios para {best_date}")
                time.sleep(max(0, 0.7 - (time.time() - inicio)))
                continue

            best_time = times[0]
            log(f"⏰ Horario elegido: {best_time}")

            if book(session, best_date, best_time):
                log(f"✅✅✅ ¡CITA AGENDADA! {best_date} {best_time} ✅✅✅")
                break  # Termina el bot
            else:
                log("❌ Falló la reserva, reintentando...")
                time.sleep(1)
        except Exception as e:
            log(f"⚠️ Error en ciclo: {e}")
            time.sleep(0.7)

        # Control de ciclo (~0.7 s)
        elapsed = time.time() - inicio
        if elapsed < 0.7:
            time.sleep(0.7 - elapsed)
        ciclo += 1
        if ciclo % 100 == 0:
            log(f"🔄 Ciclos completados: {ciclo}")

if __name__ == "__main__":
    main()
