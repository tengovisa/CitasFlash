import re
import json
from pathlib import Path
from datetime import datetime

API_LOG = Path('/root/api_control.log')
NEXUS_LOG = Path('/root/log_nexus.txt')
OUT = Path('/root/error_monitor_latest.log')

patterns = [
    (r'IndentationError', 'ERROR_CRITICO_API', 'El backend no puede iniciar por error de indentación en Python.'),
    (r'SyntaxError', 'ERROR_CRITICO_API', 'El backend no puede iniciar por error de sintaxis en Python.'),
    (r'502 Bad Gateway', 'NGINX_502', 'Nginx no encuentra el backend activo o el backend cayó.'),
    (r'403 Forbidden', 'AUTH_403', 'API key incorrecta o endpoint protegido sin credenciales válidas.'),
    (r'422', 'VALIDACION_422', 'La petición no cumple validación del backend o faltan campos requeridos.'),
    (r'Could not find the .* column', 'SCHEMA_COLUMN', 'El backend intenta usar una columna que no existe en Supabase.'),
    (r'Empty reply from server', 'PROXY_EMPTY_REPLY', 'El proxy respondió vacío; normalmente proxy muerto, saturado o incompatible.'),
    (r'ProxyError', 'PROXY_ERROR', 'Fallo de conexión con proxy.'),
    (r'407', 'PROXY_AUTH', 'El proxy requiere autenticación o credenciales inválidas.'),
    (r'403', 'AIS_403', 'AIS o un proxy devolvió acceso denegado; posible bloqueo temporal o fingerprint.'),
    (r'HTTP 500|Internal Server Error', 'SERVER_500', 'Error interno del backend o del servicio remoto.'),
    (r'address already in use', 'PORT_IN_USE', 'El puerto ya está ocupado por otro proceso.'),
]

def tail_lines(path, n=200):
    if not path.exists():
        return []
    try:
        return path.read_text(encoding='utf-8', errors='ignore').splitlines()[-n:]
    except:
        return []

def classify(lines, source):
    out = []
    text = "\n".join(lines)
    for pat, code, meaning in patterns:
        if re.search(pat, text, re.I):
            out.append({
                "source": source,
                "code": code,
                "meaning": meaning,
                "pattern": pat
            })
    return out

api_lines = tail_lines(API_LOG, 200)
nexus_lines = tail_lines(NEXUS_LOG, 200)

report = {
    "timestamp": datetime.now().isoformat(),
    "api_log_exists": API_LOG.exists(),
    "nexus_log_exists": NEXUS_LOG.exists(),
    "findings": classify(api_lines, "api_control.log") + classify(nexus_lines, "log_nexus.txt"),
    "api_tail": api_lines[-30:],
    "nexus_tail": nexus_lines[-30:]
}

OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
