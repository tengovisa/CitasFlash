#!/usr/bin/env python3
"""
ceac_selenium.py — Automatización DS-160 en CEAC
TengoVisaRD CRM
Uso: python3 ceac_selenium.py <archivo.json>
     python3 ceac_selenium.py <archivo.json> --visible
"""
import sys, json, os, time, argparse, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('/tmp/ceac_selenium.log')])
log = logging.getLogger('CEAC')

parser = argparse.ArgumentParser()
parser.add_argument('json_file')
parser.add_argument('--visible', action='store_true')
parser.add_argument('--reanudar', default=None)
args = parser.parse_args()

if not os.path.exists(args.json_file):
    log.error(f"Archivo no encontrado: {args.json_file}"); sys.exit(1)

with open(args.json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

meta = data.get('meta', {})
F    = data.get('fields', {})

log.info(f"Cliente: {meta.get('nombre','')} {meta.get('apellido','')}")
log.info(f"Pasaporte: {meta.get('pasaporte','')}")
log.info(f"Completitud: {meta.get('completeness_pct','?')}%")

def g(key, default=''):
    v = F.get(key, default)
    return str(v).strip() if v and str(v).strip() not in ['None','null'] else default

def gdate(key):
    v = g(key)
    if not v: return '', '', ''
    try:
        from datetime import datetime as dt
        d = dt.strptime(v, '%Y-%m-%d')
        M = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
             7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
        return str(d.day), M[d.month], str(d.year)
    except: return '', '', ''

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
except ImportError:
    log.error("pip install selenium --break-system-packages"); sys.exit(1)

opts = Options()
if not args.visible:
    opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_argument('--window-size=1366,768')
opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
opts.add_experimental_option('excludeSwitches', ['enable-automation'])
opts.add_experimental_option('useAutomationExtension', False)

DRIVERS = ['/usr/bin/chromedriver','/usr/lib/chromium-browser/chromedriver',
           '/snap/bin/chromedriver','/usr/lib/chromium/chromedriver']
driver_path = next((p for p in DRIVERS if os.path.exists(p)), None)
if not driver_path:
    log.error("chromedriver no encontrado"); sys.exit(1)
log.info(f"chromedriver: {driver_path}")

def wait_el(drv, el_id, timeout=10):
    return WebDriverWait(drv, timeout).until(
        EC.presence_of_element_located((By.ID, el_id)))

def fill(drv, el_id, value):
    if not value or value in ['None','null','']: return False
    try:
        el = wait_el(drv, el_id)
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.clear(); el.send_keys(str(value)); return True
    except Exception as e:
        log.warning(f"fill {el_id}: {e}"); return False

def sel(drv, el_id, value, by_text=False):
    if not value or value in ['None','null','']: return False
    try:
        el = wait_el(drv, el_id)
        s = Select(el)
        if by_text:
            for o in s.options:
                if value.upper() in o.text.upper():
                    s.select_by_visible_text(o.text); return True
        try: s.select_by_value(value); return True
        except:
            for o in s.options:
                if value.upper() in o.get_attribute('value').upper():
                    s.select_by_value(o.get_attribute('value')); return True
        log.warning(f"sel {el_id}: '{value}' no encontrado")
    except Exception as e:
        log.warning(f"sel {el_id}: {e}")
    return False

def radio(drv, name, yes=True):
    v = 'Y' if yes else 'N'
    selectors = [
        f'input[id*="{name}"][value="{v}"]',
        f'input[name*="{name}"][value="{v}"]',
        f'input[id*="{name}"][id*="{"Yes" if yes else "No"}"]',
    ]
    for css in selectors:
        try:
            el = drv.find_element(By.CSS_SELECTOR, css)
            drv.execute_script("arguments[0].click();", el); return True
        except: pass
    log.warning(f"radio {name}={v} no encontrado")
    return False

def next_pg(drv):
    for bid in ['ctl00_SiteContentPlaceHolder_FormView1_btnNext',
                'ctl00_SiteContentPlaceHolder_btnNext']:
        try:
            btn = WebDriverWait(drv, 8).until(EC.element_to_be_clickable((By.ID, bid)))
            drv.execute_script("arguments[0].click();", btn)
            time.sleep(2.5); return True
        except: pass
    try:
        btn = drv.find_element(By.CSS_SELECTOR, 'input[value="Next"],input[value="NEXT"]')
        btn.click(); time.sleep(2.5); return True
    except: pass
    log.error("Botón Next no encontrado"); return False

def save_id(drv):
    try:
        el = drv.find_element(By.ID, 'ctl00_SiteContentPlaceHolder_lblAppID')
        aid = el.text.strip()
        if aid:
            with open('/tmp/ceac_app_id.txt','w') as f: f.write(aid)
            log.info(f"Application ID: {aid}")
    except: pass

def yn(key): return g(key,'NO').upper() in ['YES','SI','SÍ','TRUE']

# ── INICIO ────────────────────────────────────────
service = Service(driver_path)
drv = webdriver.Chrome(service=service, options=opts)
drv.implicitly_wait(4)
APP_ID = ''

try:
    log.info("Navegando a CEAC...")
    drv.get('https://ceac.state.gov/GenNIV/Default.aspx')
    time.sleep(3)
    drv.save_screenshot('/tmp/ceac_p0_inicio.png')

    if args.reanudar:
        log.info(f"Reanudando: {args.reanudar}")
        fill(drv, 'ctl00_SiteContentPlaceHolder_tbxAppID', args.reanudar)
        day,month,year = gdate('q9_dob')
        fill(drv, 'ctl00_SiteContentPlaceHolder_tbxDOBDay', day)
        sel(drv, 'ctl00_SiteContentPlaceHolder_dlstDOBMonth', month, by_text=True)
        fill(drv, 'ctl00_SiteContentPlaceHolder_tbxDOBYear', year)
        try:
            btn = WebDriverWait(drv,10).until(EC.element_to_be_clickable(
                (By.ID,'ctl00_SiteContentPlaceHolder_btnRetrieve')))
            btn.click(); time.sleep(3)
        except: pass
    else:
        log.info("Nueva aplicación...")
        try:
            sel(drv,'ctl00_SiteContentPlaceHolder_LocationDropDownList','DOMINGO',by_text=True)
            time.sleep(1)
        except: pass
        try:
            cb = drv.find_element(By.ID,'ctl00_SiteContentPlaceHolder_cbxAgreement')
            if not cb.is_selected(): cb.click()
        except: pass
        try:
            btn = WebDriverWait(drv,10).until(EC.element_to_be_clickable(
                (By.ID,'ctl00_SiteContentPlaceHolder_btnNew')))
            btn.click(); time.sleep(3); save_id(drv)
        except Exception as e:
            log.warning(f"Inicio: {e}")

    # P1 — Personal
    log.info("P1 — Información Personal...")
    drv.save_screenshot('/tmp/ceac_p1.png')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxSurnames', g('q1_apellido'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxGivenName', g('q2_nombre'))
    radio(drv,'NoNativeName', yes=(not g('q6_nombre_nativo')))
    if g('q6_nombre_nativo'):
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFullNameNative', g('q6_nombre_nativo'))
    radio(drv,'OtherNames', yes=yn('q3_otros_nombres'))
    if yn('q3_otros_nombres'):
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxOtherSurnames', g('q4_otro_apellido'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxOtherGivenName', g('q5_otro_nombre'))
    try:
        s = Select(drv.find_element(By.ID,'ctl00_SiteContentPlaceHolder_FormView1_ddlSEX'))
        s.select_by_value('M' if g('q7_sexo','M').upper()=='M' else 'F')
    except: radio(drv,'SEX', yes=(g('q7_sexo','M').upper()=='M'))
    civil = {'soltero':'S','single':'S','casado':'M','married':'M','viudo':'W',
             'divorciado':'D','separado':'SP','union_libre':'C'}.get(g('q8_civil','').lower(),'S')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlMaritalStatus', civil)
    day,month,year = gdate('q9_dob')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxDOBDay', day)
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstDOBMonth', month, by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear', year)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCityOfBirth', g('q10_ciudad_nac'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxStateOfBirth', g('q11_prov_nac') or 'Does Not Apply')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlCountryOfBirth','DOMINICAN',by_text=True)
    log.info("✓ P1"); next_pg(drv); save_id(drv)

    # P2 — Nacionalidad
    log.info("P2 — Nacionalidad...")
    drv.save_screenshot('/tmp/ceac_p2.png')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlCOB','DOMINICAN',by_text=True)
    radio(drv,'OtherNationality', yes=yn('q14_otra_nac'))
    radio(drv,'PermanentResident', yes=yn('q16_pas_otra_nac'))
    if g('q20_cedula'):
        radio(drv,'NationalID', yes=True); time.sleep(0.5)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxNATIONAL_ID', g('q20_cedula'))
    else:
        radio(drv,'NationalID', yes=False)
    radio(drv,'USSSN', yes=False)
    radio(drv,'USTIN', yes=False)
    log.info("✓ P2"); next_pg(drv); save_id(drv)

    # P3 — Dirección
    log.info("P3 — Dirección...")
    drv.save_screenshot('/tmp/ceac_p3.png')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN1', g('q23_dir1'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN2', g('q24_dir2'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_CITY', g('q25_ciudad'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_STATE', g('q26_provincia') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_POSTAL', g('q27_postal') or 'Does Not Apply')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_ADDR_COUNTRY','DOMINICAN',by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_HOME_TEL', g('q33_tel'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_MOBILE_TEL', g('q34_tel2') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_BUS_TEL', g('q35_tel_trab') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_EMAIL', g('q36_email'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_EMAIL_CONFIRM', g('q36_email'))
    radio(drv,'SocialMedia', yes=yn('q37_redes'))
    if yn('q37_redes') and g('q38_red1') and g('q39_user1'):
        time.sleep(0.5)
        sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlSocialMediaPlatform1',g('q38_red1'),by_text=True)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxSocialMediaHandle1', g('q39_user1'))
    log.info("✓ P3"); next_pg(drv); save_id(drv)

    # P4 — Pasaporte
    log.info("P4 — Pasaporte...")
    drv.save_screenshot('/tmp/ceac_p4.png')
    tipo = {'REGULAR':'R','OFFICIAL':'O','DIPLOMATIC':'D'}.get(g('q42_tipo_pas','REGULAR').upper(),'R')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_TYPE', tipo)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_NUM', g('q43_numpas'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_BOOK_NUM', g('q44_libreta') or 'Does Not Apply')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_CNTRY','DOMINICAN',by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUE_CITY', g('q46_ciudad_emision'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUE_STATE', g('q47_prov_emision') or 'Does Not Apply')
    day,month,year = gdate('q48_emision')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUE_DAY', day)
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstPPT_ISSUE_MONTH', month, by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUE_YR', year)
    day,month,year = gdate('q49_vence')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_EXPIRE_DAY', day)
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstPPT_EXPIRE_MONTH', month, by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_EXPIRE_YR', year)
    radio(drv,'LostPPT', yes=yn('q50_perdio_pas'))
    log.info("✓ P4"); next_pg(drv); save_id(drv)

    # P5 — Viaje
    log.info("P5 — Viaje...")
    drv.save_screenshot('/tmp/ceac_p5.png')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_PURPOSE','TOURISM',by_text=True)
    radio(drv,'SpecificTravel', yes=yn('q56_planes'))
    time.sleep(0.5)
    day,month,year = gdate('q57_llegada')
    if day:
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_DAY', day)
        sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstARRIVAL_MONTH', month, by_text=True)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_YR', year)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_FLIGHT', g('q58_vuelo_lleg') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_CITY', g('q59_ciudad_lleg') or g('q66_ciudad_hosp'))
    dur = g('q64_duracion','1 WEEK')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlSTAY_LENGTH', dur, by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN1', g('q65_dir_hospedaje'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_CITY', g('q66_ciudad_hosp'))
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlUS_POC_ADDR_STATE', g('q67_estado_hosp'), by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_ZIP', g('q105_cont_zip') or '00000')
    paga = {'SELF':'S','YO MISMO':'S','EMPLEADOR':'E','PRESENT EMPLOYER':'E',
            'OTRA PERSONA':'O','OTHER PERSON':'O'}.get(g('q68_paga','SELF').upper(),'S')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlWHO_PAYING', paga)
    log.info("✓ P5"); next_pg(drv); save_id(drv)

    # P6 — Compañeros
    log.info("P6 — Compañeros...")
    radio(drv,'TravelingWithOthers', yes=yn('q76_compan'))
    log.info("✓ P6"); next_pg(drv); save_id(drv)

    # P7 — Viajes previos
    log.info("P7 — Viajes previos...")
    drv.save_screenshot('/tmp/ceac_p7.png')
    radio(drv,'PreviousUSTravel', yes=yn('q82_estuvo'))
    if yn('q82_estuvo'):
        time.sleep(0.5)
        day,month,year = gdate('q83_fecha_vis1')
        if day:
            fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARR_DAY_1', day)
            sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstARR_MONTH_1', month, by_text=True)
            fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxARR_YEAR_1', year)
            fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxDUR_STAY_1', g('q84_dur_vis1') or 'Does Not Apply')
    radio(drv,'PreviousUSVisa', yes=yn('q87_visa_prev'))
    if yn('q87_visa_prev'):
        time.sleep(0.5)
        day,month,year = gdate('q88_visa_emision')
        if day:
            fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_ISSUED_DAY', day)
            sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstPREV_VISA_ISSUED_MONTH', month, by_text=True)
            fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_ISSUED_YR', year)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_NUM', g('q89_visa_num') or 'Do Not Know')
        radio(drv,'SameVisaType', yes=yn('q90_mismo_tipo'))
        radio(drv,'SameCountry', yes=yn('q91_mismo_pais'))
        radio(drv,'TenYearVisa', yes=yn('q92_diez_anos'))
    radio(drv,'DeniedVisa', yes=yn('q93_negacion'))
    if yn('q93_negacion'):
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxDENIED_VISA_EXPL', g('q95_razon_neg'))
    radio(drv,'ImmigrationPetition', yes=yn('q96_peticion'))
    log.info("✓ P7"); next_pg(drv); save_id(drv)

    # P8 — Contacto EEUU
    log.info("P8 — Contacto EEUU...")
    drv.save_screenshot('/tmp/ceac_p8.png')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_SURNAME', g('q98_cont_ap'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_GIVEN_NAME', g('q99_cont_nom'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_ORG', g('q100_cont_org') or 'Does Not Apply')
    rel = {'AMIGO':'F','FRIEND':'F','FAMILIAR':'R','RELATIVE':'R','EMPLEADOR':'E',
           'HOTEL':'H','OTHER':'O','OTRO':'O'}.get(g('q101_cont_rel','OTHER').upper(),'O')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlCONT_REL', rel)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_ADDR_LN1', g('q102_cont_dir'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_ADDR_CITY', g('q103_cont_ciudad'))
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlCONT_ADDR_STATE', g('q104_cont_estado'), by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_ADDR_ZIP', g('q105_cont_zip'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_HOME_TEL', g('q106_cont_tel'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxCONT_EMAIL', g('q107_cont_email') or 'Does Not Apply')
    log.info("✓ P8"); next_pg(drv); save_id(drv)

    # P9 — Familia
    log.info("P9 — Familia...")
    drv.save_screenshot('/tmp/ceac_p9.png')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_SURNAME', g('q108_padre_ap') or 'UNKNOWN')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_GIVEN_NAME', g('q109_padre_nom') or 'UNKNOWN')
    day,month,year = gdate('q110_padre_dob')
    if day:
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_DOB_DAY', day)
        sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstFATHER_DOB_MONTH', month, by_text=True)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_DOB_YR', year)
    radio(drv,'FatherInUS', yes=yn('q111_padre_eeuu'))
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_SURNAME', g('q113_madre_ap') or 'UNKNOWN')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_GIVEN_NAME', g('q114_madre_nom') or 'UNKNOWN')
    day,month,year = gdate('q115_madre_dob')
    if day:
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_DOB_DAY', day)
        sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstMOTHER_DOB_MONTH', month, by_text=True)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_DOB_YR', year)
    radio(drv,'MotherInUS', yes=yn('q116_madre_eeuu'))
    radio(drv,'RelativesInUS', yes=yn('q118_fam_inm'))
    log.info("✓ P9"); next_pg(drv); save_id(drv)

    # P10 — Trabajo
    log.info("P10 — Trabajo...")
    drv.save_screenshot('/tmp/ceac_p10.png')
    ocup = {'EMPLOYED':'E','STUDENT':'S','SELF-EMPLOYED':'SE','RETIRED':'R',
            'UNEMPLOYED':'U','HOMEMAKER':'H','OTHER':'O'}.get(g('q131_ocupacion','EMPLOYED').upper(),'E')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlPRIMARY_OCC', ocup)
    time.sleep(0.5)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMPLOYER_NAME', g('q132_empleador') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMPLOYER_ADDR_LN1', g('q133_dir_emp1') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMPLOYER_ADDR_CITY', g('q134_emp_ciudad') or 'Does Not Apply')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMPLOYER_ADDR_POSTAL', g('q137_emp_postal') or 'Does Not Apply')
    sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_ddlEMPLOYER_ADDR_COUNTRY','DOMINICAN',by_text=True)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMPLOYER_TEL', g('q138_emp_tel') or 'Does Not Apply')
    day,month,year = gdate('q139_emp_inicio')
    if day:
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMP_START_DAY', day)
        sel(drv,'ctl00_SiteContentPlaceHolder_FormView1_dlstEMP_START_MONTH', month, by_text=True)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxEMP_START_YR', year)
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxMONTHLY_SALARY', g('q140_salario') or '0')
    fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxDUTY_DESC', g('q141_funciones') or 'Does Not Apply')
    log.info("✓ P10"); next_pg(drv); save_id(drv)

    # P11 — Trabajo anterior
    log.info("P11 — Empleo anterior...")
    radio(drv,'PreviouslyEmployed', yes=yn('q142_emp_ant'))
    log.info("✓ P11"); next_pg(drv); save_id(drv)

    # P12 — Educación
    log.info("P12 — Educación...")
    radio(drv,'AttendedEducation', yes=yn('q151_edu'))
    if yn('q151_edu'):
        time.sleep(0.5)
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxSECONDARY_SCHOOL_NAME', g('q152_escuela'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxSECONDARY_SCHOOL_CITY', g('q153_escuela_dir'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxFIELD_OF_STUDY', g('q154_carrera') or 'Does Not Apply')
    log.info("✓ P12"); next_pg(drv); save_id(drv)

    # P13-16 — SEGURIDAD
    SEC_RADIOS = [
        ('q174','DiseaseHazard'),('q175','DisorderHazard'),('q176','DrugUser'),
        ('q177','Arrested'),('q179','ControlledSubstance'),('q181','Prostitution'),
        ('q183','MoneyLaunder'),('q185','IllegalActivities'),('q187','TerrorOrg'),
        ('q193','GenocideOrTorture'),('q195','Torture'),('q197','ChildSoldier'),
        ('q199','OverstayedVisa'),('q201','MisrepresentedInfo'),
        ('q204','ChildCustody'),('q206','VotingViolation'),
    ]
    page_breaks = [3, 3, 5, 5]  # cuántos radios por página
    idx = 0
    for pg_radios in page_breaks:
        pg_num = 13 + page_breaks.index(pg_radios)
        log.info(f"P{pg_num} — Seguridad...")
        drv.save_screenshot(f'/tmp/ceac_p{pg_num}.png')
        batch = SEC_RADIOS[idx:idx+pg_radios]
        for key, rname in batch:
            is_yes = yn(key)
            radio(drv, rname, yes=is_yes)
            if is_yes:
                time.sleep(0.3)
                try:
                    expl_id = f'ctl00_SiteContentPlaceHolder_FormView1_tbx{rname}_EXPL'
                    fill(drv, expl_id, 'See attached documentation')
                except: pass
        idx += pg_radios
        log.info(f"✓ P{pg_num}"); next_pg(drv); save_id(drv)

    # FINAL — Idiomas
    log.info("FINAL — Idiomas...")
    drv.save_screenshot('/tmp/ceac_final_idiomas.png')
    try:
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxLangs', g('q160_idiomas','Spanish'))
    except: pass
    radio(drv,'PreparedByOther', yes=yn('q222_asistido'))
    if yn('q222_asistido'):
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREP_SURNAME', g('q223_asist_ap'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREP_GIVEN_NAME', g('q224_asist_nom'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREP_ORG', g('q225_asist_org') or 'TengoVisaRD')
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREP_ADDR_LN1', g('q226_asist_dir'))
        fill(drv,'ctl00_SiteContentPlaceHolder_FormView1_tbxPREP_TEL', g('q227_asist_tel'))

    drv.save_screenshot('/tmp/ceac_final.png')
    save_id(drv)

    try:
        with open('/tmp/ceac_app_id.txt') as f: APP_ID = f.read().strip()
    except: APP_ID = 'Ver en navegador'

    print()
    print("="*60)
    print("✅ DS-160 LLENADO EN CEAC")
    print("="*60)
    print(f"Cliente:  {meta.get('nombre','')} {meta.get('apellido','')}")
    print(f"App ID:   {APP_ID}")
    print(f"Campos:   {meta.get('completeness_pct','?')}% completo")
    print()
    print("PASOS MANUALES FINALES:")
    print("  1. Revisar cada página visualmente")
    print("  2. Corregir dropdowns si es necesario")
    print("  3. Firma electrónica del solicitante")
    print("  4. SUBMIT final en CEAC")
    print(f"  5. Guardar App ID: {APP_ID}")
    print()
    print("Screenshots: /tmp/ceac_*.png")
    print("Log: /tmp/ceac_selenium.log")
    print("="*60)

    if args.visible:
        input("\nNavegador abierto. Enter para cerrar...")

except KeyboardInterrupt:
    log.info("Interrumpido")
    drv.save_screenshot('/tmp/ceac_interrupted.png')
except Exception as e:
    log.error(f"Error general: {e}")
    drv.save_screenshot('/tmp/ceac_error_general.png')
finally:
    if not args.visible:
        drv.quit()
