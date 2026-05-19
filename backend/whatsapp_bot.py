"""
TengoVisa RD — Bot WhatsApp con Twilio
Captura leads 24/7 en el CRM
"""
import os, json, subprocess
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('/root/.env.tengovisa')

app = Flask(__name__)

# Memoria de conversación por usuario (en memoria RAM)
conversaciones = {}  # {phone: {"intentos": 0, "ultimo_msg": "", "escalado": False}}

def get_sesion(phone):
    if phone not in conversaciones:
        conversaciones[phone] = {"intentos_sin_entender": 0, "escalado": False, "historial": []}
    return conversaciones[phone]

def reset_sesion(phone):
    conversaciones[phone] = {"intentos_sin_entender": 0, "escalado": False, "historial": []}

CRM_API = "http://localhost:8001"
CRM_KEY = "TengoVisa2026API"
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_NUM = os.getenv('TWILIO_WHATSAPP_NUMBER', '+14155238886')

def get_config():
    try:
        with open("/root/bot_config.json") as f:
            return json.load(f)
    except:
        return {
            "hora_inicio": 22, "hora_fin": 8,
            "precio_eval": 2000, "precio_ds160": 5000,
            "precio_visa": 15000, "precio_cita": 8000,
            "tel_asesor": "+18499189998"
        }

def esta_en_horario_bot():
    """
    Bot activo:
    - Lunes-Viernes: 6:00 PM en adelante hasta 8:30 AM siguiente dia
    - Sabado: 3:00 PM en adelante
    - Domingo: todo el dia
    - Lunes madrugada hasta 8:30 AM: activo (viene del fin de semana)
    """
    try:
        import pytz
        tz = pytz.timezone('America/Santo_Domingo')
        now = __import__('datetime').datetime.now(tz)
        dia = now.weekday()  # 0=lun...5=sab,6=dom
        h = now.hour + now.minute / 60.0
    except:
        import datetime
        now = datetime.datetime.utcnow()
        h = ((now.hour - 4) % 24) + now.minute / 60.0
        dia = now.weekday()

    # Domingo — siempre activo
    if dia == 6:
        return True
    # Sabado desde 3pm — activo
    if dia == 5 and h >= 15.0:
        return True
    # Lunes madrugada hasta 8:30am — activo (viene del domingo)
    if dia == 0 and h < 8.5:
        return True
    # Martes-Viernes madrugada hasta 8:30am — activo
    if dia in [1, 2, 3, 4] and h < 8.5:
        return True
    # Lunes-Viernes desde 6pm — activo
    if dia in [0, 1, 2, 3, 4] and h >= 18.0:
        return True
    # Todo lo demas = horario laboral, asesor responde
    return False
def get_horario_texto():
    """Mensaje cuando el asesor está disponible"""
    cfg = get_config()
    tel = cfg.get('tel_asesor', '+18499189998')
    return f"👋 ¡Hola! Tu mensaje fue recibido.\n\n⏰ Nuestro equipo está en línea ahora.\nUn asesor te responderá en breve.\n\n📞 También puedes llamar: {tel}\n\n_TengoVisa RD_ 🇩🇴"

def crear_lead_crm(nombre, telefono, mensaje, origen="whatsapp"):
    """Crea lead en el CRM automáticamente"""
    import requests as req
    try:
        r = req.post(f"{CRM_API}/leads",
            headers={"x-api-key": CRM_KEY, "Content-Type": "application/json"},
            json={
                "nombre": nombre or "Lead WhatsApp",
                "apellido": "",
                "whatsapp": telefono,
                "email": "",
                "origen": origen,
                "estado": "nuevo",
                "notas": f"Bot WA: {mensaje[:200]}",
                "etapa": "captacion",
                "prioridad": "normal",
                "created_at": datetime.now().isoformat()
            }, timeout=10)
        data = r.json()
        print(f"✅ Lead CRM: {data.get('id','?')} | {telefono} | {nombre}")
        return data.get('id')
    except Exception as e:
        print(f"❌ Lead error: {e}")
    return None

def get_respuestas_db():
    """Lee respuestas desde JSON — editable desde el CRM"""
    try:
        with open("/root/bot_respuestas.json") as f:
            return json.load(f).get("respuestas", [])
    except:
        return []

def get_respuesta(msg):
    m = msg.lower().strip()
    respuestas = get_respuestas_db()
    
    # Buscar por palabras clave
    for r in respuestas:
        keywords = r.get("palabras_clave", [])
        if any(kw in m for kw in keywords):
            return r.get("respuesta", "")
    
    return None  # No encontrado → escalada


