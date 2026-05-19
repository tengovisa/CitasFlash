from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv
import os, random, urllib.request, json as j
from datetime import datetime, timedelta

load_dotenv('/root/.env.tengovisa')

app = FastAPI(title="Tengo Visa CRM API", version="1.0")

# ── AUTH ADMIN ─────────────────────────────────────────────
import secrets as _sec
import time as _tm
import asyncio as _asio

ADMIN_USER = "tengovisa"
ADMIN_PASS = "TvRD2026#Rafa"
_sess = {}

def _mk_tok():
    t = _sec.token_urlsafe(32)
    _sess[t] = _tm.time() + 43200
    [_sess.pop(k) for k,v in list(_sess.items()) if _tm.time() > v]
    return t

def _ok_tok(t):
    if t in _sess and _tm.time() < _sess[t]:
        return True
    _sess.pop(t, None)
    return False

@app.post("/auth/login")
async def auth_login(request: Request):
    try:
        b = await request.json()
        if b.get("user","") == ADMIN_USER and b.get("pass","") == ADMIN_PASS:
            return {"ok": True, "token": _mk_tok(), "expires_h": 12}
        await _asio.sleep(1)
        return JSONResponse({"ok": False, "error": "Credenciales incorrectas"}, status_code=401)
    except Exception as ex:
        return JSONResponse({"ok": False, "error": str(ex)}, status_code=400)

@app.get("/auth/verify")
async def auth_verify(request: Request):
    if _ok_tok(request.headers.get("x-session-token", "")):
        return {"ok": True, "valid": True}
    return JSONResponse({"ok": False, "valid": False}, status_code=401)

@app.post("/auth/logout")
async def auth_logout(request: Request):
    _sess.pop(request.headers.get("x-session-token", ""), None)
    return {"ok": True}


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
def sb(): return _sb.schema('crm')

import urllib.request

def send_push(title: str, message: str):
    """Notificación push al celular del asesor"""
    try:
        url = f"https://tengovisard.com/push/api.php?token=tgvsa&user_id=tengovisa%40gmail.com&title={urllib.parse.quote(title)}&message={urllib.parse.quote(message)}"
        urllib.request.urlopen(url, timeout=3)
    except:
        pass

API_KEY = os.getenv('API_KEY')
otp_store = {}


# ── KEY PÚBLICA — solo para formularios cliente ──
PUBLIC_KEY = "TVPublic2026"
PUBLIC_ALLOWED = ["/ds160/save-full", "/evaluacion/save", "/globalentry/save",
                  "/otp/", "/evaluacion/send-otp", "/evaluacion/verify-otp",
                  "/ds160/token/"]

def chk_public(x_api_key: str = Header(None)):
    if x_api_key == API_KEY:
        return True
    if x_api_key == PUBLIC_KEY:
        return True
    raise HTTPException(status_code=403, detail="Forbidden")

def chk(x_api_key: str = Header(...)):
    if x_api_key not in [API_KEY, PUBLIC_KEY]: raise HTTPException(401, "No autorizado")

