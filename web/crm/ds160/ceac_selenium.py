#!/usr/bin/env python3
"""
ceac_selenium.py — Automatización DS-160 completo en CEAC
TengoVisaRD CRM — v2.0

Uso:
  python3 ceac_selenium.py <archivo.json>
  python3 ceac_selenium.py <archivo.json> --visible
  python3 ceac_selenium.py <archivo.json> --reanudar <APP_ID>

Cubre todas las páginas del DS-160 en CEAC automáticamente.
El script NO firma ni hace SUBMIT final — eso lo hace el solicitante.
"""

import sys, json, os, time, argparse, logging
from datetime import datetime

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/ceac_selenium.log')
    ]
)
log = logging.getLogger('CEAC')

# ── Args ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('json_file')
parser.add_argument('--visible', action='store_true', help='Mostrar navegador')
parser.add_argument('--reanudar', default=None, help='App ID para reanudar')
parser.add_argument('--desde', type=int, default=1, help='Desde qué página empezar')
args = parser.parse_args()

# ── Cargar JSON ───────────────────────────────────────────────────────────────
if not os.path.exists(args.json_file):
    log.error(f"Archivo no encontrado: {args.json_file}"); sys.exit(1)

with open(args.json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

meta = data.get('meta', {})
F    = data.get('fields', {})

log.info(f"Cliente  : {meta.get('nombre','')} {meta.get('apellido','')}")
log.info(f"Pasaporte: {meta.get('pasaporte','')}")
log.info(f"Completud: {meta.get('completeness_pct','?')}%")

# ── Helpers de datos ──────────────────────────────────────────────────────────
def g(key, default=''):
    v = F.get(key, default)
    if v is None: return default
    s = str(v).strip()
    return s if s and s not in ['None','null','nan'] else default

def yn(key):
    return g(key,'NO').upper() in ['YES','SI','SÍ','TRUE','1']

def gdate(key):
    """Retorna (dia, mes_abr, año) para campos de fecha CEAC"""
    v = g(key)
    if not v: return '', '', ''
    try:
        d = datetime.strptime(v[:10], '%Y-%m-%d')
        M = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',
             7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
        return str(d.day), M[d.month], str(d.year)
    except:
        return '', '', ''

def gdate_short(key):
    """Retorna (dia, mes_abr_3, año) - formato corto para algunos campos"""
    v = g(key)
    if not v: return '', '', ''
    try:
        d = datetime.strptime(v[:10], '%Y-%m-%d')
        M = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
             7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
        return str(d.day), M[d.month], str(d.year)
    except:
        return '', '', ''

# ── Selenium setup ────────────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException,
        ElementNotInteractableException, StaleElementReferenceException
    )
except ImportError:
    log.error("Instala: pip install selenium"); sys.exit(1)

opts = Options()
if not args.visible:
    opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=1280,900')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_experimental_option('excludeSwitches', ['enable-automation'])
opts.add_experimental_option('useAutomationExtension', False)
opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

DRIVERS = ['/usr/bin/chromedriver','/usr/local/bin/chromedriver',
           '/snap/bin/chromium.chromedriver']
driver_path = next((p for p in DRIVERS if os.path.exists(p)), None)

if driver_path:
    svc = Service(driver_path)
    drv = webdriver.Chrome(service=svc, options=opts)
else:
    drv = webdriver.Chrome(options=opts)

drv.implicitly_wait(3)
W = WebDriverWait(drv, 12)

# ── Funciones de interacción ─────────────────────────────────────────────────
def wait_el(el_id, timeout=12):
    return WebDriverWait(drv, timeout).until(
        EC.presence_of_element_located((By.ID, el_id))
    )

def wait_click(el_id, timeout=12):
    el = WebDriverWait(drv, timeout).until(
        EC.element_to_be_clickable((By.ID, el_id))
    )
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.2)
    drv.execute_script("arguments[0].click();", el)
    return el

def fill(el_id, value, clear=True):
    if not value: return False
    try:
        el = wait_el(el_id)
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        if clear:
            el.clear()
            drv.execute_script("arguments[0].value='';", el)
        el.send_keys(str(value))
        return True
    except Exception as e:
        log.warning(f"fill({el_id}): {e}")
        return False

def sel_dropdown(el_id, value, by_text=False):
    if not value: return False
    try:
        el = wait_el(el_id)
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        s = Select(el)
        if by_text:
            try: s.select_by_visible_text(value)
            except:
                # Buscar opción que contenga el texto
                for opt in s.options:
                    if value.upper() in opt.text.upper():
                        s.select_by_visible_text(opt.text)
                        break
        else:
            try: s.select_by_value(value)
            except:
                try: s.select_by_visible_text(value)
                except: pass
        return True
    except Exception as e:
        log.warning(f"sel_dropdown({el_id}, {value}): {e}")
        return False

def radio(name, yes=True):
    """Selecciona radio YES o NO por nombre"""
    try:
        val = 'Y' if yes else 'N'
        # Intentar múltiples formatos de radio
        for xpath in [
            f'//input[@name="{name}" and @value="{val}"]',
            f'//input[@name="{name}" and @value="{"Yes" if yes else "No"}"]',
            f'//input[@name="{name}" and @value="{"YES" if yes else "NO"}"]',
            f'//input[@name="{name}"][@id[contains(.,"{val}")]]',
        ]:
            try:
                el = drv.find_element(By.XPATH, xpath)
                drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                drv.execute_script("arguments[0].click();", el)
                return True
            except: continue
        # Último recurso: primer/segundo radio
        els = drv.find_elements(By.XPATH, f'//input[@name="{name}"]')
        if els:
            idx = 0 if yes else 1
            if idx < len(els):
                drv.execute_script("arguments[0].click();", els[idx])
                return True
    except Exception as e:
        log.warning(f"radio({name}, {yes}): {e}")
    return False

def radio_yn(name, key, default_no=True):
    """Radio usando clave del JSON"""
    radio(name, yes=yn(key))

