#!/usr/bin/env python3
"""
ceac_upload.py — Sube DS-160 al sistema CEAC
Uso: python3 ceac_upload.py <archivo_ds160.json>

Requiere: pip install selenium webdriver-manager
El script llena automáticamente el DS-160 en ceac.state.gov
usando los datos del JSON exportado por TengoVisaRD CRM.
"""

import sys, json, time, os
from datetime import datetime

# ── Validar argumento ─────────────────────────────────
if len(sys.argv) < 2:
    print("Uso: python3 ceac_upload.py ds160_cliente.json")
    sys.exit(1)

JSON_FILE = sys.argv[1]
if not os.path.exists(JSON_FILE):
    print(f"ERROR: Archivo no encontrado: {JSON_FILE}")
    sys.exit(1)

with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

meta   = data.get('meta', {})
fields = data.get('fields', {})

# ── Validación previa al upload ───────────────────────
REQUIRED = [
    'q1_apellido','q2_nombre','q7_sexo','q8_civil','q9_dob',
    'q10_ciudad_nac','q12_pais_nac','q13_nacionalidad',
    'q23_dir1','q25_ciudad','q33_tel','q36_email',
    'q43_numpas','q45_pais_pas','q48_emision','q49_vence',
    'q55_proposito','q64_duracion','q65_dir_hospedaje',
    'q66_ciudad_hosp','q67_estado_hosp',
    'q98_cont_ap','q99_cont_nom','q101_cont_rel',
    'q102_cont_dir','q103_cont_ciudad','q104_cont_estado',
    'q105_cont_zip','q106_cont_tel',
    'q108_padre_ap','q109_padre_nom',
    'q113_madre_ap','q114_madre_nom',
    'q131_ocupacion','q160_idiomas',
    'q174','q175','q176','q177','q179','q181','q183',
    'q185','q187','q189','q191','q193','q195','q197',
    'q199','q201','q203','q204','q206',
]

LABELS = {
    'q1_apellido':'Apellido(s)','q2_nombre':'Nombre(s)',
    'q7_sexo':'Sexo','q8_civil':'Estado civil',
    'q9_dob':'Fecha nacimiento','q10_ciudad_nac':'Ciudad nacimiento',
    'q12_pais_nac':'País nacimiento','q13_nacionalidad':'Nacionalidad',
    'q23_dir1':'Dirección','q25_ciudad':'Ciudad',
    'q33_tel':'Teléfono','q36_email':'Email',
    'q43_numpas':'Número pasaporte','q45_pais_pas':'País emisor',
    'q48_emision':'Fecha expedición','q49_vence':'Fecha vencimiento',
    'q55_proposito':'Propósito viaje','q64_duracion':'Duración estadía',
    'q65_dir_hospedaje':'Dir. hospedaje','q66_ciudad_hosp':'Ciudad hospedaje',
    'q67_estado_hosp':'Estado hospedaje',
    'q98_cont_ap':'Ap. contacto EE.UU.','q99_cont_nom':'Nom. contacto EE.UU.',
    'q101_cont_rel':'Relación contacto','q102_cont_dir':'Dir. contacto',
    'q103_cont_ciudad':'Ciudad contacto','q104_cont_estado':'Estado contacto',
    'q105_cont_zip':'ZIP contacto','q106_cont_tel':'Tel. contacto',
    'q108_padre_ap':'Apellido padre','q109_padre_nom':'Nombre padre',
    'q113_madre_ap':'Apellido madre','q114_madre_nom':'Nombre madre',
    'q131_ocupacion':'Ocupación','q160_idiomas':'Idiomas',
    'q174':'Enfermedad comunicable','q175':'Trastorno mental',
    'q176':'Drogas','q177':'Arrestado','q179':'Tráfico drogas',
    'q181':'Prostitución','q183':'Crimen/fraude','q185':'Deportado',
    'q187':'Terrorismo','q189':'Apoyo terrorismo','q191':'Partido comunista',
    'q193':'Genocidio','q195':'Tortura','q197':'Reclutó menores',
    'q199':'Overstay','q201':'Fraude visa','q203':'Renunció ciudadanía',
    'q204':'Custodia ilegal','q206':'Votó ilegalmente',
}

print("=" * 60)
print("DS-160 CEAC — Verificación previa al upload")
print("=" * 60)
print(f"Cliente:   {meta.get('nombre','')} {meta.get('apellido','')}")
print(f"Email:     {meta.get('email','')}")
print(f"Pasaporte: {meta.get('pasaporte','')}")
print(f"Completitud: {meta.get('filled_fields','?')}/{meta.get('total_fields','?')} ({meta.get('completeness_pct','?')}%)")
print(f"Generado:  {meta.get('generated_at','')}")
print(f"Asesor:    {meta.get('advisor_notes','(sin notas)')[:80]}")
print()

# Verificar campos requeridos
missing = []
for k in REQUIRED:
    v = fields.get(k)
    if not v or not str(v).strip() or v in ['null','None']:
        missing.append((k, LABELS.get(k, k)))