class LeadIn(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    origen: Optional[str] = "web"

class OTPReq(BaseModel):
    nombre: str
    apellido: str
    email: str
    whatsapp: str
    edad: int = 0
    ciudad: str = ""
    ocupacion: str = ""

class OTPVer(BaseModel):
    email: str
    otp: str

class EvalIn(BaseModel):
    lead_id: str
    nombre: str
    apellido: str
    email: str
    whatsapp: str
    edad: int
    nacionalidad: str
    ciudad: str
    # DATOS PERSONALES
    edad: int = 0
    ciudad: str = ""
    nacionalidad: str = ""
    # FAMILIA
    estado_civil: str = ""
    hijos: int = 0
    dependientes: int = 0
    familia_rd: str = ""
    familia_eeuu: str = ""
    familia_eeuu_estatus: str = ""
    comunidad: str = ""
    # LABORAL
    nivel_academico: str = ""
    empleo_tipo: str = ""
    tipo_empleo: str = ""
    antiguedad: str = ""
    salario_mensual: float = 0
    funciones: str = ""
    ingresos_adicionales: bool = False
    paga_impuestos: str = ""
    # ECONOMICO
    negocio_propio: bool = False
    empresa_propia: bool = False
    propiedades: str = ""
    vehiculo: bool = False
    cuenta_bancaria: str = ""
    historial_credito: str = ""
    inversiones: bool = False
    ahorros: str = ""
    # MIGRATORIO
    visa_previa: str = ""
    negaciones_previas: int = 0
    viajes_previos: int = 0
    viajes_eeuu: str = ""
    viajes_otros: str = ""
    visa_otros_paises: str = ""
    # VIAJE
    motivo_viaje: str = ""
    duracion_viaje: str = ""
    financiamiento: str = ""
    plan_viaje: str = ""
    usa_prestamo: str = ""
    visita_familiar: str = ""
    planea_regresar: str = ""
    # SEGURIDAD
    antecedentes: bool = False
    observaciones: str = ""


@app.post("/auth/login")
async def route_auth_login(request: Request):
    try:
        body = await request.json()
        u = body.get("user", "").strip()
        p = body.get("pass", "").strip()
        if u == ADMIN_USER and p == ADMIN_PASS:
            tok = _new_session()
            return {"ok": True, "token": tok, "expires_h": 12}
        import asyncio
        await asyncio.sleep(1)
        return JSONResponse({"ok": False, "error": "Credenciales incorrectas"}, status_code=401)
    except Exception as ex:
        return JSONResponse({"ok": False, "error": str(ex)}, status_code=400)


@app.get("/auth/verify")
async def route_auth_verify(request: Request):
    tok = request.headers.get("x-session-token", "")
    if _check_session(tok):
        return {"ok": True, "valid": True}
    return JSONResponse({"ok": False, "valid": False}, status_code=401)


@app.post("/auth/logout")
async def route_auth_logout(request: Request):
    tok = request.headers.get("x-session-token", "")
    _active_sessions.pop(tok, None)
    return {"ok": True}


@app.post("/auth/login")
async def route_auth_login(request: Request):
    try:
        body = await request.json()
        u = body.get("user", "").strip()
        p = body.get("pass", "").strip()
        if u == ADMIN_USER and p == ADMIN_PASS:
            tok = _new_session()
            return {"ok": True, "token": tok, "expires_h": 12}
        import asyncio
        await asyncio.sleep(1)
        return JSONResponse({"ok": False, "error": "Credenciales incorrectas"}, status_code=401)
    except Exception as ex:
        return JSONResponse({"ok": False, "error": str(ex)}, status_code=400)


@app.get("/auth/verify")
async def route_auth_verify(request: Request):
    tok = request.headers.get("x-session-token", "")
    if _check_session(tok):
        return {"ok": True, "valid": True}
    return JSONResponse({"ok": False, "valid": False}, status_code=401)


@app.post("/auth/logout")
async def route_auth_logout(request: Request):
    tok = request.headers.get("x-session-token", "")
    _active_sessions.pop(tok, None)
    return {"ok": True}


@app.get("/")
def root(): return {"status":"ok","sistema":"Tengo Visa CRM API","version":"1.0"}

@app.get("/health")
def health():
    try: sb().table("tenants").select("id").limit(1).execute(); return {"status":"ok","db":"conectado"}
    except Exception as e: return {"status":"ok","db":"pendiente","err":str(e)[:50]}

@app.get("/leads", dependencies=[Depends(chk)])
def get_leads(estado: Optional[str]=None, limit: int=50):
    q = sb().schema("crm").table("leads").select("*").order("created_at",desc=True).limit(limit)
    if estado: q = q.eq("estado",estado)
    return q.execute().data

@app.post("/leads", dependencies=[Depends(chk)])
def create_lead(lead: LeadIn):
    data = lead.dict()
    data["created_at"] = datetime.now().isoformat()
    r = sb().table("leads").insert(data).execute()
    return r.data[0] if r.data else {"error":"no se pudo crear"}

@app.get("/clientes", dependencies=[Depends(chk)])
def get_clientes(limit: int=50):
    return sb().table("clientes").select("*").order("created_at",desc=True).limit(limit).execute().data

@app.get("/expedientes", dependencies=[Depends(chk)])
def get_expedientes(etapa: Optional[str]=None):
    q = sb().table("expedientes").select("*").order("created_at",desc=True)
    if etapa: q = q.eq("etapa",etapa)
    return q.execute().data

@app.get("/dashboard/stats", dependencies=[Depends(chk)])
def stats():
    try:
        leads = sb().schema("crm").table("leads").select("id",count="exact").execute()
        clientes = sb().table("clientes").select("id",count="exact").execute()
        expedientes = sb().table("expedientes").select("id",count="exact").execute()
        pagos = sb().schema("crm").table("pagos").select("monto").eq("estado","completado").execute()
        cobrado = sum(p.get("monto",0) or 0 for p in pagos.data)
        return {"leads":leads.count or 0,"clientes":clientes.count or 0,"expedientes":expedientes.count or 0,"cobrado_mes":cobrado}
    except: return {"leads":0,"clientes":0,"expedientes":0,"cobrado_mes":0}

@app.post("/evaluacion/send-otp")
async def send_otp(req: OTPReq):
    import subprocess, json as jj, sys
    otp = str(random.randint(100000,999999))
    otp_store[req.email] = {
        "otp": otp,
        "nombre": req.nombre,
        "apellido": req.apellido,
        "whatsapp": req.whatsapp,
        "edad": getattr(req, "edad", None),
        "ciudad": getattr(req, "ciudad", ""),
        "ocupacion": getattr(req, "ocupacion", ""),
        "expires": (datetime.now()+timedelta(minutes=10)).isoformat()
    }
    html_body = f"<h2>Hola {req.nombre}</h2><p>Tu codigo: <strong style=color:red;font-size:32px>{otp}</strong></p><p>Expira en 10 minutos.</p>"
    payload = jj.dumps({"from":"noreply@tengovisard.com","to":[req.email],"subject":"Tu codigo Tengo Visa","html":html_body})
    cmd = ["curl","-s","-X","POST","https://api.resend.com/emails","-H",f"Authorization: Bearer {os.getenv('RESEND_API_KEY','re_3t41id3F_LoM2iy8EFNG76HnXTYxLRbu5')}","-H","Content-Type: application/json","-d",payload]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    print(f"RESEND_RESPONSE: {result.stdout}", flush=True)
    print(f"RESEND_ERROR: {result.stderr}", flush=True)
    return {"ok":True,"debug":result.stdout[:100]}

@app.post("/evaluacion/verify-otp")
def verify_otp(req: OTPVer):
    s = otp_store.get(req.email)
    if not s: raise HTTPException(400,"OTP no encontrado o expirado")
    if datetime.now() > datetime.fromisoformat(s["expires"]):
        del otp_store[req.email]; raise HTTPException(400,"OTP expirado")
    if s["otp"] != req.otp: raise HTTPException(400,"OTP incorrecto")
    try:
        insert_data = {
            "nombre": s.get("nombre",""),
            "apellido": s.get("apellido",""),
            "email": req.email,
            "whatsapp": s.get("whatsapp",""),
            "telefono": s.get("whatsapp",""),
            "origen": "evaluacion_web",
            "estado": "nuevo",
            "edad": s.get("edad"),
            "ciudad": s.get("ciudad",""),
            "ocupacion": s.get("ocupacion",""),
            "etapa": "captacion",
            "prioridad": "normal",
            "created_at": datetime.now().isoformat()
        }
        lead = sb().schema("crm").table("leads").insert(insert_data).execute()
        lid = lead.data[0]["id"] if lead.data else "dev"
        # Generar codigo_cliente
        if lid and lid != "dev":
            codigo = "TV-" + lid[:6].upper()
            sb().schema("crm").table("leads").update({"codigo_cliente": codigo}).eq("id", lid).execute()
    except Exception as e:
        lid = "dev"
    del otp_store[req.email]
    return {"ok": True, "lead_id": lid, "nombre": s.get("nombre","")}

@app.post("/evaluacion/submit", dependencies=[Depends(chk)])
def submit_eval(ev: EvalIn):
    score=0; al=[]; ft=[]; db=[]
    civil={"soltero":1,"union_libre":2,"casado":3,"divorciado":1,"viudo":1}
    cv=civil.get(ev.estado_civil,1); score+=cv
    if cv>=3: ft.append("Estado civil estable")
    else: db.append("Estado civil sin vínculos formales")
    score+=3 if ev.hijos>=3 else 2 if ev.hijos>0 else 1
    if ev.hijos>0: ft.append("Arraigo familiar (hijos)")
    else: db.append("Sin hijos — menos arraigo")
    if ev.antecedentes: al.append({"nombre":"ANTECEDENTES_PENALES","gravedad":"CRITICA","bloquea":True})
    else: score+=3; ft.append("Sin antecedentes penales")
    fam={"ninguna":3,"lejana":2,"hermano":1,"padre_madre":0,"esposo_hijos":0}
    fv=fam.get(ev.familia_eeuu,2); score+=fv
    if fv<=1: al.append({"nombre":"FAMILIA_DIRECTA_EEUU","gravedad":"ALTA","bloquea":False})
    elif fv==3: ft.append("Sin familia directa en EEUU")
    edu={"primaria":1,"secundaria":2,"tecnico":2,"universitaria":3,"postgrado":3}
    score+=edu.get(ev.nivel_academico,1)
    if edu.get(ev.nivel_academico,1)>=3: ft.append("Nivel educativo universitario")
    emp={"desempleado":0,"informal":1,"independiente":2,"formal":2,"empresario":3,"jubilado":2}
    ev2=emp.get(ev.empleo_tipo,0); score+=ev2
    if ev2==0: al.append({"nombre":"SIN_EMPLEO","gravedad":"ALTA","bloquea":False}); db.append("Sin empleo formal")
    elif ev2>=2: ft.append("Empleo estable")
    score+=3 if ev.negocio_propio else 1
    if ev.negocio_propio: ft.append("Tiene negocio propio")
    prop={"ninguna":0,"alquila":1,"propia":3,"multiples":3}
    pv=prop.get(ev.propiedades,0); score+=pv
    if pv==0: db.append("Sin propiedades")
    elif pv>=3: ft.append("Propiedades propias")
    score+=2 if ev.vehiculo else 0
    if ev.vehiculo: ft.append("Tiene vehículo propio")
    banco={"ninguna":0,"basica":1,"activa":2,"solida":3}
    bv=banco.get(ev.cuenta_bancaria,0); score+=bv
    if bv==0: al.append({"nombre":"SIN_CUENTA_BANCARIA","gravedad":"ALTA","bloquea":False}); db.append("Sin cuenta bancaria")
    elif bv>=2: ft.append("Cuenta bancaria activa")
    score+=3 if ev.salario_mensual>80000 else 2 if ev.salario_mensual>30000 else 1
    if ev.salario_mensual>40000: ft.append("Ingresos sólidos")
    elif ev.salario_mensual<15000: db.append("Ingresos bajos")
    score+=3 if ev.viajes_previos>5 else 2 if ev.viajes_previos>2 else 1 if ev.viajes_previos>0 else 0
    if ev.viajes_previos>2: ft.append("Historial de viajes internacional")
    visa={"ninguna":1,"negada_reciente":0,"negada_antigua":1,"vigente":3,"expirada":2}
    score+=visa.get(ev.visa_previa,1)
    score-=ev.negaciones_previas
    if ev.negaciones_previas>0: al.append({"nombre":"NEGACION_PREVIA","gravedad":"ALTA","bloquea":False})
    fin={"tercero_sin_relacion":0,"familiar_eeuu":0,"familiar_rd":2,"propio":3,"empresa":3}
    fiv=fin.get(ev.financiamiento,1); score+=fiv
    if fiv==0: al.append({"nombre":"FINANCIAMIENTO_DUDOSO","gravedad":"ALTA","bloquea":False})
    elif fiv>=3: ft.append("Financiamiento propio")
    score=max(0,score); pct=round(score/42*100)
    hasCrit=any(a["bloquea"] for a in al)
    if hasCrit or score<18: cl="ALTO_RIESGO";rec="no_avanzar";col="#DC2626";em="🔴";mc="Identificamos áreas críticas que requieren atención. Te recomendamos una consulta personalizada para diseñar un plan de acción."
    elif score<28: cl="POTENCIAL_MEDIO";rec="fortalecer";col="#F59E0B";em="🟡";mc="Tu perfil tiene elementos positivos con áreas de mejora. Con la estrategia correcta puede fortalecerse significativamente."
    elif score<35: cl="POTENCIAL_ALTO";rec="avanzar";col="#16A34A";em="🟢";mc="Tu perfil muestra características positivas. Nuestro equipo puede orientarte para presentar tu caso de la manera más sólida."
    else: cl="PERFIL_SOLIDO";rec="avanzar_ds160";col="#2563EB";em="🔵";mc="Tu perfil presenta características muy sólidas. Estás listo para avanzar al siguiente nivel del proceso."
    docs=["Pasaporte vigente","Foto reciente","Acta de nacimiento"]
    if ev.empleo_tipo=="formal": docs.append("Carta laboral reciente")
    if ev.negocio_propio: docs.extend(["Registro mercantil","Estados financieros"])
    if ev.propiedades in ["propia","multiples"]: docs.append("Título de propiedad")
    if ev.vehiculo: docs.append("Título del vehículo")
    if ev.cuenta_bancaria in ["activa","solida"]: docs.append("Estados de cuenta 3 meses")
    if ev.estado_civil=="casado": docs.append("Acta de matrimonio")
    if ev.hijos>0: docs.append("Actas de nacimiento de hijos")
    result={"score":score,"score_max":42,"porcentaje":pct,"clasificacion":cl,"recomendacion":rec,"color":col,"emoji":em,"alertas":al,"fortalezas":ft,"debilidades":db,"documentos_sugeridos":docs,"mensaje_cliente":mc}
    # Guardar TODOS los datos del formulario
    datos_completos = {
        "datos_personales": {
            "nombre": ev.nombre, "apellido": ev.apellido,
            "email": ev.email, "whatsapp": ev.whatsapp,
            "edad": ev.edad, "nacionalidad": ev.nacionalidad, "ciudad": ev.ciudad
        },
        "perfil_familiar": {
            "estado_civil": ev.estado_civil, "hijos": ev.hijos,
            "dependientes": ev.dependientes, "familia_rd": getattr(ev,"familia_rd",""),
            "familia_eeuu": ev.familia_eeuu, "familia_eeuu_estatus": getattr(ev,"familia_eeuu_estatus",""),
            "comunidad": getattr(ev,"comunidad","")
        },
        "perfil_laboral": {
            "empleo_tipo": ev.empleo_tipo, "tipo_empleo": getattr(ev,"tipo_empleo",""),
            "antiguedad": ev.antiguedad, "salario_mensual": ev.salario_mensual,
            "funciones": getattr(ev,"funciones",""), "ingresos_adicionales": getattr(ev,"ingresos_adicionales",""),
            "paga_impuestos": getattr(ev,"paga_impuestos","")
        },
        "perfil_economico": {
            "negocio_propio": ev.negocio_propio, "propiedades": ev.propiedades,
            "vehiculo": ev.vehiculo, "cuenta_bancaria": ev.cuenta_bancaria,
            "empresa_propia": getattr(ev,"empresa_propia",""), "historial_credito": getattr(ev,"historial_credito",""),
            "inversiones": getattr(ev,"inversiones","")
        },
        "perfil_migratorio": {
            "visa_previa": ev.visa_previa, "negaciones_previas": ev.negaciones_previas,
            "viajes_previos": ev.viajes_previos, "viajes_eeuu": getattr(ev,"viajes_eeuu",""),
            "viajes_otros": getattr(ev,"viajes_otros",""), "visa_otros_paises": getattr(ev,"visa_otros_paises","")
        },
        "proposito_viaje": {
            "motivo_viaje": ev.motivo_viaje, "duracion_viaje": ev.duracion_viaje,
            "financiamiento": ev.financiamiento, "plan_viaje": getattr(ev,"plan_viaje",""),
            "usa_prestamo": getattr(ev,"usa_prestamo",""), "visita_familiar": getattr(ev,"visita_familiar",""),
            "planea_regresar": getattr(ev,"planea_regresar",""),
            "observaciones": ev.observaciones
        },
        "seguridad": {
            "antecedentes": ev.antecedentes
        }
    }
    result["datos_completos"] = datos_completos
    # Score comercial
    score_comercial = 0
    if ev.salario_mensual >= 60000: score_comercial += 3
    elif ev.salario_mensual >= 30000: score_comercial += 2
    else: score_comercial += 1
    if ev.negocio_propio: score_comercial += 2
    if len(ev.observaciones or '') > 80: score_comercial += 2
    if ev.whatsapp: score_comercial += 1
    if ev.viajes_previos > 0: score_comercial += 1
    lead_temp = "CALIENTE" if score_comercial >= 7 else "TIBIO" if score_comercial >= 4 else "FRIO"
    accion = "WhatsApp inmediato" if lead_temp=="CALIENTE" else "Llamada 24h" if lead_temp=="TIBIO" else "Email + nutricion"
    result["score_comercial"] = score_comercial
    result["lead_temperatura"] = lead_temp
    result["accion_recomendada"] = accion
    result["datos_completos"] = datos_completos

    # Mensaje WhatsApp por clasificacion
    msgs = {
        "PERFIL_SOLIDO": "✅ Excelente noticia, {n}! Tu perfil fue evaluado y presenta características muy sólidas. Te recomendamos iniciar el proceso lo antes posible. ¿Cuándo podemos hablar? 👉 wa.me/18499189998",
        "POTENCIAL_ALTO": "🟢 Hola {n}, evaluamos tu perfil y tiene muy buenas bases. Con la preparación correcta puedes tener un caso muy sólido. Te contactaremos para explicarte los próximos pasos.",
        "POTENCIAL_MEDIO": "🟡 Hola {n}, recibimos tu evaluación. Tu perfil tiene elementos positivos y áreas que podemos fortalecer juntos. ¿Tienes 5 minutos para una llamada esta semana?",
        "ALTO_RIESGO": "📋 Hola {n}, gracias por confiar en nosotros. Evaluamos tu perfil y hay aspectos importantes que debemos revisar juntos antes de avanzar. Te contactaremos pronto."
    }
    msg_wa = msgs.get(cl, msgs["POTENCIAL_MEDIO"]).replace("{n}", ev.nombre)
    result["mensaje_whatsapp"] = msg_wa

    try:
        # Guardar score en leads
        lead_id_real = ev.lead_id if ev.lead_id and ev.lead_id != "dev" else None
        if lead_id_real:
            sb().schema("crm").table("leads").update({
                "score": score, "estado": "calificado",
                "updated_at": datetime.now().isoformat()
            }).eq("id", lead_id_real).execute()
        sb().schema("crm").table("evaluaciones").insert({
            "expediente_id": lead_id_real,
            "score": score,
            "resultado": cl.lower(),
            "observaciones": ev.observaciones,
            "ia_analisis": result,
            "created_at": datetime.now().isoformat()
        }).execute()
        try:
            send_notification_email("evaluacion_rrss" if datos.get("fuente")=="rrss" else "evaluacion", {
                "🔴 LEAD TEMPERATURA": lead_temp,
                "⚡ ACCIÓN": accion,
                "📊 Score Migratorio": f"{score}/42 ({round(score/42*100)}%)",
                "🎯 Clasificación": cl,
                "👤 Nombre": f"{ev.nombre} {ev.apellido}",
                "📧 Email": ev.email,
                "📱 WhatsApp": ev.whatsapp,
                "📅 Fecha Nacimiento": str(ev.edad) + " años",
                "🏙️ Ciudad": ev.ciudad,
                "💍 Estado Civil": ev.estado_civil,
                "👶 Hijos": ev.hijos,
                "👨‍👩‍👧 Familia EEUU": ev.familia_eeuu,
                "🎓 Educación": ev.nivel_academico,
                "💼 Empleo": ev.empleo_tipo,
                "💰 Salario": f"RD$ {ev.salario_mensual:,.0f}",
                "🏢 Negocio propio": "Sí" if ev.negocio_propio else "No",
                "🏠 Propiedades": ev.propiedades,
                "🚗 Vehículo": "Sí" if ev.vehiculo else "No",
                "🏦 Banco": ev.cuenta_bancaria,
                "✈️ Visa previa": ev.visa_previa,
                "❌ Negaciones": ev.negaciones_previas,
                "🌍 Viajes previos": ev.viajes_previos,
                "✈️ Motivo viaje": ev.motivo_viaje,
                "⏱️ Duración": ev.duracion_viaje,
                "💳 Financiamiento": ev.financiamiento,
                "📝 Descripción cliente": ev.observaciones or "—",
                "💬 Mensaje WA sugerido": msg_wa
            })
        except: pass
    except Exception as e: print(f"DB err: {e}")
    return result

# ── DS-160 MODELS ──
class DS160Submit(BaseModel):
    lead_id: str
    email: str
    # Personal
    apellido_primario: str
    apellido_nativo: str = ""
    nombre: str
    otros_nombres: str = ""
    sexo: str
    estado_civil: str
    fecha_nacimiento: str
    ciudad_nacimiento: str
    pais_nacimiento: str
    pais_nacionalidad: str
    otra_nacionalidad: str = ""
    tiene_doble_nac: bool = False
    numero_seguro_social: str = ""
    numero_id_tributario: str = ""
    # Pasaporte
    tipo_pasaporte: str
    numero_pasaporte: str
    pais_emisor_pasaporte: str
    fecha_emision_pasaporte: str
    fecha_vencimiento_pasaporte: str
    perdio_pasaporte: bool = False
    # Contacto
    direccion_rd: str
    ciudad_rd: str
    provincia_rd: str
    telefono_principal: str
    telefono_adicional: str = ""
    email_contacto: str
    redes_sociales: str = ""
    # Viaje
    proposito_viaje: str
    fecha_llegada_prevista: str
    duracion_estancia: str
    tiene_itinerario: bool = False
    itinerario: str = ""
    paga_viaje: str
    nombre_contacto_eeuu: str = ""
    relacion_contacto_eeuu: str = ""
    direccion_eeuu: str = ""
    ciudad_eeuu: str = ""
    estado_eeuu: str = ""
    zip_eeuu: str = ""
    telefono_contacto_eeuu: str = ""
    # Viajes previos
    viajo_antes_eeuu: bool = False
    viajes_previos_eeuu: str = ""
    deportado_alguna_vez: bool = False
    # Familia
    nombre_padre: str = ""
    fecha_nac_padre: str = ""
    padre_en_eeuu: bool = False
    nombre_madre: str = ""
    fecha_nac_madre: str = ""
    madre_en_eeuu: bool = False
    nombre_conyuge: str = ""
    fecha_nac_conyuge: str = ""
    pais_nac_conyuge: str = ""
    familiares_eeuu: str = ""
    # Trabajo actual
    ocupacion_actual: str
    empleador_actual: str = ""
    direccion_empleador: str = ""
    telefono_empleador: str = ""
    fecha_inicio_trabajo: str = ""
    descripcion_trabajo: str = ""
    # Educacion
    nivel_educacion: str
    nombre_institucion: str = ""
    ciudad_institucion: str = ""
    fecha_inicio_edu: str = ""
    fecha_fin_edu: str = ""
    # Seguridad
    enfermedad_comunicable: bool = False
    trastorno_mental: bool = False
    adiccion_drogas: bool = False
    arrestado: bool = False
    delitos: str = ""
    trafico_drogas: bool = False
    prostitucion: bool = False
    lavado_dinero: bool = False
    trafico_personas: bool = False
    actividad_terrorista: bool = False
    espionaje: bool = False
    genocidio: bool = False
    visa_negada_antes: bool = False
    detalle_visa_negada: str = ""
    presente_eeuu_sin_permiso: bool = False
    # DIRECCIÓN COMPLETA
    direccion_linea2: str = ""
    codigo_postal_rd: str = ""
    telefono_trabajo: str = ""
    # REDES SOCIALES
    red_social_1: str = ""
    usuario_red_1: str = ""
    red_social_2: str = ""
    usuario_red_2: str = ""
    # VIAJE DETALLADO
    ciudad_llegada: str = ""
    fecha_salida: str = ""
    ciudad_salida: str = ""
    vuelo_llegada: str = ""
    vuelo_salida: str = ""
    viaja_acompañado: bool = False
    nombre_acompañante: str = ""
    relacion_acompañante: str = ""
    patrocinador_nombre: str = ""
    patrocinador_tel: str = ""
    patrocinador_email: str = ""
    patrocinador_relacion: str = ""
    patrocinador_empresa: str = ""
    # VIAJES PREVIOS DETALLE
    fecha_visita1_eeuu: str = ""
    duracion_visita1: str = ""
    fecha_visita2_eeuu: str = ""
    duracion_visita2: str = ""
    visa_anterior_numero: str = ""
    visa_anterior_fecha: str = ""
    visa_mismo_tipo: bool = False
    visa_mismo_pais: bool = False
    visa_10_años: bool = False
    razon_negacion_visa: str = ""
    peticion_inmigracion: bool = False
    detalle_peticion: str = ""
    # FAMILIA DETALLADA
    padre_estatus_eeuu: str = ""
    madre_estatus_eeuu: str = ""
    tiene_familiares_eeuu: bool = False
    familiar1_nombre: str = ""
    familiar1_parentesco: str = ""
    familiar1_estatus: str = ""
    otros_familiares_eeuu: str = ""
    conyuge_pais_ciudadania: str = ""
    conyuge_direccion: str = ""
    # TRABAJO ANTERIOR
    tuvo_empleo_anterior: bool = False
    empleador_anterior: str = ""
    direccion_emp_anterior: str = ""
    tel_emp_anterior: str = ""
    cargo_anterior: str = ""
    fecha_inicio_anterior: str = ""
    fecha_fin_anterior: str = ""
    funciones_anterior: str = ""
    # EDUCACION DETALLADA
    carrera: str = ""
    fecha_graduacion: str = ""
    # INFORMACION ADICIONAL
    idiomas: str = ""
    paises_visitados_5años: str = ""
    pertenece_organizacion: bool = False
    nombre_organizacion: str = ""
    tiene_habilidades_especiales: bool = False
    habilidades_especiales: str = ""
    sirvio_militar: bool = False
    pais_militar: str = ""
    rama_militar: str = ""
    rango_militar: str = ""
    especialidad_militar: str = ""
    fecha_inicio_militar: str = ""
    fecha_fin_militar: str = ""
    grupo_paramilitar: bool = False
    # SEGURIDAD DETALLADA
    detalle_arresto: str = ""
    trafico_drogas_detalle: str = ""
    prostitucion_detalle: str = ""
    turpitud_moral: bool = False
    detalle_turpitud: str = ""
    excluido_deportado: bool = False
    detalle_deportacion: str = ""
    terrorismo_detalle: str = ""
    apoyo_terrorismo: bool = False
    partido_comunista: bool = False
    genocidio_detalle: str = ""
    tortura: bool = False
    recluto_menores: bool = False
    overstay_eeuu: bool = False
    detalle_overstay: str = ""
    fraude_visa: bool = False
    detalle_fraude: str = ""
    renuncio_ciudadania: bool = False
    custodia_menor: bool = False
    voto_ilegal: bool = False
    # CONTACTOS ADICIONALES
    contacto2_apellido: str = ""
    contacto2_nombre: str = ""
    contacto2_tel: str = ""
    contacto2_email: str = ""
    contacto3_apellido: str = ""
    contacto3_nombre: str = ""
    contacto3_tel: str = ""
    contacto3_email: str = ""
    # ASISTENTE
    fue_asistido: bool = False
    asistente_nombre: str = ""
    asistente_org: str = ""
    asistente_tel: str = ""
    # ESTRATEGIA INTERNA ASESOR
    funciones_trabajo_1: str = ""
    funciones_trabajo_2: str = ""
    funciones_trabajo_3: str = ""
    info_adicional_libre: str = ""
    notas_asesor: str = ""

@app.post("/ds160/submit", dependencies=[Depends(chk)])
def submit_ds160(data: DS160Submit):
    try:
        lid = data.lead_id if data.lead_id and data.lead_id != "dev" else None
        todos_datos = data.dict()
        r = sb().schema("crm").table("ds160_casos").insert({
            "lead_id": lid,
            "datos": todos_datos,
            "estado": "revision",
            "revision_notas": data.notas_asesor,
            "created_at": datetime.now().isoformat()
        }).execute()
        caso_id = r.data[0]["id"] if r.data else "dev"
        if lid:
            try:
                sb().schema("crm").table("leads").update({"estado":"en_proceso","updated_at":datetime.now().isoformat()}).eq("id",lid).execute()
                sb().table("timeline").insert({"lead_id":lid,"evento":"DS-160 completado","descripcion":f"Formulario DS-160 enviado por {data.nombre} {data.apellido_primario}","icono":"🛂","created_at":datetime.now().isoformat()}).execute()
            except: pass
        try:
            send_notification_email("ds160",{
                "Nombre": f"{nombre} {apellido}",
                "Email": email,
                "Pasaporte": pas,
                "Propósito": str(body.get("q55_proposito") or body.get("proposito_viaje","B1/B2")),
                "Ocupación": str(body.get("q131_ocupacion") or body.get("ocupacion_actual","")),
                "Empleador": str(body.get("q132_empleador") or body.get("empleador_actual","")),
                "Ciudad EEUU": str(body.get("q66_ciudad_hosp") or body.get("ciudad_eeuu","")),
                "Duración": str(body.get("q64_duracion") or body.get("duracion_estancia",""))
            })
        except: pass
        try:
            notify_ds160(
                nombre=nombre,
                apellido=apellido,
                email=email,
                pasaporte=pas,
                caso_id=str(caso_id),
                whatsapp=whatsapp
            )
        except: pass
        return {"ok": True, "caso_id": caso_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/ds160/{caso_id}", dependencies=[Depends(chk)])
def get_ds160(caso_id: str):
    r = sb().schema("crm").table("ds160_casos").select("*").eq("id", caso_id).execute()
    if not r.data:
        r = sb().table("ds160_casos").select("*").eq("id", caso_id).execute()
    if not r.data: raise HTTPException(404, "Caso no encontrado")
    return r.data[0]

@app.get("/ds160", dependencies=[Depends(chk)])
def list_ds160():
    return sb().table("ds160_casos").select("*").order("created_at", desc=True).execute().data

@app.post("/ocr/pasaporte")
async def ocr_pasaporte(file: bytes = None):
    """OCR endpoint - procesa MRZ del pasaporte"""
    return {"ok": True, "msg": "OCR disponible via endpoint /ocr/pasaporte-upload"}


from fastapi import UploadFile, File
import subprocess, tempfile, os as _os

@app.post("/ocr/pasaporte-upload")
async def ocr_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        result = subprocess.run(
            ['python3','-c',f'''
import pytesseract
from PIL import Image
img = Image.open("{tmp_path}")
text = pytesseract.image_to_string(img)
lines = [l.strip() for l in text.split("\\n") if l.strip()]
mrz = [l for l in lines if len(l)>30 and all(c.isalnum() or c in "<" for c in l)]
print("MRZ_LINES:" + "|".join(mrz[:2]))
print("ALL_TEXT:" + " | ".join(lines[:15]))
'''],
            capture_output=True, text=True, timeout=30
        )
        _os.unlink(tmp_path)
        output = result.stdout
        mrz_data = {}
        if "MRZ_LINES:" in output:
            mrz_lines = output.split("MRZ_LINES:")[1].split("\n")[0].split("|")
            if len(mrz_lines) >= 2:
                l1, l2 = mrz_lines[0], mrz_lines[1]
                try:
                    # Parse MRZ line 2
                    mrz_data["numero_pasaporte"] = l2[0:9].replace("<","").strip()
                    mrz_data["pais_nacionalidad"] = l2[10:13].replace("<","").strip()
                    raw_dob = l2[13:19]
                    mrz_data["fecha_nacimiento"] = f"19{raw_dob[0:2]}-{raw_dob[2:4]}-{raw_dob[4:6]}" if int(raw_dob[0:2])>24 else f"20{raw_dob[0:2]}-{raw_dob[2:4]}-{raw_dob[4:6]}"
                    mrz_data["sexo"] = "M" if l2[20]=="M" else "F"
                    raw_exp = l2[21:27]
                    mrz_data["fecha_vencimiento_pasaporte"] = f"20{raw_exp[0:2]}-{raw_exp[2:4]}-{raw_exp[4:6]}"
                    # Parse MRZ line 1 for name
                    if "<<" in l1:
                        name_part = l1[5:] if len(l1)>5 else l1
                        parts = name_part.split("<<")
                        mrz_data["apellido_primario"] = parts[0].replace("<"," ").strip() if parts else ""
                        mrz_data["nombre"] = parts[1].replace("<"," ").strip() if len(parts)>1 else ""
                except Exception as pe:
                    mrz_data["parse_error"] = str(pe)
        return {"ok": True, "mrz": mrz_data, "raw": output[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/crm/evaluaciones", dependencies=[Depends(chk)])
def crm_evaluaciones(limit: int = 100):
    try:
        leads = sb().schema("crm").table("leads").select("*").order("created_at", desc=True).limit(limit).execute().data
        evals = sb().schema("crm").table("evaluaciones").select("*").order("created_at", desc=True).limit(limit).execute().data
        result = []
        for lead in leads:
            ev = next((e for e in evals if e.get("expediente_id") == lead.get("id")), {})
            ia = lead.get("ia_analisis") or ev.get("ia_analisis") or {}
            datos = ia.get("datos_completos") or {}
            result.append({
                "id": lead.get("id"),
                "lead_id": lead.get("id"),
                "nombre": lead.get("nombre",""),
                "apellido": lead.get("apellido",""),
                "email": lead.get("email",""),
                "whatsapp": lead.get("whatsapp",""),
                "edad": lead.get("edad") or datos.get("datos_personales",{}).get("edad",""),
                "ciudad": lead.get("ciudad") or datos.get("datos_personales",{}).get("ciudad",""),
                "ocupacion": lead.get("ocupacion") or datos.get("perfil_laboral",{}).get("ocupacion",""),
                "estado_civil": datos.get("datos_personales",{}).get("estado_civil",""),
                "hijos": datos.get("datos_personales",{}).get("hijos",0),
                "ingreso_mensual": datos.get("perfil_laboral",{}).get("ingreso_mensual",0),
                "empresa": datos.get("perfil_laboral",{}).get("empresa",""),
                "banco": datos.get("perfil_economico",{}).get("banco",""),
                "ahorros": datos.get("perfil_economico",{}).get("ahorros",0),
                "tiene_propiedad": datos.get("perfil_economico",{}).get("tiene_propiedad",False),
                "tiene_vehiculo": datos.get("perfil_economico",{}).get("tiene_vehiculo",False),
                "ha_viajado": datos.get("perfil_migratorio",{}).get("ha_viajado",False),
                "visas_anteriores": datos.get("perfil_migratorio",{}).get("visas_anteriores",""),
                "proposito_viaje": datos.get("proposito_viaje",{}).get("proposito",""),
                "familia_eeuu": datos.get("perfil_migratorio",{}).get("familia_eeuu",""),
                "score": lead.get("score",0),
                "score_comercial": lead.get("score_comercial",0),
                "clasificacion": lead.get("lead_temperatura",""),
                "estado": lead.get("estado","nuevo"),
                "etapa": lead.get("etapa",""),
                "prioridad": lead.get("prioridad","normal"),
                "codigo_cliente": lead.get("codigo_cliente",""),
                "asesor": lead.get("asesor",""),
                "ia_texto": ia.get("ia_texto",""),
                "ia_fortalezas": ia.get("fortalezas",[]),
                "ia_debilidades": ia.get("debilidades",[]),
                "ia_alertas": ia.get("alertas",[]),
                "ia_documentos": ia.get("documentos_sugeridos",[]),
                "created_at": lead.get("created_at",""),
                "eval_id": ev.get("id",""),
                "eval_resultado": ev.get("resultado",""),
            })
        return result
    except Exception as ex:
        return {"error": str(ex)}


@app.get("/crm/ds160", dependencies=[Depends(chk)])
def crm_ds160_list(limit: int = 100):
    try:
        casos = sb().schema("crm").table("ds160_casos").select("*").order("created_at", desc=True).limit(limit).execute().data
        return casos
    except Exception as ex:
        return {"error": str(ex)}

@app.put("/crm/evaluaciones/{lead_id}", dependencies=[Depends(chk)])
def update_eval_crm(lead_id: str, body: dict):
    try:
        if body.get("estado"):
            sb().schema("crm").table("leads").update({"estado": body.get("estado"), "updated_at": datetime.now().isoformat()}).eq("id", lead_id).execute()
        if body.get("notas_asesor"):
            pass
        sb().table("notas").insert({"contenido": body.get("notas_asesor"), "tipo": "estrategia_asesor", "created_at": datetime.now().isoformat()}).execute()
        return {"ok": True}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

@app.put("/crm/ds160/{caso_id}", dependencies=[Depends(chk)])
def update_ds160_crm(caso_id: str, body: dict):
    try:
        r = sb().table("ds160_casos").update({
            "datos": body.get("datos"),
            "revision_notas": body.get("notas_asesor"),
            "estado": body.get("estado", "revision"),
            "updated_at": datetime.now().isoformat()
        }).eq("id", caso_id).execute()
        return {"ok": True}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

import urllib.request as ur2
import json as j2

class IARequest(BaseModel):
    prompt: str
    tipo: str = "evaluacion"

@app.post("/ia/analizar", dependencies=[Depends(chk)])
def ia_analizar(req: IARequest):
    try:
        payload = j2.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": req.prompt}]
        }).encode()
        r = ur2.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        resp = ur2.urlopen(r, timeout=60)
        data = j2.loads(resp.read())
        text = data.get("content", [{}])[0].get("text", "Sin respuesta")
        return {"ok": True, "text": text}
    except ur2.HTTPError as e:
        err = e.read().decode()
        if "credit" in err or "balance" in err:
            return {"ok": False, "error": "sin_creditos", "msg": "Recarga créditos en console.anthropic.com"}
        return {"ok": False, "error": err[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class PasaporteSubmit(BaseModel):
    lead_id: str
    tipo_tramite: str
    tipo_cita: str
    nombre_completo: str
    cedula: str
    fecha_nacimiento: str
    telefono: str
    email: str
    oficina: str
    pasaporte_actual: str = ""
    pasaporte_vence: str = ""
    tuvo_pasaporte: str = ""
    motivo_nuevo: str = ""
    familiares: list = []
    observaciones: str = ""
    total_beneficiarios: int = 1

@app.post("/pasaporte/submit", dependencies=[Depends(chk)])
def pasaporte_submit(data: PasaporteSubmit):
    try:
        meta = {
            "tipo_tramite": data.tipo_tramite,
            "tipo_cita": data.tipo_cita,
            "cedula": data.cedula,
            "fecha_nacimiento": data.fecha_nacimiento,
            "oficina": data.oficina,
            "pasaporte_actual": data.pasaporte_actual,
            "pasaporte_vence": data.pasaporte_vence,
            "tuvo_pasaporte": data.tuvo_pasaporte,
            "familiares": data.familiares,
            "total_beneficiarios": data.total_beneficiarios,
            "observaciones": data.observaciones
        }
        r = sb().table("leads").insert({
            "nombre": data.nombre_completo.split()[0] if data.nombre_completo else "",
            "apellido": " ".join(data.nombre_completo.split()[1:]) if data.nombre_completo else "",
            "email": data.email,
            "whatsapp": data.telefono,
            "origen": f"pasaporte_{data.tipo_tramite}",
            "estado": "nuevo",
            "score": 0,
            "notas_internas": str(meta),
            "created_at": datetime.now().isoformat()
        }).execute()
        lid = r.data[0]["id"] if r.data else data.lead_id
        try:
            send_notification_email(f"pasaporte_{data.tipo_tramite}", {
                "nombre": data.nombre_completo.split()[0] if data.nombre_completo else "",
                "apellido": " ".join(data.nombre_completo.split()[1:]) if data.nombre_completo else "",
                "email": data.email,
                "whatsapp": data.telefono,
                "telefono": data.telefono,
                "caso_id": str(lid),
                "pasaporte_actual": data.pasaporte_actual,
                "tipo_tramite": data.tipo_tramite
            })
        except Exception as e:
            print(f"Pasaporte notify error: {e}")
        return {"ok": True, "lead_id": lid}
    except Exception as e:
        return {"ok": False, "error": str(e)}



@app.post("/api/pasaporte/save", dependencies=[Depends(chk)])
def pasaporte_save_alias(body: dict):
    try:
        data = PasaporteSubmit(**body)
        return pasaporte_submit(data)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/pasaporte", dependencies=[Depends(chk)])
def get_pasaportes(limit: int = 100):
    try:
        import ast
        rows = sb().schema("crm").table("leads").select("*").or_("origen.eq.pasaporte_renovacion,origen.eq.pasaporte_nuevo").order("created_at", desc=True).limit(limit).execute().data or []
        for row in rows:
            meta = {}
            raw = row.get("notas_internas") or ""
            try:
                if isinstance(raw, str) and raw.strip().startswith("{"):
                    meta = ast.literal_eval(raw)
            except Exception:
                meta = {}
            row["datos"] = meta if isinstance(meta, dict) else {}
            row["_nombre"] = row.get("nombre","")
            row["_apellido"] = row.get("apellido","")
            row["_email"] = row.get("email","")
            row["_whatsapp"] = row.get("whatsapp","")
            row["_tipo"] = row.get("origen","").replace("pasaporte_","")
        return {"ok": True, "total": len(rows), "casos": rows, "records": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "casos": [], "records": []}

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
from fastapi.responses import FileResponse

def send_notification_email(tipo: str, datos: dict, pdf_path: str = None):
    """Notificación email al asesor por cada servicio — template por tipo"""
    import subprocess, json as jj

    # Extraer campos comunes con fallback robusto
    nombre    = (datos.get('nombre') or datos.get('q2_nombre') or datos.get('f_nombre') or '').strip().title()
    apellido  = (datos.get('apellido') or datos.get('apellido_primario') or datos.get('q1_apellido') or datos.get('f_apellido1') or '').strip().title()
    email_c   = datos.get('email') or datos.get('q36_email') or ''
    telefono  = datos.get('whatsapp') or datos.get('q33_tel') or datos.get('telefono') or datos.get('telefono_principal') or 'No proporcionado'
    nombre_completo = f"{nombre} {apellido}".strip() or email_c or 'Cliente'

    # Labels y colores por tipo
    configs = {
        'evaluacion':        {'label':'Evaluación de Perfil B1/B2',   'emoji':'📋', 'color':'#001F73'},
        'evaluacion_rrss':   {'label':'Evaluación Redes Sociales',      'emoji':'📱', 'color':'#7C3AED'},
        'evaluacion_propia': {'label':'Evaluación Propia',              'emoji':'🧠', 'color':'#2563EB'},
        'ds160':             {'label':'Formulario DS-160',              'emoji':'🛂', 'color':'#001F73'},
        'globalentry':       {'label':'Global Entry / TSA PreCheck',    'emoji':'🌐', 'color':'#16A34A'},
        'global_entry':      {'label':'Global Entry / TSA PreCheck',    'emoji':'🌐', 'color':'#16A34A'},
        'pasaporte':         {'label':'Pasaporte Dominicano',           'emoji':'📘', 'color':'#0369A1'},
        'pasaporte_nuevo':   {'label':'Solicitud Pasaporte Nuevo',      'emoji':'📘', 'color':'#0369A1'},
        'pasaporte_renovacion': {'label':'Solicitud Renovación Pasaporte','emoji':'📘', 'color':'#0369A1'},
        'cita_emergencia':   {'label':'Cita de Emergencia',             'emoji':'⚡', 'color':'#DC2626'},
        'agenda_virtual':    {'label':'Agendamiento de Sesión Virtual', 'emoji':'📅', 'color':'#059669'},
    }
    cfg = configs.get(tipo, {'label': tipo.replace('_',' ').title(), 'emoji':'📩', 'color':'#001F73'})
    tipo_label = cfg['label']
    emoji      = cfg['emoji']
    color      = cfg['color']
    asunto     = f"{emoji} [{tipo_label}] — {nombre_completo}"

    # Campos específicos por tipo
    campos_extra = ''
    if tipo in ('evaluacion','evaluacion_rrss','evaluacion_propia'):
        plan = datos.get('plan','')
        fuente = datos.get('fuente','')
        ciudad = datos.get('ciudad','')
        campos_extra = f"""
        <tr><td style='color:#64748B;padding:4px 0'>Plan</td><td><b>{plan or '—'}</b></td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Ciudad</td><td>{ciudad or '—'}</td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Fuente</td><td>{fuente or '—'}</td></tr>"""
    elif tipo in ('globalentry','global_entry'):
        programa = datos.get('programa','')
        cedula   = datos.get('cedula','')
        campos_extra = f"""
        <tr><td style='color:#64748B;padding:4px 0'>Programa</td><td><b>{programa or 'Global Entry'}</b></td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Cédula</td><td>{cedula or '—'}</td></tr>"""
    elif tipo == 'ds160':
        pasaporte = datos.get('numero_pasaporte') or datos.get('q43_numpas','')
        proposito = datos.get('proposito_viaje') or datos.get('q55_proposito','')
        ocupacion = datos.get('ocupacion_actual') or datos.get('q131_ocupacion','')
        campos_extra = f"""
        <tr><td style='color:#64748B;padding:4px 0'>Pasaporte</td><td>{pasaporte or '—'}</td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Propósito</td><td>{proposito or '—'}</td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Ocupación</td><td>{ocupacion or '—'}</td></tr>"""
    elif tipo == 'pasaporte':
        tipo_pas = datos.get('q95_razon_neg','').split('|')[0].replace('TIPO:','').strip() if '|' in datos.get('q95_razon_neg','') else ''
        oficina  = datos.get('q65_dir_hospedaje','')
        campos_extra = f"""
        <tr><td style='color:#64748B;padding:4px 0'>Tipo trámite</td><td><b>{tipo_pas or '—'}</b></td></tr>
        <tr><td style='color:#64748B;padding:4px 0'>Oficina</td><td>{oficina or '—'}</td></tr>"""

    html_body = f"""
    <div style='font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#F8F9FF;border-radius:12px;overflow:hidden'>
      <div style='background:{color};padding:20px 24px;'>
        <div style='font-size:22px;font-weight:900;color:#fff'>{emoji} TengoVisaRD</div>
        <div style='font-size:13px;color:rgba(255,255,255,.75);margin-top:2px'>Nueva solicitud recibida</div>
      </div>
      <div style='padding:24px'>
        <div style='background:{color}18;border-left:4px solid {color};border-radius:6px;padding:12px 16px;margin-bottom:18px'>
          <div style='font-size:11px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:.05em'>Tipo de servicio</div>
          <div style='font-size:16px;font-weight:800;color:#0A0F2E;margin-top:2px'>{tipo_label}</div>
        </div>
        <table style='width:100%;border-collapse:collapse;font-size:13.5px'>
          <tr><td style='color:#64748B;padding:4px 0;width:38%'>Nombre</td><td><b>{nombre_completo}</b></td></tr>
          <tr><td style='color:#64748B;padding:4px 0'>Email</td><td><a href='mailto:{email_c}' style='color:{color}'>{email_c or '—'}</a></td></tr>
          <tr><td style='color:#64748B;padding:4px 0'>📱 Teléfono</td><td><b style='color:#DC2626'>{telefono}</b></td></tr>
          {campos_extra}
        </table>
        <div style='margin-top:20px;text-align:center'>
          <a href='https://crm.tengovisard.com/ds160/admin.html' style='display:inline-block;background:{color};color:#fff;padding:10px 22px;border-radius:8px;text-decoration:none;font-weight:700;font-size:13px'>Ver en el Panel CRM →</a>
        </div>
      </div>
      <div style='background:#E8ECF8;padding:12px 24px;font-size:11px;color:#94A3B8;text-align:center'>
        TengoVisaRD · Asesoría Migratoria · Santo Domingo, RD · 849-918-9998
      </div>
    </div>"""

    payload = jj.dumps({
        "from": "TengoVisaRD <noreply@tengovisard.com>",
        "to": ["tengovisa@gmail.com"],
        "subject": asunto,
        "html": html_body
    })
    try:
        cmd = ["curl","-s","-X","POST","https://api.resend.com/emails",
               "-H",f"Authorization: Bearer {os.getenv('RESEND_API_KEY','re_3t41id3F_LoM2iy8EFNG76HnXTYxLRbu5')}",
               "-H","Content-Type: application/json","-d",payload]
        subprocess.run(cmd, timeout=8, capture_output=True)
    except Exception as e:
        pass


def generar_pdf(tipo: str, datos: dict) -> str:
    """Generar PDF con los datos del formulario"""
    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    doc = SimpleDocTemplate(tmp.name, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#001F73'), spaceAfter=6)
    h2_style = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#FF1117'), spaceBefore=12, spaceAfter=4)
    normal = ParagraphStyle('norm', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    
    tipo_labels = {
        'evaluacion':'Evaluación de Perfil Migratorio',
        'evaluacion_rrss':'Evaluación RRSS',
        'ds160':'Formulario DS-160',
        'globalentry':'Global Entry',
        'pasaporte_renovacion':'Solicitud Renovación Pasaporte',
        'pasaporte_nuevo':'Solicitud Pasaporte Nuevo',
        'pasaporte':'Pasaporte Dominicano'
    }
    
    story.append(Paragraph(f"Tengo Visa RD — {tipo_labels.get(tipo,tipo)}", title_style))
    story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} | crm.tengovisard.com", normal))
    story.append(Spacer(1, 12))
    
    # Agrupar datos
    grupos = {}
    for k, v in datos.items():
        if not v or k in ['lead_id','ia_analisis'] or len(str(v)) > 500:
            continue
        prefix = k.split('_')[0] if '_' in k else 'general'
        if prefix not in grupos:
            grupos[prefix] = []
        grupos[prefix].append((k.replace('_',' ').replace('q','Q').title(), str(v)))
    
    for grupo, items in grupos.items():
        story.append(Paragraph(grupo.upper(), h2_style))
        table_data = [['Campo', 'Valor']]
        for label, val in items:
            table_data.append([label[:40], val[:80]])
        t = Table(table_data, colWidths=[2.5*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#001F73')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTSIZE',(0,0),(-1,0),8),('FONTSIZE',(0,1),(-1,-1),8),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F7FB')]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#D8E1F0')),
            ('PADDING',(0,0),(-1,-1),4),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))
    
    doc.build(story)
    return tmp.name

@app.get("/pdf/{tipo}/{lead_id}", dependencies=[Depends(chk)])
def get_pdf(tipo: str, lead_id: str):
    try:
        if tipo == 'evaluacion':
            leads = sb().schema("crm").table("leads").select("*").eq("id", lead_id).execute().data
            if not leads: raise HTTPException(404, "No encontrado")
            datos = leads[0]
        elif tipo == 'ds160':
            casos = sb().table("ds160_casos").select("*").eq("id", lead_id).execute().data
            if not casos: raise HTTPException(404, "No encontrado")
            datos = casos[0].get('datos', {})
        else:
            raise HTTPException(400, "Tipo inválido")
        
        pdf_path = generar_pdf(tipo, datos)
        nombre = datos.get('nombre','documento') or datos.get('q1_apellido','documento')
        return FileResponse(pdf_path, media_type='application/pdf', 
                          filename=f'{tipo}_{nombre}_{datetime.now().strftime("%Y%m%d")}.pdf')
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/crm/evaluaciones/{lead_id}/ia", dependencies=[Depends(chk)])
async def crm_eval_ia(lead_id: str):
    import urllib.request as ur3, json as j3
    try:
        # Obtener datos del lead
        lead = sb().schema("crm").table("leads").select("*").eq("id", lead_id).execute().data
        if not lead: raise HTTPException(404, "Lead no encontrado")
        lead = lead[0]
        ia = lead.get("ia_analisis") or {}
        dc = ia.get("datos_completos") or {}
        dp = dc.get("datos_personales") or {}
        pl = dc.get("perfil_laboral") or {}
        pe = dc.get("perfil_economico") or {}
        pm = dc.get("perfil_migratorio") or {}
        pv = dc.get("proposito_viaje") or {}

        perfil = f"""
DATOS DEL SOLICITANTE — Evaluación Visa B1/B2
===============================================
INFORMACIÓN PERSONAL:
- Nombre: {lead.get('nombre','')} {lead.get('apellido','')}
- Edad: {lead.get('edad') or dp.get('edad','No especificada')} años
- Ciudad: {lead.get('ciudad') or dp.get('ciudad','No especificada')}, República Dominicana
- Estado Civil: {dp.get('estado_civil','No especificado')}
- Hijos/Dependientes: {dp.get('hijos',0)}

PERFIL LABORAL:
- Ocupación: {lead.get('ocupacion') or pl.get('ocupacion','No especificada')}
- Tipo de empleo: {pl.get('empleo_tipo') or pl.get('tipo_empleo','No especificado')}
- Antigüedad: {pl.get('antiguedad','No especificada')}
- Ingreso mensual: RD${pl.get('salario_mensual',0):,.0f} (≈USD${(pl.get('salario_mensual',0)/57):,.0f})
- Nivel académico: {pl.get('nivel_academico','No especificado')}

PERFIL ECONÓMICO:
- Banco: {pe.get('banco','No especificado')}
- Vehículo propio: {'Sí' if pe.get('tiene_vehiculo') else 'No'}
- Propiedad inmueble: {'Sí' if pe.get('tiene_propiedad') else 'No'}
- Nivel de ahorros: {pe.get('ahorros','No especificado')}

PERFIL MIGRATORIO:
- Visas previas USA: {pm.get('visas_anteriores','Ninguna')}
- Ha viajado antes: {'Sí' if pm.get('ha_viajado') else 'No'}
- Familia en EE.UU.: {pm.get('familia_eeuu','Ninguna')}
- Negaciones previas: {pm.get('negaciones','Ninguna')}

PROPÓSITO DEL VIAJE:
- Motivo: {pv.get('proposito','Turismo')}
- Duración planeada: {pv.get('duracion','No especificada')}
- Destino: {pv.get('destino','No especificado')}

SCORE SISTEMA INTERNO: {lead.get('score',0)}/100
TEMPERATURA: {lead.get('lead_temperatura','FRIO')}
ALERTAS DEL SISTEMA: {', '.join([a.get('nombre','') for a in ia.get('alertas',[])]) or 'Ninguna'}
"""

        sys_prompt = """Eres el Analista Migratorio Senior de TengoVisaRD. Actúas como ex-oficial consular del Departamento de Estado de EE.UU. con 20 años de experiencia en visas B1/B2, con conocimiento directo de los criterios reales de la Embajada americana en Santo Domingo, República Dominicana.

CONTEXTO REAL 2026:
- Tasa de aprobación RD: 38–42%
- Perfil más escrutado: 22–40 años, sin visa previa, ingresos informales
- Criterio principal: INA §214(b) — el solicitante DEBE demostrar que regresará
- La coherencia entre trabajo, ingresos y propósito del viaje es el factor #1

REGLAS DE ANÁLISIS:
- Sé brutalmente honesto. Si el perfil es débil, dilo directamente
- Nunca des falsas esperanzas ni respuestas genéricas
- Todas las recomendaciones deben ser específicas y accionables
- Cada riesgo debe tener una solución concreta

RESPONDE EN ESPAÑOL. FORMATO OBLIGATORIO EN ESTE ORDEN:

## ⚡ VEREDICTO INMEDIATO
**[APROBACIÓN PROBABLE | RIESGO MODERADO | ALTO RIESGO DE NEGACIÓN]**
Probabilidad actual: XX% → Con mejoras: XX%

---

## 📊 SCORING DETALLADO (100 puntos)
| Categoría | Score | Máx | Estado |
|-----------|-------|-----|--------|
| Arraigo Económico | X | 25 | 🟢/🟡/🔴 |
| Arraigo Familiar | X | 20 | 🟢/🟡/🔴 |
| Estabilidad Laboral | X | 20 | 🟢/🟡/🔴 |
| Historial Migratorio | X | 15 | 🟢/🟡/🔴 |
| Propósito del Viaje | X | 10 | 🟢/🟡/🔴 |
| Perfil Demográfico | X | 10 | 🟢/🟡/🔴 |
| **TOTAL** | **X** | **100** | |

---

## ✅ FORTALEZAS REALES DEL CASO
(Solo las que tienen peso real en la decisión consular)

## 🚨 VULNERABILIDADES CRÍTICAS
(Ordenadas por impacto — exactamente qué preguntaría el oficial)

---

## 🎯 CARGO ÓPTIMO PARA EL DS-160
- **Cargo en español:** [título que proyecta autoridad y estabilidad]
- **Cargo en inglés:** [traducción estratégica]
- **Por qué:** [justificación en 2 líneas]

---

## 📋 PERFIL DS-160 READY
(Redacta el perfil completo del solicitante como si fuera para presentar al cónsul — máximo 8 líneas, tono formal, datos concretos)

---

## 📝 NOTA INTERNA CONSULAR (simulada)
NIV NOTES: Applicant: [nombre] | Nationality: DO
Employment: [empresa] | Financial ties: [evaluación]
Home country ties: [evaluación] | Purpose coherence: [evaluación]
**RECOMMENDATION: APPROVE/REFUSE 214b** | Reason: [motivo técnico]

---

## 🎙️ ESTRATEGIA DE ENTREVISTA
**Narrativa central (45 segundos):**
"[texto exacto que debe decir el solicitante]"

**Pregunta más probable del cónsul:**
[pregunta específica para este perfil]
→ Respuesta óptima: [respuesta exacta, natural, corta]

**3 preguntas trampa con respuestas:**
1. [pregunta] → [respuesta]
2. [pregunta] → [respuesta]
3. [pregunta] → [respuesta]

**Lo que NUNCA debe decir:**
- [lista específica para este perfil]

---

## 📂 DOCUMENTOS PRIORITARIOS

**IMPRESCINDIBLES** (sin estos hay rechazo inmediato):
- [documento] — Por qué lo piden y cómo presentarlo

**IMPORTANTES** (aumentan probabilidad):
- [documento] — Impacto en el caso

**OPCIONALES** (refuerzan el perfil):
- [documento]

---

## 🗓️ PLAN DE ACCIÓN
(Pasos específicos con fechas o condiciones — máximo 7 pasos)
1. [acción concreta con plazo]
2. ...

---

## 🔴 DECISIÓN FINAL
**Clasificación:** Fuerte / Aceptable / Riesgoso / Débil
**Decisión:** APLICAR AHORA / MEJORAR ANTES / NO APLICAR
**Plazo recomendado:** [cuándo aplicar y por qué]

Reporte generado por TengoVisaRD · Asesoría Migratoria · Santo Domingo, RD"""

        prompt = sys_prompt + """

Ahora evalúa este caso específico:

""" + perfil + """

IMPORTANTE: 
- Usa exactamente el formato estructurado especificado
- Incluye las tablas de scoring con emojis de colores
- Sé específico con nombres, montos y fechas cuando los tengas
- La nota del oficial debe parecer real, en inglés técnico consular
- Las preguntas trampa deben ser las que REALMENTE hace este perfil de oficial
- Basate en datos reales de aprobaciones/negaciones Embajada Santo Domingo 2025-2026
"""

        payload = j3.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 4000,
            "system": "Eres el mejor experto mundial en visas B1/B2. Respondes siempre en español con formato Markdown estructurado, tablas y emojis. Nunca das respuestas genéricas.",
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        r = ur3.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY",""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        resp = ur3.urlopen(r, timeout=90)
        data = j3.loads(resp.read())
        ia_texto = data.get("content",[{}])[0].get("text","Sin respuesta")

        # Guardar en la BD
        ia_update = lead.get("ia_analisis") or {}
        ia_update["ia_texto"] = ia_texto
        ia_update["ia_fecha"] = datetime.now().isoformat()
        sb().schema("crm").table("leads").update({
            "ia_analisis": ia_update,
            "estado": "calificado",
            "updated_at": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        return {"ok": True, "ia_texto": ia_texto}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.delete("/crm/evaluaciones/{lead_id}", dependencies=[Depends(chk)])
def delete_evaluacion(lead_id: str):
    try:
        sb().schema("crm").table("evaluaciones").delete().eq("expediente_id", lead_id).execute()
        sb().table("notas").delete().eq("contenido", lead_id).execute()
        sb().table("leads").delete().eq("id", lead_id).execute()
        return {"ok": True, "deleted": lead_id}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

@app.delete("/crm/ds160/{caso_id}", dependencies=[Depends(chk)])
def delete_ds160(caso_id: str):
    try:
        sb().table("ds160_casos").delete().eq("id", caso_id).execute()
        return {"ok": True, "deleted": caso_id}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

# ══════════════════════════════════════
# MÓDULO CLIENTES COMPLETO
# ══════════════════════════════════════

@app.get("/clientes/lista", dependencies=[Depends(chk)])
def lista_clientes(limit: int = 100, estado: str = None):
    try:
        q = sb().schema("crm").table("clientes").select("*").order("created_at", desc=True).limit(limit)
        if estado: q = q.eq("estado_caso", estado)
        return q.execute().data
    except Exception as e: return {"error": str(e)}

@app.get("/clientes/{cliente_id}", dependencies=[Depends(chk)])
def get_cliente(cliente_id: str):
    try:
        r = sb().schema("crm").table("clientes").select("*").eq("id", cliente_id).execute()
        if not r.data: raise HTTPException(404, "Cliente no encontrado")
        c = r.data[0]
        # Adjuntar pagos, seguimientos y timeline
        pagos = sb().schema("crm").table("pagos").select("*").eq("lead_id", c.get("lead_id", "")).execute().data if c.get("lead_id") else []
        segs = sb().schema("crm").table("seguimientos").select("*").eq("lead_id", c.get("lead_id", "")).order("created_at", desc=True).execute().data if c.get("lead_id") else []
        tl = sb().schema("crm").table("timeline").select("*").eq("lead_id", c.get("lead_id", "")).order("created_at", desc=True).execute().data if c.get("lead_id") else []
        total_pagado = sum(p.get("monto", 0) for p in pagos)
        c["pagos"] = pagos
        c["seguimientos"] = segs
        c["timeline"] = tl
        c["balance"] = (c.get("monto_total") or 0) - total_pagado
        c["monto_pagado_real"] = total_pagado
        return c
    except Exception as e: return {"error": str(e)}

@app.post("/clientes", dependencies=[Depends(chk)])
def crear_cliente(body: dict):
    try:
        body["created_at"] = datetime.now().isoformat()
        body["updated_at"] = datetime.now().isoformat()
        r = sb().schema("crm").table("clientes").insert(body).execute()
        cid = r.data[0]["id"] if r.data else None
        if cid and body.get("lead_id"):
            sb().table("timeline").insert({
                "lead_id": body["lead_id"],
                "evento": "Ficha de cliente creada",
                "icono": "👤",
                "created_at": datetime.now().isoformat()
            }).execute()
        return {"ok": True, "id": cid, "codigo": r.data[0].get("codigo") if r.data else None}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.put("/clientes/{cliente_id}", dependencies=[Depends(chk)])
def actualizar_cliente(cliente_id: str, body: dict):
    try:
        body["updated_at"] = datetime.now().isoformat()
        # Limpiar campos que no existen en la tabla
        campos_validos = [
            "nombre","apellido","cedula","edad","sexo","fecha_nacimiento",
            "telefono","whatsapp","correo","direccion","ciudad","pais",
            "estado_civil","nombre_conyuge","hijos","edades_hijos",
            "ocupacion","empresa","tipo_empleo","ingreso_mensual",
            "tiempo_laborando","paga_impuestos",
            "banco","tiene_cuenta","ahorros","ingresos_adicionales",
            "monto_extra","historial_credito",
            "tiene_vehiculo","detalle_vehiculo","tiene_propiedad",
            "negocio","familia_en_rd",
            "ha_solicitado_visa","resultado_visa","anio_solicitud",
            "motivo_negacion","visa_vigente","historial_viajes",
            "tiene_pasaporte","numero_pasaporte","fecha_emision_pasaporte",
            "fecha_vencimiento_pasaporte","estado_pasaporte",
            "tipo_servicio","estado_caso","asesor","fecha_inicio","etapa",
            "tiene_evaluacion","tiene_ds160","tiene_cita","tiene_preentrevista",
            "monto_total","monto_pagado","metodo_pago","numero_factura",
            "fecha_evaluacion","fecha_ds160","fecha_cita_consular","fecha_preentrevista",
            "estado_seguimiento","ultimo_contacto","proximo_contacto",
            "observaciones","notas_internas","updated_at"
        ]
        data = {k: v for k, v in body.items() if k in campos_validos}
        r = sb().schema("crm").table("clientes").update(data).eq("id", cliente_id).execute()
        return {"ok": True}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.delete("/clientes/{cliente_id}", dependencies=[Depends(chk)])
def eliminar_cliente(cliente_id: str):
    try:
        sb().schema("crm").table("clientes").delete().eq("id", cliente_id).execute()
        return {"ok": True}
    except Exception as e: return {"ok": False, "error": str(e)}

# ══════════════════════════════════════
# INTEGRACIÓN AIS + CITASFLASH
# ══════════════════════════════════════

@app.post("/clientes/{cliente_id}/migrar-citasflash", dependencies=[Depends(chk)])
async def migrar_a_citasflash(cliente_id: str, body: dict = {}):
    """Crea la cuenta del cliente en CitasFlash para búsqueda de cita"""
    import httpx
    try:
        # Obtener datos del cliente
        c = sb().schema("crm").table("clientes").select("*").eq("id", cliente_id).execute().data
        if not c: raise HTTPException(404, "Cliente no encontrado")
        c = c[0]

        # Verificar campos mínimos
        required = ["ais_email", "ais_password", "numero_pasaporte", "ds160_numero"]
        missing = [f for f in required if not c.get(f)]
        if missing:
            return {"ok": False, "error": f"Faltan campos: {', '.join(missing)}"}

        # Login en CitasFlash API
        cf_url = "http://localhost:8000"
        cf_key = "CitaFast2026Bot2"
        
        # Crear cuenta en CitasFlash
        payload = {
            "email": c["ais_email"],
            "password": c["ais_password"],
            "country": "do",
            "facility_id": c.get("facility_id", 75),
            "nombre": f"{c['nombre']} {c['apellido']}",
            "passport_number": c["numero_pasaporte"],
            "ds160_number": c["ds160_numero"],
            "visa_type": "B1/B2",
            "visa_class": c.get("visa_class", "B1/B2"),
            "min_date": str(c.get("fecha_deseada_cita") or ""),
            "asesor": "Tengo Visa RD",
            "contacto_asesor": c.get("whatsapp", ""),
            "estado_pago": "pagado",
            "prioridad": 1,
            "is_active": True
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(f"{cf_url}/cuentas",
                headers={"x-api-key": cf_key, "Content-Type": "application/json"},
                json=payload, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            cf_id = data.get("id")
            
            # Guardar citasflash_id en el cliente
            sb().schema("crm").table("clientes").update({
                "citasflash_id": cf_id,
                "estado_cita": "en_busqueda",
                "updated_at": datetime.now().isoformat()
            }).eq("id", cliente_id).execute()
            
            # Timeline
            sb().schema("crm").table("timeline").insert({
                "lead_id": c.get("lead_id") or cliente_id,
                "evento": "Migrado a CitasFlash",
                "descripcion": f"Cuenta creada en CitasFlash ID: {cf_id}",
                "icono": "🎯",
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {"ok": True, "citasflash_id": cf_id, "mensaje": "Cliente migrado a CitasFlash ✅"}
        else:
            return {"ok": False, "error": r.text[:200]}

    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/clientes/{cliente_id}/estado-cita", dependencies=[Depends(chk)])
async def estado_cita(cliente_id: str):
    """Consulta el estado de la cita desde CitasFlash y actualiza el CRM"""
    import httpx
    try:
        c = sb().schema("crm").table("clientes").select("*").eq("id", cliente_id).execute().data
        if not c: raise HTTPException(404, "Cliente no encontrado")
        c = c[0]
        
        cf_id = c.get("citasflash_id")
        if not cf_id:
            return {"ok": False, "error": "Cliente no tiene cuenta en CitasFlash"}
        
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://localhost:8000/cuentas/{cf_id}",
                headers={"x-api-key": "CitaFast2026Bot2"}, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            schedule_id = data.get("schedule_id")
            booked_date = data.get("booked_date") or data.get("last_appointment_date")
            status = data.get("status", "")
            asc_date = data.get("asc_date")
            
            # Actualizar CRM con datos de CitasFlash
            update = {
                "updated_at": datetime.now().isoformat(),
                "estado_cita": "cita_tomada" if booked_date else "en_busqueda"
            }
            if schedule_id: update["schedule_id"] = str(schedule_id)
            if booked_date: update["cita_tomada"] = booked_date
            if asc_date: update["cita_asc_date"] = asc_date
            if booked_date: update["fecha_cita_consular"] = booked_date
            if booked_date: update["estado_caso"] = "cita_agendada"
            
            sb().schema("crm").table("clientes").update(update).eq("id", cliente_id).execute()
            
            # Timeline si se tomó cita
            if booked_date and not c.get("cita_tomada"):
                sb().schema("crm").table("timeline").insert({
                    "lead_id": c.get("lead_id") or cliente_id,
                    "evento": "🎉 Cita consular tomada",
                    "descripcion": f"Fecha: {booked_date} | Schedule ID: {schedule_id}",
                    "icono": "📅",
                    "created_at": datetime.now().isoformat()
                }).execute()
            
            return {
                "ok": True,
                "schedule_id": schedule_id,
                "booked_date": booked_date,
                "asc_date": asc_date,
                "status": status,
                "estado_cita": update["estado_cita"]
            }
        else:
            return {"ok": False, "error": r.text[:100]}
            
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/clientes/{cliente_id}/pausar-cita", dependencies=[Depends(chk)])
async def pausar_cita(cliente_id: str):
    import httpx
    try:
        c = sb().schema("crm").table("clientes").select("citasflash_id").eq("id", cliente_id).execute().data
        if not c or not c[0].get("citasflash_id"): 
            return {"ok": False, "error": "Sin cuenta CitasFlash"}
        cf_id = c[0]["citasflash_id"]
        async with httpx.AsyncClient() as client:
            await client.patch(f"http://localhost:8000/cuentas/{cf_id}/toggle",
                headers={"x-api-key": "CitaFast2026Bot2"}, timeout=10)
        sb().schema("crm").table("clientes").update({"estado_cita": "pausado","updated_at": datetime.now().isoformat()}).eq("id", cliente_id).execute()
        return {"ok": True, "mensaje": "Cita pausada ✅"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ══════════════════════════════════════
# SYNC AUTOMÁTICO SCHEDULE ID
# ══════════════════════════════════════

@app.post("/sync/schedule-ids", dependencies=[Depends(chk)])
async def sync_schedule_ids():
    """Sincroniza schedule_ids y estados de cita entre CitasFlash y CRM"""
    import httpx
    resultados = []
    try:
        # Obtener todos los clientes con citasflash_id
        clientes = sb().schema("crm").table("clientes").select(
            "id,nombre,apellido,codigo,citasflash_id,schedule_id,cita_tomada,estado_cita"
        ).not_.is_("citasflash_id", "null").execute().data

        if not clientes:
            return {"ok": True, "mensaje": "Sin clientes con CitasFlash vinculado", "actualizados": 0}

        async with httpx.AsyncClient() as client:
            for cli in clientes:
                cf_id = cli.get("citasflash_id")
                try:
                    r = await client.get(
                        f"http://localhost:8000/cuentas/{cf_id}",
                        headers={"x-api-key": "CitaFast2026Bot2"},
                        timeout=8
                    )
                    if r.status_code != 200:
                        continue
                    cf = r.json()
                    update = {"updated_at": datetime.now().isoformat()}
                    changed = False

                    # Schedule ID
                    if cf.get("schedule_id") and str(cf["schedule_id"]) != str(cli.get("schedule_id") or ""):
                        update["schedule_id"] = str(cf["schedule_id"])
                        changed = True

                    # Cita tomada
                    booked = cf.get("booked_date") or cf.get("last_appointment_date")
                    if booked and booked != cli.get("cita_tomada"):
                        update["cita_tomada"] = booked
                        update["fecha_cita_consular"] = booked
                        update["estado_cita"] = "cita_tomada"
                        update["estado_caso"] = "cita_agendada"
                        changed = True

                    # ASC date
                    if cf.get("asc_date"):
                        update["cita_asc_date"] = cf["asc_date"]

                    if changed:
                        sb().schema("crm").table("clientes").update(update).eq("id", cli["id"]).execute()
                        resultados.append({
                            "cliente": cli["codigo"],
                            "schedule_id": update.get("schedule_id"),
                            "cita": update.get("cita_tomada")
                        })
                except Exception:
                    continue

        return {"ok": True, "actualizados": len(resultados), "resultados": resultados}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/clientes/{cliente_id}/schedule", dependencies=[Depends(chk)])
async def get_schedule_info(cliente_id: str):
    """Obtiene info del schedule desde CitasFlash para un cliente"""
    import httpx
    try:
        cli = sb().schema("crm").table("clientes").select("*").eq("id", cliente_id).execute().data
        if not cli: raise HTTPException(404, "No encontrado")
        cli = cli[0]
        cf_id = cli.get("citasflash_id")
        if not cf_id:
            return {"ok": False, "error": "Sin cuenta CitasFlash vinculada"}
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"http://localhost:8000/cuentas/{cf_id}",
                headers={"x-api-key": "CitaFast2026Bot2"},
                timeout=8
            )
        data = r.json()
        return {
            "ok": True,
            "schedule_id": data.get("schedule_id"),
            "status": data.get("status"),
            "booked_date": data.get("booked_date"),
            "asc_date": data.get("asc_date"),
            "is_active": data.get("is_active"),
            "last_appointment_date": data.get("last_appointment_date"),
            "visa_status": data.get("visa_status"),
            "min_date": data.get("min_date"),
            "max_date": data.get("max_date"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/bot/config", dependencies=[Depends(chk)])
async def guardar_bot_config(body: dict):
    """Guarda configuración del bot WhatsApp"""
    try:
        import json
        config_path = "/root/bot_config.json"
        with open(config_path, 'w') as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
        # Reiniciar bot con nueva config
        import subprocess
        subprocess.Popen(['systemctl', 'restart', 'whatsapp-bot'])
        return {"ok": True, "config": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/bot/config", dependencies=[Depends(chk)])
async def get_bot_config():
    try:
        import json
        with open("/root/bot_config.json") as f:
            return json.load(f)
    except:
        return {"hora_inicio":22,"hora_fin":8,"precio_eval":2000,"precio_ds160":5000,"precio_visa":15000,"precio_cita":8000,"tel_asesor":"+18499189998"}

# ══════════════════════════════════════
# BOT REDES — GESTIÓN DE RESPUESTAS
# ══════════════════════════════════════
import json as _json

@app.get("/bot/respuestas", dependencies=[Depends(chk)])
def get_bot_respuestas():
    try:
        with open("/root/bot_respuestas.json") as f:
            return _json.load(f)
    except:
        return {"respuestas": []}

@app.post("/bot/respuestas", dependencies=[Depends(chk)])
def save_bot_respuestas(body: dict):
    try:
        with open("/root/bot_respuestas.json","w") as f:
            _json.dump(body, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.put("/bot/respuestas/{resp_id}", dependencies=[Depends(chk)])
def update_respuesta(resp_id: str, body: dict):
    try:
        with open("/root/bot_respuestas.json") as f:
            data = _json.load(f)
        for i,r in enumerate(data.get("respuestas",[])):
            if r.get("id") == resp_id:
                data["respuestas"][i].update(body)
                break
        else:
            data.setdefault("respuestas",[]).append({**body,"id":resp_id})
        with open("/root/bot_respuestas.json","w") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/bot/respuestas/{resp_id}", dependencies=[Depends(chk)])
def delete_respuesta(resp_id: str):
    try:
        with open("/root/bot_respuestas.json") as f:
            data = _json.load(f)
        data["respuestas"] = [r for r in data.get("respuestas",[]) if r.get("id") != resp_id]
        with open("/root/bot_respuestas.json","w") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/bot/test", dependencies=[Depends(chk)])
def test_bot_respuesta(msg: str = "hola"):
    try:
        import subprocess, json as jj
        r = subprocess.run(
            ['curl','-s',f'http://localhost:8002/test-respuesta?msg={msg}'],
            capture_output=True, text=True, timeout=5
        )
        return jj.loads(r.stdout)
    except Exception as e:
        return {"error": str(e)}

# ══ GOOGLE CALENDAR ══
@app.get("/calendar/citas-hoy", dependencies=[Depends(chk)])
def citas_hoy():
    try:
        import subprocess, json as jj
        r = subprocess.run(
            ['/root/botenv/bin/python', '-c',
             'import sys; sys.path.insert(0,"/root"); from google_calendar_sync import get_citas_hoy; import json; print(json.dumps(get_citas_hoy()))'],
            capture_output=True, text=True, timeout=15
        )
        return jj.loads(r.stdout.strip().split('\n')[-1])
    except Exception as e:
        return []

@app.post("/calendar/sync", dependencies=[Depends(chk)])
def sync_calendar():
    try:
        import subprocess
        r = subprocess.run(
            ['/root/botenv/bin/python', '/root/google_calendar_sync.py'],
            capture_output=True, text=True, timeout=30
        )
        return {"ok": True, "output": r.stdout[-500:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ══ PANEL REDES — MENSAJES TWILIO ══
@app.get("/redes/mensajes-wa", dependencies=[Depends(chk)])
async def mensajes_whatsapp(page: int = 0):
    """Obtiene mensajes WhatsApp de Twilio"""
    import urllib.request as ur, base64
    try:
        cfg = {}
        try:
            with open("/root/bot_config.json") as f:
                cfg = __import__("json").load(f)
        except: pass
        
        sid = cfg.get("twilio_sid","")
        token = cfg.get("twilio_token","")
        num = cfg.get("twilio_num","+14155238886")
        
        # Mensajes recibidos (inbound)
        url_in = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json?To=whatsapp:{num}&PageSize=50"
        # Mensajes enviados (outbound)
        url_out = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json?From=whatsapp:{num}&PageSize=50"
        
        creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
        headers = {"Authorization": f"Basic {creds}"}
        
        msgs_in = []
        msgs_out = []
        
        for url, container in [(url_in, msgs_in), (url_out, msgs_out)]:
            req = ur.Request(url, headers=headers)
            resp = ur.urlopen(req, timeout=10)
            data = __import__("json").loads(resp.read())
            container.extend(data.get("messages", []))
        
        # Combinar y ordenar
        todos = msgs_in + msgs_out
        todos.sort(key=lambda x: x.get("date_created",""), reverse=True)
        
        # Agrupar por número de contacto
        contactos = {}
        for m in todos:
            frm = m.get("from","").replace("whatsapp:","")
            to = m.get("to","").replace("whatsapp:","")
            phone = frm if frm != num else to
            phone = phone.replace(num,"").strip() or frm
            
            if phone not in contactos:
                contactos[phone] = {
                    "phone": phone,
                    "mensajes": [],
                    "ultimo": m.get("date_sent") or m.get("date_created",""),
                    "no_leidos": 0
                }
            contactos[phone]["mensajes"].append({
                "body": m.get("body",""),
                "fecha": (m.get("date_sent") or m.get("date_created",""))[:16],
                "direction": "out" if frm.replace("whatsapp:","") == num else "in",
                "status": m.get("status","")
            })
        
        return {
            "ok": True,
            "contactos": list(contactos.values())[:20],
            "total": len(contactos)
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "contactos": []}

@app.post("/redes/enviar-wa", dependencies=[Depends(chk)])
async def enviar_whatsapp_crm(body: dict):
    """Envía mensaje WhatsApp desde el CRM"""
    import urllib.request as ur, urllib.parse as up, base64
    try:
        cfg = {}
        try:
            with open("/root/bot_config.json") as f:
                cfg = __import__("json").load(f)
        except: pass
        
        sid = cfg.get("twilio_sid","")
        token = cfg.get("twilio_token","")
        num = cfg.get("twilio_num","+14155238886")
        
        to = body.get("to","").strip()
        msg = body.get("mensaje","").strip()
        if not to or not msg:
            return {"ok": False, "error": "Faltan campos"}
        
        data = up.urlencode({
            "To": f"whatsapp:{to}",
            "From": f"whatsapp:{num}",
            "Body": msg
        }).encode()
        
        creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
        req = ur.Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            data=data,
            headers={"Authorization": f"Basic {creds}"}
        )
        resp = ur.urlopen(req, timeout=10)
        result = __import__("json").loads(resp.read())
        return {"ok": True, "sid": result.get("sid"), "status": result.get("status")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ══ GENERAR PDF EVALUACIÓN ══
@app.get("/crm/evaluaciones/{lead_id}/pdf", dependencies=[Depends(chk)])
async def generar_pdf_evaluacion(lead_id: str):
    """Genera PDF de evaluación migratoria"""
    try:
        import subprocess, os
        # Obtener datos del lead
        lead = sb().schema("crm").table("leads").select("*").eq("id", lead_id).execute().data
        if not lead: raise HTTPException(404, "Lead no encontrado")
        lead = lead[0]
        ia = lead.get("ia_analisis") or {}
        dc = ia.get("datos_completos") or {}
        dp = dc.get("datos_personales") or {}
        pl = dc.get("perfil_laboral") or {}

        data = {
            "nombre": lead.get("nombre",""),
            "apellido": lead.get("apellido",""),
            "email": lead.get("email",""),
            "whatsapp": lead.get("whatsapp",""),
            "edad": lead.get("edad") or dp.get("edad", 0),
            "ciudad": lead.get("ciudad") or dp.get("ciudad",""),
            "ocupacion": lead.get("ocupacion") or pl.get("ocupacion",""),
            "estado_civil": dp.get("estado_civil",""),
            "hijos": dp.get("hijos", 0),
            "score": lead.get("score", 0),
            "ia_texto": ia.get("ia_texto",""),
        }

        pdf_path = f"/tmp/evaluacion_{lead_id}.pdf"
        # Importar y usar el generador
        import sys; sys.path.insert(0, '/root')
        from generar_evaluacion_pdf import generar_pdf
        generar_pdf(data, pdf_path)

        from fastapi.responses import FileResponse
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"TengoVisa_Evaluacion_{data['nombre']}_{data['apellido']}.pdf"
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════
# DS-160 EXTENDIDO v2 — Export + Notes + Fields
# ═══════════════════════════════════════════════
from fastapi.responses import JSONResponse
import json as _json

_DS160_LEGACY = {"q1_apellido":"apellido_primario","q2_nombre":"nombre","q7_sexo":"sexo","q8_civil":"estado_civil","q9_dob":"fecha_nacimiento","q10_ciudad_nac":"ciudad_nacimiento","q12_pais_nac":"pais_nacimiento","q13_nacionalidad":"pais_nacionalidad","q20_cedula":"numero_id_tributario","q23_dir1":"direccion_rd","q25_ciudad":"ciudad_rd","q26_provincia":"provincia_rd","q33_tel":"telefono_principal","q36_email":"email","q42_tipo_pas":"tipo_pasaporte","q43_numpas":"numero_pasaporte","q45_pais_pas":"pais_emisor_pasaporte","q48_emision":"fecha_emision_pasaporte","q49_vence":"fecha_vencimiento_pasaporte","q55_proposito":"proposito_viaje","q64_duracion":"duracion_estancia","q65_dir_hospedaje":"itinerario","q66_ciudad_hosp":"ciudad_eeuu","q67_estado_hosp":"estado_eeuu","q68_paga":"paga_viaje","q82_estuvo":"viajo_antes_eeuu","q93_negacion":"visa_negada_antes","q95_razon_neg":"detalle_visa_negada","q99_cont_nom":"nombre_contacto_eeuu","q101_cont_rel":"relacion_contacto_eeuu","q102_cont_dir":"direccion_eeuu","q103_cont_ciudad":"ciudad_eeuu","q105_cont_zip":"zip_eeuu","q106_cont_tel":"telefono_contacto_eeuu","q107_cont_email":"email_contacto","q131_ocupacion":"ocupacion_actual","q132_empleador":"empleador_actual","q133_dir_emp1":"direccion_empleador","q138_emp_tel":"telefono_empleador","q139_emp_inicio":"fecha_inicio_trabajo","q141_funciones":"descripcion_trabajo","q152_escuela":"nombre_institucion","q154_carrera":"nivel_educacion","q174":"enfermedad_comunicable","q177":"arrestado","q185":"deportado_alguna_vez","q187":"actividad_terrorista","q199":"presente_eeuu_sin_permiso"}

_DS160_ORDER = ["q1_apellido","q2_nombre","q3_otros_nombres","q4_otro_apellido","q5_otro_nombre","q6_nombre_nativo","q7_sexo","q8_civil","q9_dob","q10_ciudad_nac","q11_prov_nac","q12_pais_nac","q13_nacionalidad","q14_otra_nac","q15_otra_nac_pais","q16_pas_otra_nac","q17_pas_otro","q18_emision_otro","q19_vence_otro","q20_cedula","q21_ssn","q22_tin","q23_dir1","q24_dir2","q25_ciudad","q26_provincia","q27_postal","q28_pais_res","q29_dir_ant","q30_dir_ant","q31_ciudad_ant","q32_pais_ant","q33_tel","q34_tel2","q35_tel_trab","q36_email","q37_redes","q38_red1","q39_user1","q40_red2","q41_user2","q42_tipo_pas","q43_numpas","q44_libreta","q45_pais_pas","q46_ciudad_emision","q47_prov_emision","q48_emision","q49_vence","q50_perdio_pas","q51_pas_perdido","q52_pais_pas_perdido","q53_explicacion_perdido","q54_solicitante","q55_proposito","q56_planes","q57_llegada","q58_vuelo_lleg","q59_ciudad_lleg","q60_salida","q61_vuelo_sal","q62_ciudad_sal","q63_llegada_est","q64_duracion","q65_dir_hospedaje","q66_ciudad_hosp","q67_estado_hosp","q68_paga","q69_pat_apellido","q70_pat_nombre","q71_pat_tel","q72_pat_email","q73_pat_relacion","q74_empresa_pat","q75_dir_empresa","q76_compan","q77_grupo","q78_grupo_nom","q79_comp1_ap","q80_comp1_nom","q81_comp1_rel","q82_estuvo","q83_fecha_vis1","q84_dur_vis1","q85_fecha_vis2","q86_dur_vis2","q87_visa_prev","q88_visa_emision","q89_visa_num","q90_mismo_tipo","q91_mismo_pais","q92_diez_anos","q93_negacion","q94_negacion_donde","q95_razon_neg","q96_peticion","q97_peticion_exp","q98_cont_ap","q99_cont_nom","q100_cont_org","q101_cont_rel","q102_cont_dir","q103_cont_ciudad","q104_cont_estado","q105_cont_zip","q106_cont_tel","q107_cont_email","q108_padre_ap","q109_padre_nom","q110_padre_dob","q111_padre_eeuu","q112_padre_estatus","q113_madre_ap","q114_madre_nom","q115_madre_dob","q116_madre_eeuu","q117_madre_estatus","q118_fam_inm","q119_fam1_ap","q120_fam1_nom","q121_fam1_rel","q122_fam1_estatus","q123_otros_fam","q124_otros_fam_exp","q125_con_ap","q126_con_nom","q127_con_dob","q128_con_pais_nac","q129_con_ciudadania","q130_con_dir","q131_ocupacion","q132_empleador","q133_dir_emp1","q134_emp_ciudad","q135_emp_prov","q136_emp_pais","q137_emp_postal","q138_emp_tel","q139_emp_inicio","q140_salario","q141_funciones","q142_emp_ant","q143_emp_ant_nom","q144_dir_emp_ant","q145_tel_emp_ant","q146_cargo_ant","q147_inicio_ant","q148_fin_ant","q149_func_ant","q151_edu","q152_escuela","q153_escuela_dir","q154_carrera","q155_edu_inicio","q156_edu_fin","q157_clan","q158_clan_nom","q159_paises","q160_idiomas","q161_org","q162_org_nom","q163_habilidades","q164_habilidades_exp","q165_militar","q166_mil_pais","q167_mil_rama","q168_mil_rango","q169_mil_esp","q170_mil_inicio","q171_mil_fin","q172_paramilitar","q173_paramilitar_exp","q174","q175","q176","q177","q178_arresto","q179","q180","q181","q182","q183","q184","q185","q186","q187","q188","q189","q190","q191","q192","q193","q194","q195","q196","q197","q198","q199","q200","q201","q202","q203","q204","q205","q206","q207","q222_asistido","q223_asist_ap","q224_asist_nom","q225_asist_org","q226_asist_dir","q227_asist_tel"]


def _build_ordered_fields(datos: dict) -> dict:
    fields = {}
    for k in _DS160_ORDER:
        v = datos.get(k)
        if not v and k in _DS160_LEGACY:
            v = datos.get(_DS160_LEGACY[k])
        if isinstance(v, bool):
            v = "YES" if v else "NO"
        fields[k] = str(v) if v is not None and str(v).strip() else None
    return fields


@app.get("/ds160/export/v2/{caso_id}", dependencies=[Depends(chk)])
async def ds160_export_v2(caso_id: str):
    """Export DS-160 JSON ordenado Q1-Q227 con fallback legacy"""
    try:
        r = sb().schema("crm").table("ds160_casos").select("*").eq("id", caso_id).execute()
        if not r.data:
            raise HTTPException(404, "No encontrado")
        caso  = r.data[0]
        datos = caso.get("datos") or {}
        fields  = _build_ordered_fields(datos)
        filled  = sum(1 for v in fields.values() if v)
        sb().schema("crm").table("ds160_casos").update({
            "estado": "exportado",
            "updated_at": datetime.now().isoformat()
        }).eq("id", caso_id).execute()
        export = {
            "meta": {
                "caso_id":       caso_id,
                "email":         datos.get("email", ""),
                "nombre":        datos.get("nombre", "") or datos.get("q2_nombre", ""),
                "apellido":      datos.get("apellido_primario", "") or datos.get("q1_apellido", ""),
                "pasaporte":     datos.get("numero_pasaporte", "") or datos.get("q43_numpas", ""),
                "advisor_notes": caso.get("revision_notas", ""),
                "generated_by":  "TengoVisaRD CRM",
                "generated_at":  datetime.now().isoformat(),
                "form_version":  "DS-160-2025",
                "embassy":       "Santo Domingo, Dominican Republic",
                "total_fields":  len(_DS160_ORDER),
                "filled_fields": filled,
            },
            "fields": fields
        }
        return JSONResponse(
            content=export,
            headers={"Content-Disposition": f'attachment; filename="ds160_{datos.get("email","caso")}_{datetime.now().strftime("%Y-%m-%d")}.json"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ds160/notes/v2/{caso_id}", dependencies=[Depends(chk)])
async def ds160_notes_v2(caso_id: str, body: dict):
    try:
        sb().schema("crm").table("ds160_casos").update({
            "revision_notas": body.get("notes", ""),
            "estado": "revisado",
            "updated_at": datetime.now().isoformat()
        }).eq("id", caso_id).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ds160/field/v2/{caso_id}", dependencies=[Depends(chk)])
async def ds160_field_v2(caso_id: str, body: dict):
    try:
        campo = body.get("field", "")
        valor = body.get("value", "")
        # Columnas especiales que van directo a la tabla, no a datos{}
        COLS_DIRECTAS = {"estado", "numero_caso", "expediente_id", "cliente_id"}
        if campo in COLS_DIRECTAS:
            sb().schema("crm").table("ds160_casos").update({campo: valor}).eq("id", caso_id).execute()
            return {"ok": True, "campo": campo, "directo": True}
        r = sb().schema("crm").table("ds160_casos").select("datos").eq("id", caso_id).execute()
        if not r.data:
            return {"ok": False, "error": "No encontrado"}
        datos = r.data[0].get("datos") or {}
        datos[campo] = valor
        sb().schema("crm").table("ds160_casos").update({
            "datos": datos,
            "updated_at": datetime.now().isoformat()
        }).eq("id", caso_id).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ds160/all/v2", dependencies=[Depends(chk)])
async def ds160_list_v2(q: str = "", status: str = "", limit: int = 200):
    try:
        query = sb().schema("crm").table("ds160_casos").select("*").order("created_at", desc=True).limit(limit)
        query = query.neq("estado", "archivado")
        if status:
            query = query.eq("estado", status)
        rows = query.execute().data or []
        for row in rows:
            d = row.get("datos") or {}
            row["_nombre"]   = d.get("nombre", "") or d.get("q2_nombre", "")
            row["_apellido"] = d.get("apellido_primario", "") or d.get("q1_apellido", "")
            row["_email"]    = d.get("email", "")
            row["_pasaporte"]= d.get("numero_pasaporte", "") or d.get("q43_numpas", "")
            # Calcular % usando AMBOS esquemas (nuevo q- y viejo legacy)
            filled = sum(
                1 for k in _DS160_ORDER
                if any([
                    d.get(k) and str(d.get(k)).strip() and str(d.get(k)) not in ['null','None',''],
                    _DS160_LEGACY.get(k) and d.get(_DS160_LEGACY.get(k,'')) and
                    str(d.get(_DS160_LEGACY.get(k,''))).strip() and
                    str(d.get(_DS160_LEGACY.get(k,''))) not in ['null','None','']
                ])
            )
            row["_pct"] = round((filled / len(_DS160_ORDER)) * 100)
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in (r["_nombre"]+r["_apellido"]+r["_email"]+r["_pasaporte"]).lower()]
        return {"ok": True, "total": len(rows), "casos": rows, "records": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ds160/download/{caso_id}")
async def ds160_download(caso_id: str):
    """Genera y sirve JSON DS-160 directamente desde Supabase"""
    import subprocess, os, glob
    try:
        result = subprocess.run(
            ['python3', '/var/www/crm/ds160/export_ds160.py', caso_id],
            capture_output=True, text=True, timeout=30
        )
        # Buscar el archivo generado
        files = glob.glob(f'/var/www/crm/ds160/exports/ds160_*_{caso_id[:8]}.json')
        if not files:
            return {"ok": False, "error": "No se generó el archivo", "stderr": result.stderr}
        fname = files[0]
        with open(fname, 'r', encoding='utf-8') as f:
            content = _json.load(f)
        return JSONResponse(
            content=content,
            headers={"Content-Disposition": f'attachment; filename="{os.path.basename(fname)}"'}
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.delete("/ds160/{caso_id}", dependencies=[Depends(chk)])
def delete_ds160_v2(caso_id: str):
    try:
        sb().schema("crm").table("ds160_casos").delete().eq("id", caso_id).execute()
        return {"ok": True, "deleted": caso_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ══════════════════════════════════════════════════
# NOTIFICACIONES DS-160 — WhatsApp + Email + Badge
# ══════════════════════════════════════════════════
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cache anti-duplicados — ventana de 5 minutos por email
_notif_cache = {}

def notify_ds160(nombre: str, apellido: str, email: str, pasaporte: str, caso_id: str, whatsapp: str = ""):
    global _notif_cache
    from datetime import datetime, timedelta
    now = datetime.now()
    cache_key = f"{email}_{caso_id}"
    # Bloquear si ya se notificó en los últimos 5 minutos
    if cache_key in _notif_cache:
        last = _notif_cache[cache_key]
        if now - last < timedelta(minutes=5):
            print(f"Notif duplicada bloqueada ({(now-last).seconds}s): {email}")
            return
    _notif_cache[cache_key] = now
    # Limpiar cache antiguo
    _notif_cache = {k:v for k,v in _notif_cache.items() if now-v < timedelta(minutes=10)}
    """Dispara las 3 notificaciones cuando llega un DS-160"""
    msg_text = f"""
🛂 NUEVO DS-160 RECIBIDO

👤 Cliente: {nombre} {apellido}
📧 Email: {email}
🛂 Pasaporte: {pasaporte}
🆔 Caso ID: {caso_id[:8]}
🕐 Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Ver en panel:
https://crm.tengovisard.com/ds160/admin.html
""".strip()

    # 1 — WhatsApp via Twilio
    try:
        send_push("🛂 Nuevo DS-160", f"{nombre} · {email}")
        import urllib.request, urllib.parse, base64
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_tok = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_WHATSAPP_NUMBER','whatsapp:+14155238886')
        to_number = 'whatsapp:+18499189998'
        msg_wa = f"""🛂 *NUEVO DS-160 — TengoVisaRD*

👤 *{nombre} {apellido}*
📧 {email}
🛂 Pasaporte: {pasaporte if pasaporte else '—'}
📱 WhatsApp: {whatsapp if whatsapp else '—'}
🆔 Caso: {caso_id[:8]}

👉 https://crm.tengovisard.com/ds160/admin.html"""
        payload = urllib.parse.urlencode({
            'From': twilio_from if twilio_from.startswith('whatsapp:') else f'whatsapp:{twilio_from}',
            'To': to_number,
            'Body': msg_wa
        }).encode()
        creds = base64.b64encode(f'{twilio_sid}:{twilio_tok}'.encode()).decode()
        req = urllib.request.Request(
            f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json',
            data=payload,
            headers={'Authorization': f'Basic {creds}', 'Content-Type': 'application/x-www-form-urlencoded'}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"WhatsApp notify error: {e}")

    # 2 — Email via Gmail SMTP
    try:
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_pass = os.getenv('SMTP_PASS', '')
        smtp_to   = os.getenv('NOTIFY_EMAIL', 'diocuma@gmail.com')
        if smtp_user and smtp_pass:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'🛂 Nuevo DS-160 — {nombre} {apellido}'
            msg['From'] = smtp_user
            msg['To'] = smtp_to
            html = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto">
  <div style="background:#001F73;color:#fff;padding:20px;border-radius:12px 12px 0 0">
    <h2 style="margin:0">🛂 Nuevo DS-160 Recibido</h2>
    <p style="margin:4px 0 0;opacity:.8;font-size:13px">TengoVisaRD CRM · {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
  </div>
  <div style="background:#f8fafc;padding:20px;border:1px solid #e2e8f0">
    <table style="width:100%;font-size:14px">
      <tr><td style="color:#64748b;padding:6px 0;width:120px">👤 Cliente</td><td style="font-weight:800;font-size:15px">{nombre} {apellido}</td></tr>
      <tr><td style="color:#64748b;padding:6px 0">📧 Email</td><td>{email}</td></tr>
      <tr><td style="color:#64748b;padding:6px 0">🛂 Pasaporte</td><td style="font-family:monospace;font-weight:700">{pasaporte if pasaporte else '—'}</td></tr>
      <tr><td style="color:#64748b;padding:6px 0">📱 WhatsApp</td><td style="font-weight:700">{whatsapp if whatsapp else '—'}</td></tr>
      <tr><td style="color:#64748b;padding:6px 0">🆔 Caso ID</td><td style="font-family:monospace">{caso_id[:8]}</td></tr>
    </table>
    <a href="https://crm.tengovisard.com/ds160/admin.html#{caso_id}" style="display:block;margin-top:16px;padding:14px;background:#001F73;color:#fff;text-align:center;border-radius:8px;text-decoration:none;font-weight:800;font-size:15px">
      👁 Ver expediente en el panel →
    </a>
  </div>
  <div style="background:#fff;padding:12px 20px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;text-align:center;font-size:11px;color:#94A3B8">
    TengoVisaRD · Asesoría Migratoria · Santo Domingo, RD
  </div>
</div>"""
            msg.attach(MIMEText(html, 'html'))
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as s:
                s.login(smtp_user, smtp_pass)
                s.sendmail(smtp_user, smtp_to, msg.as_string())
    except Exception as e:
        print(f"Email notify error: {e}")

    # 3 — Badge en CRM (guardar en Supabase tabla notificaciones)
    try:
        pass  # notif disabled
    except Exception as e:
        print(f"Badge notify error: {e}")


@app.post("/ds160/save-full", dependencies=[Depends(chk)])
async def ds160_save_full_v3(body: dict):
    body = {k:(v if v not in ['', 'null', None] else None) for k,v in body.items()}
    try:
        # Soportar tanto campos qXXX como legacy
        email    = body.get("q36_email") or body.get("email","")
        nombre   = str(body.get("q2_nombre") or body.get("nombre","")).upper()
        apellido = str(body.get("q1_apellido") or body.get("apellido_primario","")).upper()
        pas      = str(body.get("q43_numpas") or body.get("numero_pasaporte","")).upper()
        whatsapp = str(body.get("q33_tel") or body.get("whatsapp") or body.get("telefono_principal",""))
        # Normalizar — guardar email en ambos campos para compatibilidad
        if body.get("q36_email") and not body.get("email"):
            body["email"] = body["q36_email"]
        if body.get("email") and not body.get("q36_email"):
            body["q36_email"] = body["email"]
        existing = sb().schema("crm").table("ds160_casos").select("id").eq("datos->>email", email).order("created_at", desc=True).limit(1).execute()

        if existing.data:
            caso_id = existing.data[0]["id"]
            sb().schema("crm").table("ds160_casos").update({
                "datos": body,
                "estado": "revision",
                "updated_at": datetime.now().isoformat()
            }).eq("id", caso_id).execute()
            action = "updated"
        else:
            r = sb().schema("crm").table("ds160_casos").insert({
                "datos": body,
                "estado": "revision",
                "created_at": datetime.now().isoformat()
            }).execute()
            caso_id = r.data[0]["id"] if r.data else None
            action = "created"

        try:
            notify_ds160(nombre=nombre, apellido=apellido, email=email, pasaporte=pas, caso_id=str(caso_id), whatsapp=str(body.get("whatsapp") or body.get("telefono") or body.get("q33_tel") or ""))
        except: pass

        return {"ok": True, "caso_id": caso_id, "action": action}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════
# MÓDULO EVALUACIÓN MIGRATORIA B1/B2
# ══════════════════════════════════════════════

@app.post("/evaluacion/save", dependencies=[Depends(chk)])
async def evaluacion_save(body: dict):
    """Guarda evaluación migratoria y dispara IA scoring"""
    try:
        email    = body.get("email","") or body.get("correo","")
        nombre   = str(body.get("nombre","") or body.get("q2_nombre","")).upper()
        apellido = str(body.get("apellido","") or body.get("q1_apellido","")).upper()

        # Verificar si ya existe por email
        existing = sb().schema("crm").table("evaluaciones_b1b2").select("id").eq("datos->>email", email).order("created_at", desc=True).limit(1).execute()

        if existing.data:
            caso_id = existing.data[0]["id"]
            sb().schema("crm").table("evaluaciones_b1b2").update({
                "datos": body,
                "estado": "pendiente",
                "updated_at": datetime.now().isoformat()
            }).eq("id", caso_id).execute()
            action = "updated"
        else:
            r = sb().schema("crm").table("evaluaciones_b1b2").insert({
                "datos": body,
                "estado": "pendiente",
                "created_at": datetime.now().isoformat()
            }).execute()
            caso_id = r.data[0]["id"] if r.data else None
            action = "created"

        # Notificación
        try:
            send_notification_email("evaluacion_rrss" if str(body.get("fuente","")).lower()=="rrss" else "evaluacion", {
                "nombre": body.get("nombre",""),
                "apellido": body.get("apellido",""),
                "email": body.get("email",""),
                "whatsapp": body.get("whatsapp",""),
                "telefono": body.get("whatsapp",""),
                "caso_id": str(caso_id),
                "tipo_plan": body.get("tipo_plan",""),
                "motivo_viaje": body.get("motivo_viaje",""),
                "estado_civil": body.get("estado_civil",""),
                "salario_mensual": body.get("salario_mensual",""),
                "observaciones": body.get("observaciones","")
            })
        except Exception as e:
            print(f"Evaluacion notify error: {e}")

        return {"ok": True, "caso_id": caso_id, "action": action}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/evaluacion/all", dependencies=[Depends(chk)])
async def evaluacion_list(q: str = "", status: str = "", limit: int = 200):
    try:
        query = sb().schema("crm").table("evaluaciones_b1b2").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("estado", status)
        rows = query.execute().data or []
        for row in rows:
            d = row.get("datos") or {}
            row["_nombre"]   = d.get("nombre","")
            row["_apellido"] = d.get("apellido","")
            row["_email"]    = d.get("email","")
            row["_score"]    = row.get("score_ia", 0)
            row["_decision"] = row.get("decision_ia","PENDIENTE")
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in (r["_nombre"]+r["_apellido"]+r["_email"]).lower()]
        return {"ok": True, "total": len(rows), "casos": rows, "records": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/evaluacion/{eval_id}", dependencies=[Depends(chk)])
async def evaluacion_get(eval_id: str):
    try:
        r = sb().schema("crm").table("evaluaciones_b1b2").select("*").eq("id", eval_id).execute()
        if not r.data: raise HTTPException(404, "No encontrado")
        return r.data[0]
    except HTTPException: raise
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/evaluacion/ia/{eval_id}", dependencies=[Depends(chk)])
async def evaluacion_ia(eval_id: str):
    """Genera análisis IA del perfil migratorio"""
    try:
        r = sb().schema("crm").table("evaluaciones_b1b2").select("*").eq("id", eval_id).execute()
        if not r.data: return {"ok": False, "error": "No encontrado"}
        datos = r.data[0].get("datos", {})

        # Construir prompt para Claude
        ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
        if not ANTHROPIC_KEY:
            return {"ok": False, "error": "ANTHROPIC_API_KEY no configurado"}

        perfil = f"""
PERFIL DEL SOLICITANTE:
Nombre: {datos.get('nombre','')} {datos.get('apellido','')}
Edad: {datos.get('edad','')} años
Estado civil: {datos.get('estado_civil','')}
Hijos: {datos.get('hijos','0')}
Ciudad: {datos.get('ciudad','')}

ARRAIGO ECONÓMICO:
Situación laboral: {datos.get('empleo_tipo','')} | Tipo: {datos.get('tipo_empleo','')}
Funciones: {datos.get('funciones','')}
Salario: RD${datos.get('salario_mensual','')}
Empresa propia: {datos.get('empresa_propia','')}
Salario mensual: RD${datos.get('salario_mensual','')}
Empresa propia: {datos.get('empresa_propia','')}
Propiedades: {datos.get('propiedades','')}
Vehículo: {datos.get('vehiculo','')}
Cuenta bancaria: {datos.get('cuenta_bancaria','')}

ARRAIGO FAMILIAR:
Pareja en RD: {datos.get('pareja_en_rd','')}
Hijos menores a cargo: {datos.get('hijos_cargo','')}
Familia en EE.UU.: {datos.get('familia_eeuu','')}
Estatus familiar EE.UU.: {datos.get('familia_eeuu_estatus','')}

HISTORIAL MIGRATORIO:
Viajes previos: {datos.get('viajes_previos','')}
Países visitados: {datos.get('paises_visitados','')}
Visa negada antes: {datos.get('visa_negada','')}
Razón negación: {datos.get('razon_negacion','')}
Ha estado en EE.UU.: {datos.get('estuvo_eeuu','')}
Overstay: {datos.get('overstay','')}

PROPÓSITO DEL VIAJE:
Tipo: {datos.get('tipo_viaje','')}
Destino: {datos.get('destino_eeuu','')}
Duración: {datos.get('duracion_viaje','')} días
Quién paga: {datos.get('quien_paga','')}
Presupuesto: ${datos.get('presupuesto','')} USD

DOCUMENTOS DISPONIBLES:
{datos.get('documentos_disponibles','')}
"""

        # Llamar a Claude API
        import urllib.request as ur, json as jj
        payload = jj.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 3000,
            "system": """Eres un Oficial Consular Senior simulado + Analista Migratorio experto en visas B1/B2 (INA §214(b)). Evalúas perfiles con criterios reales de la Embajada de EE.UU. en Santo Domingo. Responde SOLO en JSON válido con esta estructura exacta:
{
  "score_economico": 75,
  "score_familiar": 80,
  "score_migratorio": 60,
  "score_proposito": 70,
  "score_total": 71,
  "probabilidad_aprobacion": "65-75%",
  "decision": "APLICAR",
  "red_flags": ["descripción del riesgo 1", "descripción del riesgo 2"],
  "fortalezas": ["fortaleza 1", "fortaleza 2"],
  "narrativa_central": "Texto de 30-45 segundos para la entrevista",
  "documentos_prioritarios": ["doc 1", "doc 2"],
  "recomendaciones": ["acción 1", "acción 2"],
  "respuestas_modelo": {
    "purpose_of_travel": "respuesta en inglés",
    "job_duties": "respuesta en inglés",
    "ties_to_home": "respuesta en inglés"
  },
  "plan_accion": ["paso 1", "paso 2", "paso 3"]
}
Decision debe ser: APLICAR, MEJORAR, o NO_APLICAR""",
            "messages": [{"role": "user", "content": f"Evalúa este perfil:\n{perfil}"}]
        }).encode()

        req = ur.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01"
            }
        )
        resp = ur.urlopen(req, timeout=60)
        result = jj.loads(resp.read())
        ia_text = result["content"][0]["text"]
        # Limpiar markdown si viene con ```json
        ia_text = ia_text.replace("```json","").replace("```","").strip()
        ia_data = jj.loads(ia_text)

        # Guardar resultado en Supabase
        sb().schema("crm").table("evaluaciones_b1b2").update({
            "resultado_ia": ia_data,
            "score_ia": ia_data.get("score_total", 0),
            "decision_ia": ia_data.get("decision","PENDIENTE"),
            "estado": "evaluado",
            "updated_at": datetime.now().isoformat()
        }).eq("id", eval_id).execute()

        return {"ok": True, "resultado": ia_data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.delete("/evaluacion/{eval_id}", dependencies=[Depends(chk)])
async def evaluacion_delete(eval_id: str):
    try:
        sb().schema("crm").table("evaluaciones_b1b2").delete().eq("id", eval_id).execute()
        return {"ok": True, "deleted": eval_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════
# MÓDULO GLOBAL ENTRY
# ══════════════════════════════════════════════

@app.post("/globalentry/save", dependencies=[Depends(chk)])
async def globalentry_save(body: dict):
    try:
        email    = body.get("email","")
        nombre   = str(body.get("f_nombre","")).upper()
        apellido = str(body.get("f_apellido1","")).upper()
        existing = sb().schema("crm").table("globalentry_solicitudes").select("id").eq("datos->>email", email).order("created_at", desc=True).limit(1).execute()
        if existing.data:
            caso_id = existing.data[0]["id"]
            sb().schema("crm").table("globalentry_solicitudes").update({
                "datos": body, "estado": "recibido",
                "updated_at": datetime.now().isoformat()
            }).eq("id", caso_id).execute()
            action = "updated"
        else:
            r = sb().schema("crm").table("globalentry_solicitudes").insert({
                "datos": body, "estado": "recibido",
                "created_at": datetime.now().isoformat()
            }).execute()
            caso_id = r.data[0]["id"] if r.data else None
            action = "created"
        try:
            notify_ds160(nombre=nombre, apellido=apellido, email=email, pasaporte=body.get("pasaporte",""), caso_id=str(caso_id))
        except: pass
        try:
            send_notification_email("globalentry", {
                "nombre": body.get("nombre") or body.get("f_nombre",""),
                "apellido": body.get("apellido") or body.get("f_apellido1",""),
                "email": body.get("email",""),
                "whatsapp": body.get("telefono") or body.get("whatsapp",""),
                "telefono": body.get("telefono") or body.get("whatsapp",""),
                "caso_id": str(caso_id)
            })
        except Exception as e:
            print(f"GlobalEntry notify error: {e}")
        return {"ok": True, "caso_id": caso_id, "action": action}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/globalentry/all", dependencies=[Depends(chk)])
async def globalentry_list(limit: int = 200):
    try:
        rows = sb().schema("crm").table("globalentry_solicitudes").select("*").order("created_at", desc=True).limit(limit).execute().data or []
        for row in rows:
            d = row.get("datos") or {}
            row["_nombre"]   = d.get("f_nombre","")
            row["_apellido"] = d.get("f_apellido1","")
            row["_email"]    = d.get("email","")
        return {"ok": True, "total": len(rows), "casos": rows, "records": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════
# TOKEN / LINK ÚNICO POR CLIENTE
# ══════════════════════════════════════════════
import secrets
try:
    import requests
except: requests=None

@app.post("/ds160/generar-link", dependencies=[Depends(chk)])
async def generar_link_cliente(body: dict):
    """Genera link único para que el cliente llene su DS-160"""
    try:
        nombre   = body.get("nombre","")
        apellido = body.get("apellido","")
        email    = body.get("email","")
        tel      = body.get("tel","")
        if not email:
            return {"ok": False, "error": "Email requerido"}

        token = secrets.token_urlsafe(16)
        # Guardar token en Supabase
        r = sb().schema("crm").table("ds160_casos").insert({
            "datos": {
                "nombre": nombre.upper(),
                "q2_nombre": nombre.upper(),
                "q1_apellido": apellido.upper(),
                "email": email,
                "q33_tel": tel,
                "_token": token,
                "_generado": datetime.now().isoformat()
            },
            "estado": "borrador",
            "created_at": datetime.now().isoformat()
        }).execute()

        caso_id = r.data[0]["id"] if r.data else None
        link = f"https://crm.tengovisard.com/ds160/?token={token}&caso={caso_id}"

        return {
            "ok": True,
            "token": token,
            "caso_id": caso_id,
            "link": link,
            "whatsapp": f"https://wa.me/{tel.replace('+','').replace(' ','')}?text={requests.utils.quote(f'Hola {nombre}, aquí está tu link para llenar el DS-160: {link}') if tel else ''}"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ds160/token/{token}")
async def get_ds160_by_token(token: str):
    """Obtiene datos pre-llenados por token"""
    try:
        r = sb().schema("crm").table("ds160_casos").select("id,datos").eq("datos->>'_token'", token).limit(1).execute()
        if not r.data:
            return {"ok": False, "error": "Token inválido o expirado"}
        d = r.data[0]["datos"]
        return {
            "ok": True,
            "caso_id": r.data[0]["id"],
            "nombre": d.get("nombre",""),
            "apellido": d.get("q1_apellido",""),
            "email": d.get("email",""),
            "tel": d.get("q33_tel","")
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ══ ALIAS OTP — para Global Entry y cualquier formulario ══
@app.post("/otp/request")
async def otp_request_alias(body: dict):
    """Alias de /evaluacion/send-otp para compatibilidad"""
    from fastapi import Request
    class R: pass
    req = OTPReq(
        nombre=body.get("nombre",""),
        apellido=body.get("apellido",""),
        whatsapp=body.get("whatsapp",""),
        email=body.get("email","")
    )
    return await send_otp(req)

@app.post("/otp/verify")
async def otp_verify_alias(body: dict):
    """Alias de /evaluacion/verify-otp para compatibilidad"""
    req = OTPVer(
        email=body.get("email",""),
        otp=body.get("otp","")
    )
    return verify_otp(req)


@app.post("/pdf/extract", dependencies=[Depends(chk)])
async def pdf_extract(body: dict):
    """Extrae campos DS-160 de un PDF usando Claude IA"""
    try:
        import base64, urllib.request, json as jmod
        
        b64 = body.get("pdf_b64","")
        if not b64:
            return {"ok": False, "error": "PDF requerido"}
        
        # Llamar a Claude API para extraer datos del PDF
        CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY","")
        if not CLAUDE_KEY:
            return {"ok": False, "error": "API key de Claude no configurada"}
        
        payload = {
            "model": "claude-opus-4-5",
            "max_tokens": 4000,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": b64}
                    },
                    {
                        "type": "text",
                        "text": """Extrae TODOS los datos de este formulario DS-160 / evaluación migratoria.
Devuelve SOLO un JSON con los campos en este formato exacto (sin texto extra, sin markdown):
{
  "nombre": "", "apellido_primario": "", "q2_nombre": "", "q1_apellido": "",
  "email": "", "telefono_principal": "", "q33_tel": "",
  "fecha_nacimiento": "YYYY-MM-DD", "q9_dob": "YYYY-MM-DD",
  "sexo": "M o F", "q7_sexo": "M o F",
  "estado_civil": "", "q8_civil": "",
  "numero_id_tributario": "", "q20_cedula": "",
  "pais_nacimiento": "", "q12_pais_nac": "",
  "ciudad_nacimiento": "", "q10_ciudad_nac": "",
  "pais_nacionalidad": "", "q13_nacionalidad": "",
  "direccion_rd": "", "q23_dir1": "",
  "ciudad_rd": "", "q25_ciudad": "",
  "provincia_rd": "", "q26_provincia": "",
  "numero_pasaporte": "", "q43_numpas": "",
  "tipo_pasaporte": "", "q42_tipo_pas": "",
  "pais_emisor_pasaporte": "", "q45_pais_pas": "",
  "fecha_emision_pasaporte": "YYYY-MM-DD", "q48_emision": "YYYY-MM-DD",
  "fecha_vencimiento_pasaporte": "YYYY-MM-DD", "q49_vence": "YYYY-MM-DD",
  "proposito_viaje": "B-2", "q55_proposito": "B-2",
  "direccion_eeuu": "", "q65_dir_hospedaje": "",
  "ciudad_eeuu": "", "q66_ciudad_hosp": "",
  "nombre_contacto_eeuu": "", "q98_cont_ap": "",
  "relacion_contacto_eeuu": "", "q101_cont_rel": "",
  "nombre_padre": "", "q108_padre_ap": "",
  "nombre_madre": "", "q113_madre_ap": "",
  "ocupacion_actual": "", "q131_ocupacion": "",
  "empresa_actual": "", "q132_empresa": "",
  "fuente": "pdf_import"
}
Solo incluye campos que tengan valor real en el documento. No inventes datos."""
                    }
                ]
            }]
        }
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=jmod.dumps(payload).encode(),
            headers={
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = jmod.loads(resp.read())
        
        text = result["content"][0]["text"].strip()
        # Limpiar markdown si viene
        text = text.replace("```json","").replace("```","").strip()
        datos = jmod.loads(text)
        
        # Limpiar campos vacíos
        datos = {k:v for k,v in datos.items() if v and str(v).strip() and str(v) not in ["null","None",""]}
        
        return {"ok": True, "datos": datos, "campos": len(datos)}
        
    except Exception as e:
        return {"ok": False, "error": str(e), "datos": {}}

@app.post("/ds160/crear", dependencies=[Depends(chk)])
async def ds160_crear(body: dict):
    """Crear caso DS-160 desde datos extraídos"""
    try:
        import uuid
        datos = body.get("datos", {})
        estado = body.get("estado", "revision")
        caso_id = str(uuid.uuid4())
        r = sb().schema("crm").table("ds160_casos").insert({
            "id": caso_id,
            "estado": estado,
            "datos": datos
        }).execute()
        if r.data:
            return {"ok": True, "id": caso_id}
        return {"ok": False, "error": "No se pudo crear"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ds160/analizar/{caso_id}", dependencies=[Depends(chk)])
async def ds160_analizar(caso_id: str):
    """Análisis estratégico DS-160 para presentación consular"""
    try:
        r = sb().schema("crm").table("ds160_casos").select("*").eq("id", caso_id).execute()
        if not r.data:
            return {"ok": False, "error": "No encontrado"}
        
        caso = r.data[0]
        datos = caso.get("datos", {})
        
        nombre = f"{datos.get('q2_nombre') or datos.get('nombre','')} {datos.get('q1_apellido') or datos.get('apellido_primario','')}".strip()
        
        prompt = f"""Eres un ex-oficial consular del Departamento de Estado de EE.UU. con 20 años de experiencia evaluando visas B1/B2 para ciudadanos dominicanos. Analiza este perfil y dame una estrategia CONCRETA para maximizar las probabilidades de aprobación.

PERFIL DEL SOLICITANTE:
- Nombre: {nombre}
- Fecha nacimiento: {datos.get('q9_dob') or datos.get('fecha_nacimiento','')}
- Estado civil: {datos.get('q8_civil') or datos.get('estado_civil','')}
- Ocupación: {datos.get('q131_ocupacion') or datos.get('ocupacion_actual','')}
- Empresa: {datos.get('q132_empresa') or datos.get('empresa_actual','')}
- Salario: {datos.get('salario','')}
- Propósito viaje: {datos.get('q55_proposito') or datos.get('proposito_viaje','')}
- Ciudad destino: {datos.get('q66_ciudad_hosp') or datos.get('ciudad_eeuu','')}
- Duración estadía: {datos.get('q64_duracion') or datos.get('duracion_estancia','')}
- Familiares en EEUU: {datos.get('q118_fam_inm','')}
- Visa anterior: {datos.get('q87_visa_prev','')}
- Viajes anteriores: {datos.get('q82_estuvo','')}
- Padre en EEUU: {datos.get('q111_padre_eeuu','')}
- Madre en EEUU: {datos.get('q116_madre_eeuu','')}
- Bienes: {datos.get('bienes','')}
- Pagador viaje: {datos.get('pagador_viaje','')}
- Monto viaje: {datos.get('monto_viaje','')}

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin markdown, sin explicaciones. Usa esta estructura exacta:
{
  "score_total": [0-100],
  "score_economico": [0-100],
  "score_familiar": [0-100],
  "score_migratorio": [0-100],
  "score_proposito": [0-100],
  "decision": "APROBAR|RIESGO_MEDIO|NO_APLICAR",
  "probabilidad_aprobacion": "X%-Y%",
  "narrativa_central": "2-3 oraciones describiendo el perfil y estrategia principal",
  "fortalezas": ["punto 1","punto 2","punto 3"],
  "red_flags": ["riesgo 1","riesgo 2"],
  "recomendaciones": ["accion 1","accion 2","accion 3"],
  "plan_accion": ["paso 1","paso 2","paso 3"],
  "documentos_prioritarios": ["doc 1","doc 2","doc 3"],
  "respuestas_modelo": {
    "purpose_of_travel": "respuesta exacta en inglés para el cónsul",
    "ties_to_home": "respuesta exacta en inglés para el cónsul",
    "job_duties": "respuesta exacta en inglés para el cónsul"
  }
}"""

        import urllib.request, json as jmod, os
        
        CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY","")
        if not CLAUDE_KEY:
            return {"ok": False, "error": "ANTHROPIC_API_KEY no configurada"}
        
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=jmod.dumps(payload).encode(),
            headers={
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = jmod.loads(resp.read())
        
        texto = result["content"][0]["text"]
        
        return {
            "ok": True,
            "resultado": texto,
            "nombre": nombre,
            "caso_id": caso_id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ds160/ceac-json/{caso_id}", dependencies=[Depends(chk)])
async def ds160_ceac_json(caso_id: str):
    """Exporta JSON optimizado para CEAC/DS-160 oficial"""
    r = sb().schema("crm").table("ds160_casos").select("*").eq("id", caso_id).execute()
    if not r.data: return {"ok": False, "error": "No encontrado"}
    d = r.data[0].get("datos", {})
    def g(*keys):
        for k in keys:
            v = d.get(k)
            if v and str(v).strip() and str(v).lower() not in ['null','none','']:
                return str(v).strip().upper()
        return ""
    ceac = {
        "personal": {
            "surname": g("q1_apellido","apellido_primario"),
            "given_name": g("q2_nombre","nombre"),
            "other_names": g("q3_otros_nombres"),
            "sex": g("q7_sexo","sexo"),
            "marital_status": g("q8_civil","estado_civil"),
            "dob": g("q9_dob","fecha_nacimiento"),
            "city_of_birth": g("q10_ciudad_nac","ciudad_nacimiento"),
            "country_of_birth": g("q12_pais_nac","pais_nacimiento"),
            "nationality": g("q13_nacionalidad","pais_nacionalidad"),
            "national_id": g("q20_cedula","numero_id_tributario"),
        },
        "address": {
            "line1": g("q23_dir1","direccion_rd"),
            "city": g("q25_ciudad","ciudad_rd"),
            "province": g("q26_provincia","provincia_rd"),
            "country": g("q28_pais_res"),
            "phone": g("q33_tel","telefono_principal"),
            "email": d.get("email","").lower().strip(),
        },
        "passport": {
            "type": g("q42_tipo_pas","tipo_pasaporte"),
            "number": g("q43_numpas","numero_pasaporte"),
            "country_issued": g("q45_pais_pas","pais_emisor_pasaporte"),
            "city_issued": g("q46_ciudad_emision"),
            "date_issued": g("q48_emision","fecha_emision_pasaporte"),
            "date_expires": g("q49_vence","fecha_vencimiento_pasaporte"),
            "lost_passport": g("q50_perdio_pas"),
        },
        "travel": {
            "purpose": g("q55_proposito","proposito_viaje"),
            "intended_arrival": g("q57_llegada","fecha_llegada_prevista"),
            "stay_duration": g("q64_duracion","duracion_estancia"),
            "address_in_us": g("q65_dir_hospedaje","direccion_eeuu"),
            "city_in_us": g("q66_ciudad_hosp","ciudad_eeuu"),
            "state_in_us": g("q67_estado_hosp","estado_eeuu"),
            "who_pays": g("q68_paga"),
            "prev_us_visit": g("q82_estuvo"),
            "prev_visa": g("q87_visa_prev"),
            "visa_refused": g("q93_negacion"),
        },
        "us_contact": {
            "surname": g("q98_cont_ap"),
            "given_name": g("q99_cont_nom"),
            "organization": g("q100_cont_org"),
            "relationship": g("q101_cont_rel"),
            "address": g("q102_cont_dir","direccion_contacto_eeuu"),
            "city": g("q103_cont_ciudad"),
            "state": g("q104_cont_estado"),
            "zip": g("q105_cont_zip"),
            "phone": g("q106_cont_tel","telefono_contacto_eeuu"),
            "email": d.get("q107_cont_email",""),
        },
        "family": {
            "father_surname": g("q108_padre_ap","apellido_padre"),
            "father_given": g("q109_padre_nom","nombre_padre"),
            "father_dob": g("q110_padre_dob","fecha_nacimiento_padre"),
            "father_in_us": g("q111_padre_eeuu"),
            "mother_surname": g("q113_madre_ap","apellido_madre"),
            "mother_given": g("q114_madre_nom","nombre_madre"),
            "mother_dob": g("q115_madre_dob","fecha_nacimiento_madre"),
            "mother_in_us": g("q116_madre_eeuu"),
            "spouse_surname": g("q125_con_ap","apellido_conyuge"),
            "spouse_given": g("q126_con_nom","nombre_conyuge"),
            "spouse_dob": g("q127_con_dob","fecha_nacimiento_conyuge"),
        },
        "work": {
            "occupation": g("q131_ocupacion","ocupacion_actual"),
            "employer": g("q132_empleador","empresa_actual","q132_empresa"),
            "employer_address": g("q133_dir_emp1","direccion_trabajo"),
            "employer_city": g("q134_emp_ciudad","ciudad_empleador"),
            "employer_province": g("q135_emp_prov"),
            "employer_phone": g("q138_emp_tel","q35_tel_trab"),
            "start_date": g("q139_emp_inicio","fecha_inicio_trabajo"),
            "monthly_salary": g("q140_salario","salario","salario_mensual"),
            "duties": g("q141_funciones","cargo_actual"),
        },
        "security": {
            "q174": g("q174"), "q175": g("q175"), "q176": g("q176"),
            "q177": g("q177"), "q179": g("q179"), "q181": g("q181"),
            "q183": g("q183"), "q185": g("q185"), "q187": g("q187"),
            "q195_overstay": g("q195","q195_overstay"),
            "q196_fraud": g("q196","q196_fraude"),
            "q199": g("q199"), "q201": g("q201"),
            "q204_illegal_custody": g("q204"),
            "q206_illegal_vote": g("q206"),
            "q222_prepared_by_other": g("q222","q222_asistido"),
        },
        "_meta": {
            "caso_id": caso_id,
            "nombre_completo": g("q2_nombre","nombre") + " " + g("q1_apellido","apellido_primario"),
            "email": d.get("email",""),
            "generated": datetime.now().isoformat(),
            "source": "TengoVisaRD CRM",
            "embassy": "Santo Domingo, Dominican Republic",
        }
    }
    # Calcular completitud
    total = sum(len(v) if isinstance(v,dict) else 1 for k,v in ceac.items() if k!='_meta')
    filled = sum(1 for sec in ceac.values() if isinstance(sec,dict) for v in sec.values() if v and v.strip())
    ceac["_meta"]["completeness"] = f"{round(filled/max(total,1)*100)}%"
    return {"ok": True, "ceac": ceac, "caso_id": caso_id}