def fill_date(day_id, month_id, year_id, key):
    """Llena campos de fecha separados"""
    day, month, year = gdate(key)
    if day: fill(day_id, day)
    if month: sel_dropdown(month_id, month, by_text=True)
    if year: fill(year_id, year)

def fill_date_select(base_id, key):
    """Llena fecha con selectores estándar CEAC"""
    day, month, year = gdate(key)
    if day:   sel_dropdown(f'{base_id}Day', day)
    if month: sel_dropdown(f'{base_id}Month', month, by_text=True)
    if year:  fill(f'{base_id}Year', year)

def next_pg():
    """Click en botón Next de CEAC"""
    next_ids = [
        'ctl00_SiteContentPlaceHolder_FormView1_btnNext',
        'ctl00_SiteContentPlaceHolder_btnNext',
        'btnNext',
    ]
    for bid in next_ids:
        try:
            btn = WebDriverWait(drv, 8).until(
                EC.element_to_be_clickable((By.ID, bid))
            )
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5)
            drv.execute_script("arguments[0].click();", btn)
            time.sleep(3)
            return True
        except: continue
    # Intentar por CSS
    try:
        btn = drv.find_element(By.CSS_SELECTOR,
            'input[value="Next"],input[value="NEXT"],input[value="Continue"]')
        drv.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        return True
    except: pass
    log.error("❌ Botón Next no encontrado")
    drv.save_screenshot('/tmp/ceac_no_next.png')
    return False

def save_id():
    """Guarda el Application ID si aparece"""
    try:
        for sel in ['#ctl00_SiteContentPlaceHolder_ucApplicationID_lblAppID',
                    '.app-id', '[id*="AppID"]', '[id*="ApplicationID"]']:
            try:
                el = drv.find_element(By.CSS_SELECTOR, sel)
                if el.text.strip():
                    with open('/tmp/ceac_app_id.txt','w') as f: f.write(el.text.strip())
                    log.info(f"App ID: {el.text.strip()}")
                    return el.text.strip()
            except: continue
    except: pass
    return None

def screenshot(name):
    drv.save_screenshot(f'/tmp/ceac_{name}.png')

def safe_fill(el_id, value):
    """Fill que no falla si el campo no existe"""
    if not value: return
    try: fill(el_id, value)
    except: pass

def try_add_another(btn_id):
    """Click en Add Another si existe"""
    try:
        btn = drv.find_element(By.ID, btn_id)
        drv.execute_script("arguments[0].click();", btn)
        time.sleep(1)
    except: pass

# ── Prefijo base CEAC ─────────────────────────────────────────────────────────
P = 'ctl00_SiteContentPlaceHolder_FormView1_'

def fid(suffix):
    return P + suffix