def get_respuesta_legacy(msg):
    cfg = get_config()
    pe = f"RD${cfg.get('precio_eval',2500):,}"
    pp = f"RD${cfg.get('precio_pareja',4000):,}"
    pv = f"RD${cfg.get('precio_visa',30000):,}"
    pc = f"RD${cfg.get('precio_cita',5000):,}"
    tel = cfg.get('tel_asesor', '+18499189998')
    cal = cfg.get('calendario_url', 'https://calendar.app.google/h8E33fxZsJefNLvD6')
    eval_url = "https://crm.tengovisard.com/evaluacion/"

    m = msg.lower().strip()

    # SALUDOS
    if any(x in m for x in ['hola','buenos','buenas','hi','hello','saludos','buen dia','buenas tardes','buenas noches']):
        return f"""👋 ¡Hola! Gracias por contactar a *TengoVisa RD* 🇩🇴🇺🇸

📅 Te ayudamos con:
- Visa por primera vez
- Renovación de visa
- Adelantar cita para 2026

Para orientarte, indícanos:
1️⃣ ¿Qué necesitas?
2️⃣ ¿Tienes pasaporte vigente?
3️⃣ ¿Has tenido visa aprobada o negada?
4️⃣ ¿Cuántas personas aplican?
5️⃣ ¿Solo información o iniciar proceso?

Con estos datos te indicamos el siguiente paso 👇"""

    # PRIMERA VEZ / NUEVA VISA
    if any(x in m for x in ['primera vez','nueva visa','primera','nunca he tenido','nuevo']):
        return f"""🇺🇸 *Visa por Primera Vez — TengoVisa RD*

Te ofrecemos acompañamiento completo:
✅ Llenado del formulario consular (DS-160)
✅ Preparación para la entrevista
✅ Gestión de cita cercana (según disponibilidad)

*Requisitos:*
- Pasaporte vigente
- Documentos según tu perfil

*Inversión:*
💳 Evaluación inicial: *{pe}* (descontable)
💳 Parejas: *{pp}*
💰 Servicio completo: *{pv}* por solicitante

📝 El pago final se realiza al entregar toda la información.

¿Deseas iniciar la evaluación de tu caso ahora?"""

    # RENOVACION
    if any(x in m for x in ['renovar','renovacion','renovación','vencida','vencio','vencio','caducada']):
        return f"""🔄 *Renovación de Visa — TengoVisa RD*

Para renovación manejamos todo el proceso:
✅ Nuevo DS-160
✅ Gestión de cita
✅ Preparación para entrevista

💰 Inversión: *{pv}* por solicitante
📅 Cita: Buscamos la primera disponible 2026

¿Cuándo venció tu visa anterior?"""

    # CITA / ADELANTAR CITA
    if any(x in m for x in ['cita','adelantar','appointment','fecha','cuando','reprogramar','cambiar cita']):
        return f"""📅 *Gestión de Citas Consulares — TengoVisa RD*

Realizamos la gestión según disponibilidad de la Embajada.
Actualmente trabajamos el trimestre 2026.
Buscamos siempre la *primera cita disponible*.

💰 Costo: *{pc}*
✅ Se paga SOLO después de que la cita esté agendada y verificada por usted.

*Para iniciar necesitas:*
- Pasaporte vigente
- DS-160 completado
- Pago MRV realizado

¿Ya tienes estos documentos listos?"""

    # PRECIO / COSTO
    if any(x in m for x in ['precio','costo','cuanto','cuánto','tarifa','cobran','vale','inversion','inversión']):
        return f"""💰 *Tarifas TengoVisa RD 2026:*

📋 Evaluación inicial: *{pe}* (descontable)
👫 Parejas: *{pp}*
🇺🇸 Servicio completo: *{pv}* por solicitante
📅 Solo gestión de cita: *{pc}*

💡 _La evaluación inicial se descuenta si continúa con el proceso completo._

📝 El pago final se realiza después de entregar toda la información requerida.

¿Te interesa algún servicio?"""

    # EVALUACION
    if any(x in m for x in ['evaluacion','evaluación','evalua','perfil','califica','saber si califico']):
        return f"""📋 *Evaluación de Perfil Migratoria*

Completa tu evaluación GRATIS:
👉 {eval_url}

Recibirás en minutos:
✅ Score de probabilidad (0-100)
✅ Análisis IA personalizado
✅ Documentos que necesitas
✅ Recomendación de si aplicar ahora o esperar

💳 Evaluación inicial con asesor: *{pe}* (descontable)

¿Deseas hacer la evaluación ahora?"""

    # AGENDAR / CITA ASESOR
    if any(x in m for x in ['agendar','agenda','cita con','asesor','consulta','reunion','reunión','calendly','calendar']):
        return f"""📅 *Agenda tu Cita de Asesoría*

Para brindarte seguimiento personalizado, registra tus datos:

👉 {cal}

Recibirás confirmación con los detalles.

⚠️ *Este paso es obligatorio para el seguimiento.*
Solo laboramos por cita previa.

📞 Asesor directo: {tel}"""

    # PASAPORTE
    if any(x in m for x in ['pasaporte','passport','renovar pasaporte','pasaporte vencido']):
        return f"""🪪 *Gestión de Pasaporte*

Te ayudamos con tu solicitud digital:
👉 https://crm.tengovisard.com/pasaporte/

También tramitamos renovación de pasaporte dominicano.

¿Tu pasaporte está vigente o necesitas renovarlo primero?"""

    # DS-160
    if any(x in m for x in ['ds160','ds-160','formulario','ds 160','ceac']):
        return f"""📝 *Formulario DS-160*

Completa tu DS-160 con nuestra guía:
👉 https://crm.tengovisard.com/ds160/

✅ Sistema guarda tu progreso
✅ Revisión por asesor incluida
✅ Parte del servicio completo

💰 DS-160 solo: *RD$5,000*"""

    # ESTADO DEL CASO
    if any(x in m for x in ['estado','caso','proceso','como va','cómo va','seguimiento','expediente','codigo','código']):
        return f"""🔍 *Estado de tu Caso*

Para consultar tu caso necesito:
- Tu código *TV-XXXXXX*
- o tu correo electrónico registrado

📊 También puedes ver tu expediente en:
https://crm.tengovisard.com/

¿Cuál es tu código de cliente?"""

    # SI / INICIAR
    if any(x in m for x in ['si','sí','yes','iniciar','comenzar','quiero','interesa','adelante','proceder']):
        return f"""✅ ¡Excelente! Vamos a iniciar.

*Primer paso — Agenda tu cita de asesoría:*
👉 {cal}

O completa tu evaluación online GRATIS:
👉 {eval_url}

📞 También puedes llamarnos: {tel}

_Este paso es obligatorio para brindarte seguimiento personalizado._"""

    # NO / SOLO INFORMACION
    if any(x in m for x in ['no','solo informacion','solo información','información','informacion','info']):
        return f"""ℹ️ Con gusto te informamos.

*Servicios TengoVisa RD:*
- 🇺🇸 Visa B1/B2 primera vez o renovación
- 📅 Gestión de cita consular
- 📝 DS-160 completo
- 🪪 Renovación de pasaporte

*Precios:*
- Evaluación: {pe} | Pareja: {pp}
- Servicio completo: {pv}
- Solo cita: {pc}

¿En qué más puedo ayudarte?"""

    # GRACIAS
    if any(x in m for x in ['gracias','thank','ok','bueno','listo','excelente','perfecto','entendido']):
        return f"""😊 ¡Con mucho gusto!

Recuerda que puedes:
📋 Evaluar tu perfil GRATIS: {eval_url}
📅 Agendar asesoría: {cal}
📞 Llamarnos: {tel}

¡Que tengas un excelente día! 🇩🇴 *TengoVisa RD*"""

    # DEFAULT — no entendió
    return None  # Señal para escalada

