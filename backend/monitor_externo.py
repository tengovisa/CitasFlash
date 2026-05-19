import os, requests
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client
from datetime import datetime

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def send_telegram(msg):
    token = '8612004045:AAGFmqfUsmefl0YoR2PGTyZd26YDvZQm0Zo'
    chat_id = '1193245321'
    requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
        json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}, timeout=10)

def check():
    cuentas = sb.table('cuentas_citafast').select('id,email,password,schedule_id,proxies,last_appointment_date,status').execute().data
    for a in cuentas:
        try:
            r = requests.post('http://localhost:8000/cuentas/validar',
                headers={'x-api-key': 'CitaFast2026Bot2'},
                json={'email': a['email'], 'password': a['password'],
                      'schedule_id': a['schedule_id'], 'proxies': a.get('proxies','')},
                timeout=25)
            d = r.json()
            if not d.get('valid'): continue
            fecha_ais = d.get('fecha_actual','')
            fecha_bd = a.get('last_appointment_date','')
            if fecha_ais and fecha_ais != 'Sin cita asignada' and fecha_ais != fecha_bd and a['status'] != 'Cita Agendada':
                msg = (f"🚨 *Alerta Perfil agendado fuera de Nexus*\n\n"
                       f"👤 `{a['email']}`\n"
                       f"📅 *Fecha AIS:* {fecha_ais}\n"
                       f"📋 *Anterior en BD:* {fecha_bd or 'Sin cita'}")
                send_telegram(msg)
                sb.table('cuentas_citafast').update({
                    'last_appointment_date': fecha_ais,
                    'status': 'Cita Agendada Externa',
                    'is_active': False
                }).eq('id', a['id']).execute()
                print(f'Detectada: {a["email"]} — {fecha_ais}')
        except Exception as e:
            print(f'Error {a["email"]}: {e}')

if __name__ == '__main__':
    now = datetime.now()
    if now.weekday() == 2 and 7 <= now.hour < 9:
        print(f'Ejecutando: {now.strftime("%H:%M")}')
        check()
    else:
        print('Fuera de horario')