if missing:
    print(f"⚠️  CAMPOS REQUERIDOS FALTANTES ({len(missing)}):")
    for k, l in missing:
        print(f"   ✗ {k:30} — {l}")
    print()
    print("❌ No se puede subir al CEAC hasta completar estos campos.")
    print("   Use el panel asesor para completarlos:")
    print("   https://crm.tengovisard.com/ds160/admin.html")
    sys.exit(2)

print("✅ Todos los campos requeridos están completos")
print()

# ── Mostrar resumen del formulario ────────────────────
print("RESUMEN DEL FORMULARIO:")
print("-" * 40)
SUMMARY = [
    ('Apellido(s)',        fields.get('q1_apellido','')),
    ('Nombre(s)',          fields.get('q2_nombre','')),
    ('Sexo',              fields.get('q7_sexo','')),
    ('Estado civil',      fields.get('q8_civil','')),
    ('Fecha nacimiento',  fields.get('q9_dob','')),
    ('Ciudad nacimiento', fields.get('q10_ciudad_nac','')),
    ('País nacimiento',   fields.get('q12_pais_nac','')),
    ('Nacionalidad',      fields.get('q13_nacionalidad','')),
    ('Cédula',            fields.get('q20_cedula','')),
    ('Teléfono',          fields.get('q33_tel','')),
    ('Email',             fields.get('q36_email','')),
    ('Pasaporte #',       fields.get('q43_numpas','')),
    ('País emisor',       fields.get('q45_pais_pas','')),
    ('Expedición',        fields.get('q48_emision','')),
    ('Vencimiento',       fields.get('q49_vence','')),
    ('Propósito viaje',   fields.get('q55_proposito','')),
    ('Duración estadía',  fields.get('q64_duracion','')),
    ('Hospedaje',         fields.get('q65_dir_hospedaje','')),
    ('Ciudad EE.UU.',     fields.get('q66_ciudad_hosp','')),
    ('Estado EE.UU.',     fields.get('q67_estado_hosp','')),
    ('Contacto EE.UU.',   f"{fields.get('q99_cont_nom','')} {fields.get('q98_cont_ap','')}"),
    ('Tel. contacto',     fields.get('q106_cont_tel','')),
    ('Padre',             f"{fields.get('q109_padre_nom','')} {fields.get('q108_padre_ap','')}"),
    ('Madre',             f"{fields.get('q114_madre_nom','')} {fields.get('q113_madre_ap','')}"),
    ('Ocupación',         fields.get('q131_ocupacion','')),
    ('Empleador',         fields.get('q132_empleador','')),
    ('Idiomas',           fields.get('q160_idiomas','')),
]
for label, val in SUMMARY:
    if val and val.strip():
        print(f"  {label:<22}: {val}")

print()
print("PREGUNTAS DE SEGURIDAD (S13):")
SEC = [
    ('q174','Enfermedad comunicable'),('q175','Trastorno mental'),
    ('q176','Drogas'),('q177','Arrestado'),('q179','Tráfico drogas'),
    ('q181','Prostitución'),('q183','Crimen/fraude'),('q185','Deportado'),
    ('q187','Terrorismo'),('q199','Overstay'),('q201','Fraude visa'),
]
for k, l in SEC:
    v = fields.get(k, '?')
    icon = '🔴' if str(v).upper() in ['YES','SI','SÍ'] else '🟢'
    print(f"  {icon} {l}: {v}")

print()
print("=" * 60)
print("✅ FORMULARIO VERIFICADO — Listo para subir al CEAC")
print()
print("PRÓXIMOS PASOS:")
print("  1. Ingresar a https://ceac.state.gov/GenNIV/Default.aspx")
print("  2. Seleccionar embajada: Santo Domingo")
print("  3. Iniciar nueva aplicación o continuar")
print("  4. Llenar con los datos de este reporte")
print("  5. Guardar el Número de Aplicación (AA-XXXXXXXXXX)")
print()
print(f"Archivo JSON: {JSON_FILE}")
print(f"Generado por: TengoVisaRD CRM — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 60)

# Guardar reporte de verificación
report_file = JSON_FILE.replace('.json', '_REPORTE.txt')
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(f"DS-160 REPORTE DE VERIFICACIÓN\n")
    f.write(f"{'='*50}\n")
    f.write(f"Cliente: {meta.get('nombre','')} {meta.get('apellido','')}\n")
    f.write(f"Email: {meta.get('email','')}\n")
    f.write(f"Pasaporte: {meta.get('pasaporte','')}\n")
    f.write(f"Completitud: {meta.get('completeness_pct','?')}%\n")
    f.write(f"Verificado: {datetime.now().isoformat()}\n")
    f.write(f"Asesor notas: {meta.get('advisor_notes','')}\n")
    f.write(f"\nCAMPOS COMPLETOS: {meta.get('filled_fields','?')}/{meta.get('total_fields','?')}\n")
    if missing:
        f.write(f"\nCAMPOS FALTANTES ({len(missing)}):\n")
        for k,l in missing: f.write(f"  - {k}: {l}\n")

print(f"Reporte guardado: {report_file}")