def get_respuesta_con_memoria(msg, phone):
    """Maneja la conversación con memoria y escalada"""
    sesion = get_sesion(phone)
    
    # Si ya fue escalado — no responder más automáticamente
    if sesion.get('escalado'):
        return None
    
    respuesta = get_respuesta(msg)
    
    if respuesta is None:
        sesion['intentos_sin_entender'] = sesion.get('intentos_sin_entender', 0) + 1
        
        if sesion['intentos_sin_entender'] == 1:
            # Primer intento fallido — mostrar menú
            cfg = get_config()
            tel = cfg.get('tel_asesor', '+18499189998')
            return f"""🤖 No entendí tu mensaje. Elige una opción:

1️⃣ *visa* — Información de visas
2️⃣ *evaluacion* — Evalúa tu perfil GRATIS
3️⃣ *precio* — Ver tarifas
4️⃣ *cita* — Gestión de citas
5️⃣ *agendar* — Cita con asesor
6️⃣ *estado* — Estado de mi caso

O escribe lo que necesitas con tus propias palabras 👇"""
        
        elif sesion['intentos_sin_entender'] == 2:
            # Segundo intento — ofrecer asesor
            cfg = get_config()
            tel = cfg.get('tel_asesor', '+18499189998')
            return f"""😊 Déjame conectarte con un asesor.

Un miembro de nuestro equipo revisará tu consulta y te responderá pronto.

📞 También puedes llamar directamente: {tel}
📅 Agenda una cita: {cfg.get('calendario_url','https://calendar.app.google/h8E33fxZsJefNLvD6')}

Tu mensaje ha sido registrado ✅"""
        
        else:
            # Tercer intento — escalada definitiva y notificar
            sesion['escalado'] = True
            notificar_asesor(phone, sesion.get('historial', []))
            return None  # No responder más
    
    # Entendió — reset contador
    sesion['intentos_sin_entender'] = 0
    sesion['historial'].append(msg[:100])
    if len(sesion['historial']) > 10:
        sesion['historial'] = sesion['historial'][-10:]
    
    return respuesta

