#!/usr/bin/env python3
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

def get_schedule_id_from_profile(email, password):
    session = requests.Session(impersonate="chrome120")
    
    # 1. Login
    r1 = session.get("https://ais.usvisa-info.com/en-do/niv/users/sign_in", timeout=15)
    csrf = BeautifulSoup(r1.text, "html.parser").find("meta", {"name": "csrf-token"})["content"]
    
    r2 = session.post("https://ais.usvisa-info.com/en-do/niv/users/sign_in",
        data={"user[email]": email, "user[password]": password, "policy_confirmed": "1", "commit": "Sign In"},
        headers={"X-CSRF-Token": csrf}, timeout=15)
    
    # 2. Buscar schedule_id en el perfil
    r3 = session.get("https://ais.usvisa-info.com/en-do/niv", timeout=15)
    match = re.search(r'/schedule/(\d+)/', r3.text)
    
    if match:
        schedule_id = match.group(1)
        print(f"✅ schedule_id encontrado: {schedule_id}")
        return schedule_id
    else:
        print("❌ No se encontró schedule_id. ¿La cuenta tiene cita activa?")
        return None

# Usar credenciales de tu cuenta
get_schedule_id_from_profile("toledocuestayasociados@gmail.com", "TU_PASSWORD")
