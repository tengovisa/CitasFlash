"""
TengoVisa RD — Google Calendar Sync
Lee citas de tengovisa@gmail.com y crea leads en el CRM
"""
import os, json, requests
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account

CREDS_FILE = '/root/google_calendar_credentials.json'
CALENDAR_ID = 'tengovisa@gmail.com'
CRM_API = 'http://localhost:8001'
CRM_KEY = 'TengoVisa2026API'

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    return build('calendar', 'v3', credentials=creds)

def sync_citas():
    """Lee eventos de hoy y mañana y los sincroniza al CRM"""
    try:
        service = get_calendar_service()
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f'✅ {len(events)} eventos encontrados')
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            titulo = event.get('summary', 'Cita sin título')
            descripcion = event.get('description', '')
            attendees = event.get('attendees', [])
            
            # Extraer email del cliente
            cliente_email = None
            for att in attendees:
                if att.get('email') != 'tengovisa@gmail.com':
                    cliente_email = att.get('email')
                    break
            
            print(f'  📅 {start[:16]} | {titulo} | {cliente_email or "sin email"}')
            
            # Crear lead en CRM si hay email
            if cliente_email:
                try:
                    r = requests.post(f'{CRM_API}/leads',
                        headers={'x-api-key': CRM_KEY, 'Content-Type': 'application/json'},
                        json={
                            'nombre': titulo.split(' ')[0] if titulo else 'Lead Calendar',
                            'apellido': '',
                            'email': cliente_email,
                            'origen': 'google_calendar',
                            'estado': 'nuevo',
                            'etapa': 'consulta_agendada',
                            'notas': f'Cita agendada: {start[:16]} | {titulo}\n{descripcion[:200]}',
                            'prioridad': 'alta'
                        }, timeout=10)
                    if r.status_code == 200:
                        print(f'    ✅ Lead CRM creado')
                except Exception as e:
                    print(f'    ❌ Error CRM: {e}')
        
        return events
    except Exception as e:
        print(f'❌ Error Calendar: {e}')
        return []

def get_citas_hoy():
    """Retorna las citas de hoy para el dashboard"""
    try:
        service = get_calendar_service()
        import pytz
        tz = pytz.timezone('America/Santo_Domingo')
        hoy = datetime.now(tz)
        inicio = hoy.replace(hour=0, minute=0, second=0).astimezone(pytz.utc)
        fin = hoy.replace(hour=23, minute=59, second=59).astimezone(pytz.utc)
        
        events = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=inicio.isoformat(),
            timeMax=fin.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])
        
        return [{
            'id': e.get('id'),
            'titulo': e.get('summary','Sin título'),
            'inicio': e['start'].get('dateTime', e['start'].get('date',''))[:16],
            'descripcion': e.get('description','')[:200],
            'email_cliente': next((a['email'] for a in e.get('attendees',[]) if a.get('email') != CALENDAR_ID), None)
        } for e in events]
    except Exception as e:
        print(f'Error: {e}')
        return []

if __name__ == '__main__':
    print('=== SYNC GOOGLE CALENDAR ===')
    sync_citas()
