import requests, json
from datetime import datetime, timedelta

SUPA = "https://lbttnpcpqdjmpktuoegs.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxidHRucGNwcWRqbXBrdHVvZWdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2NjAyNDEsImV4cCI6MjA5MTIzNjI0MX0.GsuZUkJIOmOITdl0hATt_P603a7vaI01j72nzG94O60"
WA_TOKEN = ""  # Necesitas WhatsApp Business API
PHONE = "18499189998"

# Revisar leads de los ultimos 6 minutos
hace6min = (datetime.utcnow() - timedelta(minutes=6)).isoformat()
r = requests.get(
    f"{SUPA}/rest/v1/leads?created_at=gt.{hace6min}&select=nombre,whatsapp,origen",
    headers={"apikey": KEY, "Accept-Profile": "crm"}
)
leads = r.json()
if leads:
    for l in leads:
        print(f"NUEVO LEAD: {l.get('nombre')} - {l.get('whatsapp')} - {l.get('origen')}")