# ─────────────────────────────────────────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
try:
    # ── INICIO ───────────────────────────────────────────────────────────────
    log.info("Abriendo CEAC...")
    drv.get('https://ceac.state.gov/genniv/')
    time.sleep(3)
    screenshot('00_inicio')

    if args.reanudar:
        # Reanudar aplicación existente
        log.info(f"Reanudando App ID: {args.reanudar}")
        try:
            wait_click('ctl00_SiteContentPlaceHolder_LinkRetrieve')
            time.sleep(1)
            fill('ctl00_SiteContentPlaceHolder_ucRetrieveApp_tbxAppID', args.reanudar)
            wait_click('ctl00_SiteContentPlaceHolder_ucRetrieveApp_btnContinue')
            time.sleep(3)
        except Exception as e:
            log.error(f"Error reanudando: {e}")
    else:
        # Nueva aplicación
        log.info("Iniciando nueva aplicación...")
        try:
            # Seleccionar ubicación de la embajada
            sel_dropdown('ctl00_SiteContentPlaceHolder_ddlLocation', 'Dominican Republic', by_text=True)
            time.sleep(0.5)
        except: pass

        try:
            wait_click('ctl00_SiteContentPlaceHolder_btnNewApp')
            time.sleep(2)
        except:
            try:
                wait_click('ctl00_SiteContentPlaceHolder_btnNew')
                time.sleep(2)
            except: pass

        # Aceptar términos si aparecen
        try:
            wait_click('ctl00_SiteContentPlaceHolder_chkbxDisclaimer')
            time.sleep(0.5)
            wait_click('ctl00_SiteContentPlaceHolder_btnContinue')
            time.sleep(2)
        except: pass

        save_id()
        screenshot('01_nueva_app')

    # ── P1 — INFORMACIÓN PERSONAL 1 (Q1-Q12) ────────────────────────────────
    log.info("P1 — Información Personal 1...")
    try:
        fill(fid('tbxSurname'), g('q1_apellido'))
        fill(fid('tbxGivenName'), g('q2_nombre'))

        # Otros nombres
        radio_yn('OtherNames', 'q3_otros_nombres')
        if yn('q3_otros_nombres'):
            time.sleep(0.5)
            safe_fill(fid('tbxOtherSurname'), g('q4_otro_apellido'))
            safe_fill(fid('tbxOtherGivenName'), g('q5_otro_nombre'))

        # Nombre en alfabeto nativo
        native = g('q6_nombre_nativo')
        if native:
            try:
                radio('NativeAlphabet', yes=True)
                time.sleep(0.3)
                safe_fill(fid('tbxNativeFullName'), native)
            except:
                safe_fill(fid('tbxNativeFullName'), native)
        else:
            try: radio('NativeAlphabet', yes=False)
            except: pass

        # Sexo
        if g('q7_sexo','').upper() in ['M','MALE','MASCULINO','H']:
            radio('Gender', yes=True)  # Male
        else:
            radio('Gender', yes=False)  # Female

        # Estado civil
        civil_map = {
            'soltero':'S','single':'S',
            'casado':'M','married':'M',
            'union_libre':'C','common_law':'C',
            'divorciado':'D','divorced':'D',
            'viudo':'W','widowed':'W',
            'separado':'L','separated':'L',
        }
        civil_val = civil_map.get(g('q8_civil','').lower(), 'S')
        sel_dropdown(fid('ddlMaritalStatus'), civil_val)

        # Fecha de nacimiento
        day, month, year = gdate('q9_dob')
        if day:   sel_dropdown(fid('ddlDOBDay'), day)
        if month: sel_dropdown(fid('ddlDOBMonth'), month, by_text=True)
        if year:  fill(fid('tbxDOBYear'), year)

        # Ciudad y país de nacimiento
        fill(fid('tbxBirthCity'), g('q10_ciudad_nac'))
        safe_fill(fid('tbxBirthStateProvince'), g('q11_prov_nac', 'Does Not Apply'))
        sel_dropdown(fid('ddlBirthCountry'), 'Dominican Republic', by_text=True)

    except Exception as e:
        log.error(f"Error P1: {e}"); screenshot('p1_error')

    log.info("✓ P1"); next_pg(); save_id(); screenshot('p1_done')

    # ── P2 — INFORMACIÓN PERSONAL 2 (Q13-Q22) ───────────────────────────────
    log.info("P2 — Información Personal 2...")
    try:
        # Nacionalidad
        sel_dropdown(fid('ddlCountryCitizenship'), 'Dominican Republic', by_text=True)

        # Otra nacionalidad
        radio_yn('OtherCitizenship', 'q14_otra_nac')
        if yn('q14_otra_nac'):
            time.sleep(0.5)
            try:
                sel_dropdown(fid('ddlOtherCountryCitizenship'),
                    g('q15_otra_nac_pais'), by_text=True)
                radio_yn('OtherPassport', 'q16_pas_otra_nac')
                if yn('q16_pas_otra_nac'):
                    safe_fill(fid('tbxOtherPassportNum'), g('q17_pas_otro'))
                    day, month, year = gdate('q18_emision_otro')
                    if day:   sel_dropdown(fid('ddlOtherPassportIssueDateDay'), day)
                    if month: sel_dropdown(fid('ddlOtherPassportIssueDateMonth'), month, by_text=True)
                    if year:  fill(fid('tbxOtherPassportIssueDateYear'), year)
                    day, month, year = gdate('q19_vence_otro')
                    if day:   sel_dropdown(fid('ddlOtherPassportExpDateDay'), day)
                    if month: sel_dropdown(fid('ddlOtherPassportExpDateMonth'), month, by_text=True)
                    if year:  fill(fid('tbxOtherPassportExpDateYear'), year)
            except: pass

        # ID Nacional (Cédula)
        cedula = g('q20_cedula')
        if cedula and cedula != 'Does Not Apply':
            radio('NatID', yes=True)
            time.sleep(0.3)
            safe_fill(fid('tbxNatID'), cedula)
        else:
            radio('NatID', yes=False)

        # SSN
        ssn = g('q21_ssn')
        if ssn and ssn not in ['Does Not Apply','DOES NOT APPLY','']:
            radio('USSSNum', yes=True)
            time.sleep(0.3)
            safe_fill(fid('tbxUSSSNum'), ssn)
        else:
            radio('USSSNum', yes=False)

        # TIN
        tin = g('q22_tin')
        if tin and tin not in ['Does Not Apply','DOES NOT APPLY','']:
            radio('USTaxNum', yes=True)
            time.sleep(0.3)
            safe_fill(fid('tbxUSTaxNum'), tin)
        else:
            radio('USTaxNum', yes=False)

    except Exception as e:
        log.error(f"Error P2: {e}"); screenshot('p2_error')

    log.info("✓ P2"); next_pg(); save_id(); screenshot('p2_done')

    # ── P3 — DIRECCIÓN Y TELÉFONO (Q23-Q35) ─────────────────────────────────
    log.info("P3 — Dirección y Teléfono...")
    try:
        fill(fid('tbxHomeAddressLine1'), g('q23_dir1'))
        safe_fill(fid('tbxHomeAddressLine2'), g('q24_dir2', 'Does Not Apply'))
        fill(fid('tbxHomeAddressCity'), g('q25_ciudad'))
        safe_fill(fid('tbxHomeAddressStateProvince'), g('q26_provincia', 'Does Not Apply'))
        safe_fill(fid('tbxHomeAddressPostalZip'), g('q27_postal', 'Does Not Apply'))
        sel_dropdown(fid('ddlHomeAddressCountry'), 'Dominican Republic', by_text=True)

        # Dirección anterior
        radio_yn('MailingAddress', 'q29_dir_ant')
        if yn('q29_dir_ant'):
            time.sleep(0.5)
            safe_fill(fid('tbxMailingAddressLine1'), g('q30_dir_ant'))
            safe_fill(fid('tbxMailingAddressCity'), g('q31_ciudad_ant'))
            try:
                sel_dropdown(fid('ddlMailingAddressCountry'), g('q32_pais_ant'), by_text=True)
            except: pass

        # Teléfonos
        fill(fid('tbxPhoneNumberPrimary'), g('q33_tel'))
        safe_fill(fid('tbxPhoneNumberSecondary'), g('q34_tel2', 'Does Not Apply'))
        safe_fill(fid('tbxPhoneNumberWork'), g('q35_tel_trab', 'Does Not Apply'))

    except Exception as e:
        log.error(f"Error P3: {e}"); screenshot('p3_error')

    log.info("✓ P3"); next_pg(); save_id(); screenshot('p3_done')

    # ── P4 — PASAPORTE (Q42-Q53) ─────────────────────────────────────────────
    log.info("P4 — Pasaporte...")
    try:
        # Tipo de pasaporte
        tipo_map = {
            'regular':'R','ordinary':'R',
            'oficial':'O','official':'O',
            'diplomatico':'D','diplomatic':'D',
            'laissez':'L',
        }
        tipo_val = tipo_map.get(g('q42_tipo_pas','regular').lower(), 'R')
        try:
            sel_dropdown(fid('ddlPassportType'), tipo_val)
        except:
            radio('PassportType', yes=True)  # Regular

        fill(fid('tbxPassportNumber'), g('q43_numpas'))
        safe_fill(fid('tbxPassportBookNumber'), g('q44_libreta', 'Does Not Apply'))
        sel_dropdown(fid('ddlPassportCountry'), 'Dominican Republic', by_text=True)
        safe_fill(fid('tbxPassportIssuanceCity'), g('q46_ciudad_emision'))
        safe_fill(fid('tbxPassportIssuanceStateProvince'), g('q47_prov_emision', 'Does Not Apply'))

        # Fecha expedición
        day, month, year = gdate('q48_emision')
        if day:   sel_dropdown(fid('ddlPassportIssuanceDateDay'), day)
        if month: sel_dropdown(fid('ddlPassportIssuanceDateMonth'), month, by_text=True)
        if year:  fill(fid('tbxPassportIssuanceDateYear'), year)

        # Fecha vencimiento
        day, month, year = gdate('q49_vence')
        if day:   sel_dropdown(fid('ddlPassportExpirationDateDay'), day)
        if month: sel_dropdown(fid('ddlPassportExpirationDateMonth'), month, by_text=True)
        if year:  fill(fid('tbxPassportExpirationDateYear'), year)

        # Pasaporte perdido
        radio_yn('LostPassport', 'q50_perdio_pas')
        if yn('q50_perdio_pas'):
            time.sleep(0.5)
            safe_fill(fid('tbxLostPassportNum'), g('q51_pas_perdido', 'Do Not Know'))
            try:
                sel_dropdown(fid('ddlLostPassportCountry'), g('q52_pais_pas_perdido'), by_text=True)
            except: pass
            safe_fill(fid('tbxLostPassportExpl'), g('q53_explicacion_perdido'))

    except Exception as e:
        log.error(f"Error P4: {e}"); screenshot('p4_error')

    log.info("✓ P4"); next_pg(); save_id(); screenshot('p4_done')

    # ── P5 — CONTACTO (Q36-Q41, email y redes) ───────────────────────────────
    log.info("P5 — Email y Redes Sociales...")
    try:
        fill(fid('tbxEmailAddress'), g('q36_email'))
        fill(fid('tbxEmailAddressConfirm'), g('q36_email'))

        # Redes sociales
        radio_yn('SocialMedia', 'q37_redes')
        if yn('q37_redes'):
            time.sleep(0.5)
            red1 = g('q38_red1')
            user1 = g('q39_user1')
            if red1:
                try:
                    sel_dropdown(fid('ddlSocialMediaType'), red1, by_text=True)
                    safe_fill(fid('tbxSocialMediaIdentifier'), user1)
                except:
                    safe_fill(fid('tbxSocialMediaType'), red1)
                    safe_fill(fid('tbxSocialMediaIdentifier'), user1)

    except Exception as e:
        log.error(f"Error P5: {e}"); screenshot('p5_error')

    log.info("✓ P5"); next_pg(); save_id(); screenshot('p5_done')

    # ── P6 — INFORMACIÓN DEL VIAJE (Q54-Q68) ─────────────────────────────────
    log.info("P6 — Información del Viaje...")
    try:
        # Propósito del viaje
        prop_map = {
            'b1/b2':'B','b-1/b-2':'B','turismo':'B','tourism':'B','business':'B',
            'f':'F','student':'F','estudiante':'F',
            'j':'J','exchange':'J','intercambio':'J',
            'h':'H','work':'H','trabajo':'H',
        }
        prop_val = prop_map.get(g('q55_proposito','').lower(), 'B')
        try:
            sel_dropdown(fid('ddlTripPurpose'), prop_val)
        except:
            safe_fill(fid('tbxTripPurpose'), g('q55_proposito', 'Temporary Visitor for Pleasure'))

        # Planes específicos
        radio_yn('SpecificTravel', 'q56_planes')
        if yn('q56_planes'):
            time.sleep(0.5)
            day, month, year = gdate('q57_llegada')
            if day:   sel_dropdown(fid('ddlArrivalDateDay'), day)
            if month: sel_dropdown(fid('ddlArrivalDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxArrivalDateYear'), year)
            safe_fill(fid('tbxArrivalFlight'), g('q58_vuelo_lleg', 'Does Not Apply'))
            safe_fill(fid('tbxArrivalCity'), g('q59_ciudad_lleg', 'Does Not Apply'))
            day, month, year = gdate('q60_salida')
            if day:   sel_dropdown(fid('ddlDepartureDateDay'), day)
            if month: sel_dropdown(fid('ddlDepartureDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxDepartureDateYear'), year)
            safe_fill(fid('tbxDepartureFlight'), g('q61_vuelo_sal', 'Does Not Apply'))
            safe_fill(fid('tbxDepartureCity'), g('q62_ciudad_sal', 'Does Not Apply'))
        else:
            # Fecha estimada
            day, month, year = gdate('q63_llegada_est')
            if day:   sel_dropdown(fid('ddlArrivalDateDay'), day)
            if month: sel_dropdown(fid('ddlArrivalDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxArrivalDateYear'), year)

        # Duración estadía
        fill(fid('tbxTripLength'), g('q64_duracion', '7 Days'))

        # Dirección hospedaje
        fill(fid('tbxStreetAddress1'), g('q65_dir_hospedaje'))
        fill(fid('tbxCity'), g('q66_ciudad_hosp'))
        sel_dropdown(fid('ddlState'), g('q67_estado_hosp'), by_text=True)

        # Quién paga
        paga_map = {
            'si':'S','self':'S','yo':'S','propio':'S','myself':'S',
            'no':'O','otro':'O','other':'O','empresa':'O','company':'O',
        }
        paga_val = paga_map.get(g('q68_paga','').lower(), 'S')
        try:
            sel_dropdown(fid('ddlPayerType'), paga_val)
        except:
            radio('TripPayer', yes=(paga_val=='S'))

        if paga_val != 'S':
            time.sleep(0.5)
            safe_fill(fid('tbxPayerSurname'), g('q69_pat_apellido'))
            safe_fill(fid('tbxPayerGivenName'), g('q70_pat_nombre'))
            safe_fill(fid('tbxPayerPhone'), g('q71_pat_tel'))
            safe_fill(fid('tbxPayerEmail'), g('q72_pat_email'))
            safe_fill(fid('tbxPayerRelationship'), g('q73_pat_relacion'))

    except Exception as e:
        log.error(f"Error P6: {e}"); screenshot('p6_error')

    log.info("✓ P6"); next_pg(); save_id(); screenshot('p6_done')

    # ── P7 — COMPAÑEROS DE VIAJE (Q76-Q81) ───────────────────────────────────
    log.info("P7 — Compañeros de Viaje...")
    try:
        radio_yn('OtherPersonsTraveling', 'q76_compan')
        if yn('q76_compan'):
            time.sleep(0.5)
            radio_yn('Group', 'q77_grupo')
            if yn('q77_grupo'):
                safe_fill(fid('tbxGroupName'), g('q78_grupo_nom'))
            else:
                safe_fill(fid('tbxOtherTravelerSurname_0'), g('q79_comp1_ap'))
                safe_fill(fid('tbxOtherTravelerGivenName_0'), g('q80_comp1_nom'))
                safe_fill(fid('tbxOtherTravelerRelationship_0'), g('q81_comp1_rel'))

    except Exception as e:
        log.error(f"Error P7: {e}"); screenshot('p7_error')

    log.info("✓ P7"); next_pg(); save_id(); screenshot('p7_done')

    # ── P8 — VIAJES PREVIOS A EE.UU. (Q82-Q97) ───────────────────────────────
    log.info("P8 — Viajes Previos a EE.UU....")
    try:
        radio_yn('PreviouslyInUS', 'q82_estuvo')
        if yn('q82_estuvo'):
            time.sleep(0.5)
            day, month, year = gdate('q83_fecha_vis1')
            if day:   sel_dropdown(fid('ddlPreviousVisaIssueDateDay_0'), day)
            if month: sel_dropdown(fid('ddlPreviousVisaIssueDateMonth_0'), month, by_text=True)
            if year:  fill(fid('tbxPreviousVisaIssueDateYear_0'), year)
            safe_fill(fid('tbxDurationOfStay_0'), g('q84_dur_vis1', 'Unknown'))

        # Visa anterior
        radio_yn('PreviouslyIssuedVisa', 'q87_visa_prev')
        if yn('q87_visa_prev'):
            time.sleep(0.5)
            day, month, year = gdate('q88_visa_emision')
            if day:   sel_dropdown(fid('ddlPreviousVisaIssueDateDay'), day)
            if month: sel_dropdown(fid('ddlPreviousVisaIssueDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxPreviousVisaIssueDateYear'), year)
            safe_fill(fid('tbxPreviousVisaNumber'), g('q89_visa_num', 'Do Not Know'))
            radio_yn('SameTypeVisa', 'q90_mismo_tipo')
            radio_yn('SameCountryVisa', 'q91_mismo_pais')
            radio_yn('TenYearVisa', 'q92_diez_anos')

        # Visa negada
        radio_yn('VisaRefused', 'q93_negacion')
        if yn('q93_negacion'):
            time.sleep(0.5)
            safe_fill(fid('tbxRefusalWherewhen'), g('q94_negacion_donde'))
            safe_fill(fid('tbxRefusalReason'), g('q95_razon_neg'))

        # Petición USCIS
        radio_yn('ImmigrantPetition', 'q96_peticion')
        if yn('q96_peticion'):
            time.sleep(0.3)
            safe_fill(fid('tbxImmigrantPetitionExplanation'), g('q97_peticion_exp'))

    except Exception as e:
        log.error(f"Error P8: {e}"); screenshot('p8_error')

    log.info("✓ P8"); next_pg(); save_id(); screenshot('p8_done')

    # ── P9 — CONTACTO EN EE.UU. (Q98-Q107) ───────────────────────────────────
    log.info("P9 — Contacto en EE.UU....")
    try:
        fill(fid('tbxUSContactSurname'), g('q98_cont_ap'))
        fill(fid('tbxUSContactGivenName'), g('q99_cont_nom'))
        safe_fill(fid('tbxUSContactOrganization'), g('q100_cont_org', 'Does Not Apply'))

        # Relación
        rel_map = {
            'friend':'FRIEND','amigo':'FRIEND','amiga':'FRIEND',
            'relative':'RELATIVE','familiar':'RELATIVE','pariente':'RELATIVE',
            'employer':'EMPLOYER','empleador':'EMPLOYER',
            'hotel':'HOTEL',
            'other':'OTHER','otro':'OTHER','otra':'OTHER',
        }
        rel_val = rel_map.get(g('q101_cont_rel','').lower(), 'FRIEND')
        sel_dropdown(fid('ddlUSContactRelationship'), rel_val)

        fill(fid('tbxUSContactAddressLine1'), g('q102_cont_dir'))
        fill(fid('tbxUSContactCity'), g('q103_cont_ciudad'))
        sel_dropdown(fid('ddlUSContactState'), g('q104_cont_estado'), by_text=True)
        safe_fill(fid('tbxUSContactZip'), g('q105_cont_zip'))
        fill(fid('tbxUSContactPhone'), g('q106_cont_tel'))
        safe_fill(fid('tbxUSContactEmail'), g('q107_cont_email'))

    except Exception as e:
        log.error(f"Error P9: {e}"); screenshot('p9_error')

    log.info("✓ P9"); next_pg(); save_id(); screenshot('p9_done')

    # ── P10 — FAMILIA (Q108-Q130) ────────────────────────────────────────────
    log.info("P10 — Familia...")
    try:
        # Padre
        fill(fid('tbxFatherSurname'), g('q108_padre_ap', 'Unknown'))
        fill(fid('tbxFatherGivenName'), g('q109_padre_nom', 'Unknown'))
        day, month, year = gdate('q110_padre_dob')
        if day:   sel_dropdown(fid('ddlFatherDOBDay'), day)
        if month: sel_dropdown(fid('ddlFatherDOBMonth'), month, by_text=True)
        if year:  fill(fid('tbxFatherDOBYear'), year)

        radio_yn('FatherInUS', 'q111_padre_eeuu')
        if yn('q111_padre_eeuu'):
            time.sleep(0.3)
            try:
                sel_dropdown(fid('ddlFatherUSStatus'),
                    g('q112_padre_estatus', 'OTHER'), by_text=True)
            except: pass

        # Madre
        fill(fid('tbxMotherSurname'), g('q113_madre_ap', 'Unknown'))
        fill(fid('tbxMotherGivenName'), g('q114_madre_nom', 'Unknown'))
        day, month, year = gdate('q115_madre_dob')
        if day:   sel_dropdown(fid('ddlMotherDOBDay'), day)
        if month: sel_dropdown(fid('ddlMotherDOBMonth'), month, by_text=True)
        if year:  fill(fid('tbxMotherDOBYear'), year)

        radio_yn('MotherInUS', 'q116_madre_eeuu')
        if yn('q116_madre_eeuu'):
            time.sleep(0.3)
            try:
                sel_dropdown(fid('ddlMotherUSStatus'),
                    g('q117_madre_estatus', 'OTHER'), by_text=True)
            except: pass

        # Familiares inmigrantes
        radio_yn('ImmediateRelatives', 'q118_fam_inm')
        if yn('q118_fam_inm'):
            time.sleep(0.5)
            safe_fill(fid('tbxRelativeSurname_0'), g('q119_fam1_ap'))
            safe_fill(fid('tbxRelativeGivenName_0'), g('q120_fam1_nom'))
            try:
                sel_dropdown(fid('ddlRelativeRelationship_0'), g('q121_fam1_rel'), by_text=True)
                sel_dropdown(fid('ddlRelativeStatus_0'), g('q122_fam1_estatus'), by_text=True)
            except: pass

        # Otros familiares
        radio_yn('OtherRelatives', 'q123_otros_fam')
        if yn('q123_otros_fam'):
            time.sleep(0.3)
            safe_fill(fid('tbxOtherRelativesExplanation'), g('q124_otros_fam_exp'))

        # Cónyuge (si aplica)
        civil = g('q8_civil','').lower()
        if civil in ['casado','married','union_libre','common_law']:
            safe_fill(fid('tbxSpouseSurname'), g('q125_con_ap'))
            safe_fill(fid('tbxSpouseGivenName'), g('q126_con_nom'))
            day, month, year = gdate('q127_con_dob')
            if day:   sel_dropdown(fid('ddlSpouseDOBDay'), day)
            if month: sel_dropdown(fid('ddlSpouseDOBMonth'), month, by_text=True)
            if year:  fill(fid('tbxSpouseDOBYear'), year)
            try:
                sel_dropdown(fid('ddlSpouseCountryOfBirth'),
                    g('q128_con_pais_nac', 'Dominican Republic'), by_text=True)
                sel_dropdown(fid('ddlSpouseCountryCitizenship'),
                    g('q129_con_ciudadania', 'Dominican Republic'), by_text=True)
            except: pass
            safe_fill(fid('tbxSpouseAddress'), g('q130_con_dir', 'Same'))

    except Exception as e:
        log.error(f"Error P10: {e}"); screenshot('p10_error')

    log.info("✓ P10"); next_pg(); save_id(); screenshot('p10_done')

    # ── P11 — TRABAJO ACTUAL (Q131-Q141) ─────────────────────────────────────
    log.info("P11 — Trabajo Actual...")
    try:
        ocup_map = {
            'employed':'E','empleado':'E','employee':'E',
            'self_employed':'X','self-employed':'X','independiente':'X',
            'empresario':'X','businessman':'X',
            'student':'S','estudiante':'S',
            'retired':'R','jubilado':'R','pensionado':'R',
            'unemployed':'U','desempleado':'U',
            'homemaker':'H','ama de casa':'H',
            'other':'O','otro':'O',
        }
        ocup_val = ocup_map.get(g('q131_ocupacion','').lower(), 'E')
        sel_dropdown(fid('ddlPrimaryOccupation'), ocup_val)

        fill(fid('tbxEmployerName'), g('q132_empleador'))
        fill(fid('tbxEmployerAddress'), g('q133_dir_emp1'))
        fill(fid('tbxEmployerCity'), g('q134_emp_ciudad'))
        safe_fill(fid('tbxEmployerStateProvince'), g('q135_emp_prov', 'Does Not Apply'))
        sel_dropdown(fid('ddlEmployerCountry'), 'Dominican Republic', by_text=True)
        safe_fill(fid('tbxEmployerZip'), g('q137_emp_postal', 'Does Not Apply'))
        fill(fid('tbxEmployerPhone'), g('q138_emp_tel'))

        # Fecha inicio
        day, month, year = gdate('q139_emp_inicio')
        if day:   sel_dropdown(fid('ddlEmpStartDateDay'), day)
        if month: sel_dropdown(fid('ddlEmpStartDateMonth'), month, by_text=True)
        if year:  fill(fid('tbxEmpStartDateYear'), year)

        safe_fill(fid('tbxMonthlyIncome'), g('q140_salario', '0'))
        fill(fid('tbxDutyDescription'), g('q141_funciones', 'Does Not Apply'))

    except Exception as e:
        log.error(f"Error P11: {e}"); screenshot('p11_error')

    log.info("✓ P11"); next_pg(); save_id(); screenshot('p11_done')

    # ── P12 — TRABAJO ANTERIOR (Q142-Q149) ───────────────────────────────────
    log.info("P12 — Trabajo Anterior...")
    try:
        radio_yn('PreviouslyEmployed', 'q142_emp_ant')
        if yn('q142_emp_ant'):
            time.sleep(0.5)
            safe_fill(fid('tbxPrevEmployerName_0'), g('q143_emp_ant_nom'))
            safe_fill(fid('tbxPrevEmployerAddress_0'), g('q144_dir_emp_ant'))
            safe_fill(fid('tbxPrevEmployerPhone_0'), g('q145_tel_emp_ant'))
            safe_fill(fid('tbxPrevEmpJobTitle_0'), g('q146_cargo_ant'))
            day, month, year = gdate('q147_inicio_ant')
            if day:   sel_dropdown(fid('ddlPrevEmpStartDateDay_0'), day)
            if month: sel_dropdown(fid('ddlPrevEmpStartDateMonth_0'), month, by_text=True)
            if year:  fill(fid('tbxPrevEmpStartDateYear_0'), year)
            day, month, year = gdate('q148_fin_ant')
            if day:   sel_dropdown(fid('ddlPrevEmpEndDateDay_0'), day)
            if month: sel_dropdown(fid('ddlPrevEmpEndDateMonth_0'), month, by_text=True)
            if year:  fill(fid('tbxPrevEmpEndDateYear_0'), year)
            safe_fill(fid('tbxPrevDutyDescription_0'), g('q149_func_ant'))

    except Exception as e:
        log.error(f"Error P12: {e}"); screenshot('p12_error')

    log.info("✓ P12"); next_pg(); save_id(); screenshot('p12_done')

    # ── P13 — EDUCACIÓN (Q151-Q156) ───────────────────────────────────────────
    log.info("P13 — Educación...")
    try:
        radio_yn('AttendedEducation', 'q151_edu')
        if yn('q151_edu'):
            time.sleep(0.5)
            safe_fill(fid('tbxSchoolName_0'), g('q152_escuela'))
            safe_fill(fid('tbxSchoolCityOrTown_0'), g('q153_escuela_dir'))
            safe_fill(fid('tbxFieldOfStudy_0'), g('q154_carrera', 'Does Not Apply'))
            day, month, year = gdate('q155_edu_inicio')
            if day:   sel_dropdown(fid('ddlEduFromDateDay_0'), day)
            if month: sel_dropdown(fid('ddlEduFromDateMonth_0'), month, by_text=True)
            if year:  fill(fid('tbxEduFromDateYear_0'), year)
            day, month, year = gdate('q156_edu_fin')
            if day:   sel_dropdown(fid('ddlEduToDateDay_0'), day)
            if month: sel_dropdown(fid('ddlEduToDateMonth_0'), month, by_text=True)
            if year:  fill(fid('tbxEduToDateYear_0'), year)

    except Exception as e:
        log.error(f"Error P13: {e}"); screenshot('p13_error')

    log.info("✓ P13"); next_pg(); save_id(); screenshot('p13_done')

    # ── P14 — INFO ADICIONAL (Q157-Q173) ─────────────────────────────────────
    log.info("P14 — Info Adicional...")
    try:
        # Clan o tribu
        radio_yn('ClanOrTribe', 'q157_clan')
        if yn('q157_clan'):
            safe_fill(fid('tbxClanOrTribeName'), g('q158_clan_nom'))

        # Países visitados
        fill(fid('tbxCountriesVisited'), g('q159_paises', 'None'))

        # Idiomas
        fill(fid('tbxLanguagesSpoken'), g('q160_idiomas', 'Spanish'))

        # Organizaciones
        radio_yn('Org', 'q161_org')
        if yn('q161_org'):
            safe_fill(fid('tbxOrgExplanation'), g('q162_org_nom'))

        # Habilidades especiales
        radio_yn('SpecializedSkills', 'q163_habilidades')
        if yn('q163_habilidades'):
            safe_fill(fid('tbxSpecializedSkillsExplanation'), g('q164_habilidades_exp'))

        # Servicio militar
        radio_yn('MilitaryService', 'q165_militar')
        if yn('q165_militar'):
            time.sleep(0.3)
            try:
                sel_dropdown(fid('ddlMilitaryCountry'),
                    g('q166_mil_pais', 'Dominican Republic'), by_text=True)
            except: pass
            safe_fill(fid('tbxMilitaryBranch'), g('q167_mil_rama'))
            safe_fill(fid('tbxMilitaryRank'), g('q168_mil_rango'))
            safe_fill(fid('tbxMilitarySpecialty'), g('q169_mil_esp'))
            day, month, year = gdate('q170_mil_inicio')
            if day:   sel_dropdown(fid('ddlMilFromDateDay'), day)
            if month: sel_dropdown(fid('ddlMilFromDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxMilFromDateYear'), year)
            day, month, year = gdate('q171_mil_fin')
            if day:   sel_dropdown(fid('ddlMilToDateDay'), day)
            if month: sel_dropdown(fid('ddlMilToDateMonth'), month, by_text=True)
            if year:  fill(fid('tbxMilToDateYear'), year)

        # Grupos paramilitares
        radio_yn('ParamilitaryOrg', 'q172_paramilitar')
        if yn('q172_paramilitar'):
            safe_fill(fid('tbxParamilitaryOrgExplanation'), g('q173_paramilitar_exp'))

    except Exception as e:
        log.error(f"Error P14: {e}"); screenshot('p14_error')

    log.info("✓ P14"); next_pg(); save_id(); screenshot('p14_done')

    # ── P15 — SEGURIDAD 1: Salud y Criminal (Q174-Q183) ──────────────────────
    log.info("P15 — Seguridad: Salud y Criminal...")
    try:
        radio_yn('DiseaseHazard', 'q174')
        radio_yn('DisorderHazard', 'q175')
        radio_yn('DrugUser', 'q176')
        radio_yn('Arrested', 'q177')
        if yn('q177'):
            safe_fill(fid('tbxArrestedExplanation'), g('q178_arresto'))
        radio_yn('ControlledSubstance', 'q179')
        if yn('q179'):
            safe_fill(fid('tbxControlledSubstanceExplanation'), g('q180', g('q180_traf_drogas')))
        radio_yn('Prostitution', 'q181')
        if yn('q181'):
            safe_fill(fid('tbxProstitutionExplanation'), g('q182', g('q182_prostitucion')))
        radio_yn('MoneyLaunder', 'q183')
        if yn('q183'):
            safe_fill(fid('tbxMoneyLaunderExplanation'), g('q184', g('q184_turpitud')))

    except Exception as e:
        log.error(f"Error P15: {e}"); screenshot('p15_error')

    log.info("✓ P15"); next_pg(); save_id(); screenshot('p15_done')

    # ── P16 — SEGURIDAD 2: Deportación y Terrorismo (Q185-Q198) ──────────────
    log.info("P16 — Seguridad: Deportación y Terrorismo...")
    try:
        radio_yn('IllegalActivities', 'q185')
        if yn('q185'):
            safe_fill(fid('tbxIllegalActivitiesExplanation'), g('q186', g('q186_deportacion')))
        radio_yn('TerrorOrg', 'q187')
        if yn('q187'):
            safe_fill(fid('tbxTerrorOrgExplanation'), g('q188', g('q188_terrorismo')))
        radio_yn('TerrorSupport', 'q189')
        if yn('q189'):
            safe_fill(fid('tbxTerrorSupportExplanation'), g('q190', g('q190_apoyo_terror')))
        radio_yn('TotalitarianParty', 'q191')
        if yn('q191'):
            safe_fill(fid('tbxTotalitarianPartyExplanation'), g('q192', g('q192_partido')))
        radio_yn('GenocideOrTorture', 'q193')
        if yn('q193'):
            safe_fill(fid('tbxGenocideExplanation'), g('q194', g('q194_genocidio')))
        radio_yn('Torture', 'q195')
        if yn('q195'):
            safe_fill(fid('tbxTortureExplanation'), g('q196', g('q196_tortura')))
        radio_yn('ChildSoldier', 'q197')
        if yn('q197'):
            safe_fill(fid('tbxChildSoldierExplanation'), g('q198', g('q198_menores')))

    except Exception as e:
        log.error(f"Error P16: {e}"); screenshot('p16_error')

    log.info("✓ P16"); next_pg(); save_id(); screenshot('p16_done')

    # ── P17 — SEGURIDAD 3: Overstay y Otros (Q199-Q207) ──────────────────────
    log.info("P17 — Seguridad: Overstay y Otros...")
    try:
        radio_yn('OverstayedVisa', 'q199')
        if yn('q199'):
            safe_fill(fid('tbxOverstayedVisaExplanation'), g('q200', g('q200_overstay')))
        radio_yn('MisrepresentedInfo', 'q201')
        if yn('q201'):
            safe_fill(fid('tbxMisrepresentedInfoExplanation'), g('q202', g('q202_fraude')))
        radio_yn('RenounceUSCitizenship', 'q203')
        radio_yn('ChildCustody', 'q204')
        if yn('q204'):
            safe_fill(fid('tbxChildCustodyExplanation'), g('q205', g('q205_custodia')))
        radio_yn('VotingViolation', 'q206')
        if yn('q206'):
            safe_fill(fid('tbxVotingViolationExplanation'), g('q207', g('q207_voto')))

    except Exception as e:
        log.error(f"Error P17: {e}"); screenshot('p17_error')

    log.info("✓ P17"); next_pg(); save_id(); screenshot('p17_done')

    # ── P18 — PREPARADOR Y FIRMA (Q222-Q227) ──────────────────────────────────
    log.info("P18 — Preparador del formulario...")
    try:
        radio_yn('PreparedByOther', 'q222_asistido')
        if yn('q222_asistido'):
            time.sleep(0.5)
            safe_fill(fid('tbxPrepSurname'), g('q223_asist_ap'))
            safe_fill(fid('tbxPrepGivenName'), g('q224_asist_nom'))
            safe_fill(fid('tbxPrepOrg'), g('q225_asist_org', 'TengoVisaRD'))
            safe_fill(fid('tbxPrepAddress'), g('q226_asist_dir'))
            safe_fill(fid('tbxPrepPhone'), g('q227_asist_tel'))

    except Exception as e:
        log.error(f"Error P18: {e}"); screenshot('p18_error')

    # NO hacer next aquí — el cliente firma manualmente
    screenshot('p18_final')
    save_id()

    # ── RESULTADO FINAL ───────────────────────────────────────────────────────
    try:
        with open('/tmp/ceac_app_id.txt') as f: APP_ID = f.read().strip()
    except: APP_ID = 'Ver en navegador'

    print()
    print("=" * 65)
    print("✅  DS-160 LLENADO AUTOMÁTICAMENTE EN CEAC")
    print("=" * 65)
    print(f"Cliente   : {meta.get('nombre','')} {meta.get('apellido','')}")
    print(f"Pasaporte : {meta.get('pasaporte','')}")
    print(f"App ID    : {APP_ID}")
    print(f"Completud : {meta.get('completeness_pct','?')}%")
    print()
    print("PASOS MANUALES FINALES (en el navegador):")
    print("  1. Revisar cada página visualmente")
    print("  2. Corregir dropdowns de país si es necesario")
    print("  3. Subir foto del solicitante (5x5 cm, fondo blanco)")
    print("  4. El SOLICITANTE firma electrónicamente")
    print("  5. SUBMIT final — NO hacer antes de revisar TODO")
    print(f"  6. Guardar el App ID: {APP_ID}")
    print()
    print("Screenshots guardados en: /tmp/ceac_*.png")
    print("Log completo en: /tmp/ceac_selenium.log")
    print("=" * 65)

    if args.visible:
        input("\n⏸  Navegador abierto para revisión. Enter para cerrar...")

except KeyboardInterrupt:
    log.info("Interrumpido por el usuario")
    drv.save_screenshot('/tmp/ceac_interrupted.png')
except Exception as e:
    log.error(f"Error general: {e}")
    drv.save_screenshot('/tmp/ceac_error_general.png')
    raise
finally:
    if not args.visible:
        drv.quit()