def notificar_asesor(phone, historial):
    """Notifica al asesor cuando el bot no puede ayudar"""
    import requests as req
    try:
        # Crear lead con nota de escalada
        req.post(f"{CRM_API}/leads",
            headers={"x-api-key": CRM_KEY, "Content-Type": "application/json"},
            json={
                "nombre": "Lead escalado bot",
                "whatsapp": phone,
                "origen": "whatsapp_escalado",
                "estado": "nuevo",
                "notas": f"Bot no pudo responder. Historial: {' | '.join(historial)}",
                "prioridad": "alta",
                "etapa": "captacion"
            }, timeout=5)
        print(f"📢 Asesor notificado: {phone}")
    except Exception as e:
        print(f"Error notificando: {e}")

    # DEFAULT
    return f"""🤖 Hola, soy el asistente de *TengoVisa RD* 🇩🇴

Escribe una de estas palabras:
- *hola* — Inicio
- *visa* — Información de visas
- *cita* — Gestión de citas
- *precio* — Ver tarifas
- *evaluacion* — Evalúa tu perfil GRATIS
- *agendar* — Cita con asesor
- *estado* — Estado de tu caso

📞 Asesor directo: {tel}"""


def enviar_twilio(to_number, mensaje):
    """Envía mensaje WhatsApp via Twilio"""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body=mensaje,
            from_=f'whatsapp:{TWILIO_NUM}',
            to=f'whatsapp:{to_number}'
        )
        print(f"📤 Twilio OK: {msg.sid}")
        return True
    except Exception as e:
        print(f"❌ Twilio error: {e}")
        return False

# ── WEBHOOK TWILIO ──
@app.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    phone = request.form.get('From', '').replace('whatsapp:', '').strip()
    text = request.form.get('Body', '').strip()
    nombre = request.form.get('ProfileName', '') or 'Lead WA'

    print(f"📱 [{datetime.now().strftime('%H:%M')}] {phone} ({nombre}): {text[:80]}")

    if text and phone:
        # Crear lead en CRM (siempre, independiente del horario)
        crear_lead_crm(nombre, phone, text, 'whatsapp_twilio')

        # Responder según horario
        if esta_en_horario_bot():
            respuesta = get_respuesta_con_memoria(text, phone)
        else:
            cfg = get_config()
            tel = cfg.get('tel_asesor', '+18499189998')
            respuesta = f"👋 Hola {nombre}! Tu mensaje fue recibido.\n\n⏰ Nuestro equipo está disponible de 8am a 10pm.\n\nTe responderemos pronto. También puedes escribirnos a:\n📞 {tel}\n\n_TengoVisa RD_ 🇩🇴"

        from twilio.twiml.messaging_response import MessagingResponse
        resp = MessagingResponse()
        resp.message(respuesta)
        return str(resp), 200, {'Content-Type': 'text/xml'}

    return '', 200

# ── WEBHOOK META WhatsApp Business API ──
@app.route('/webhook/whatsapp', methods=['GET'])
def verify_meta():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == 'TengoVisaBot2026':
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook/whatsapp', methods=['POST'])
def meta_webhook():
    data = request.get_json()
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        for msg in messages:
            phone = msg.get('from', '')
            text = msg.get('text', {}).get('body', '')
            nombre = value.get('contacts', [{}])[0].get('profile', {}).get('name', '')
            if text and phone:
                crear_lead_crm(nombre, phone, text, 'whatsapp_meta')
                if esta_en_horario_bot():
                    respuesta = get_respuesta(text)
                    # Aquí iría envío via Meta API
    except Exception as e:
        print(f"Meta webhook error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/health')
def health():
    cfg = get_config()
    en_horario = esta_en_horario_bot()
    return jsonify({
        "status": "ok",
        "bot": "TengoVisa WhatsApp",
        "en_horario": en_horario,
        "config": cfg
    })

@app.route('/test-respuesta')
def test_respuesta():
    msg = request.args.get('msg', 'hola')
    return jsonify({"respuesta": get_respuesta(msg)})

if __name__ == '__main__':
    print("🤖 TengoVisa WhatsApp Bot iniciando...")
    print(f"📱 Twilio: {TWILIO_NUM}")
    print(f"🔗 Webhook: https://crm.tengovisard.com/webhook/twilio")
    app.run(host='127.0.0.1', port=8002, debug=False)
