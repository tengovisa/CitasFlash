#!/usr/bin/env python3
"""
Script de exportación DS-160 — TengoVisaRD CRM
Genera JSON con claves qXXX para llenado CEAC
Uso: python3 export_ds160.py <caso_id>
     python3 export_ds160.py all
"""
import sys, json, os, re
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('/root/.env.tengovisa')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ── MAPA LEGACY: campo_qXXX → nombre_en_datos ────────────────────────────────
# Cuando los datos fueron guardados con nombres legacy (sin prefijo q),
# este mapa permite recuperarlos bajo la clave qXXX correcta
LEGACY = {
    "q1_apellido":      "apellido_primario",
    "q2_nombre":        "nombre",
    "q6_nombre_nativo": "nombre_nativo",
    "q7_sexo":          "sexo",
    "q8_civil":         "estado_civil",
    "q9_dob":           "fecha_nacimiento",
    "q10_ciudad_nac":   "ciudad_nacimiento",
    "q11_prov_nac":     "provincia_nacimiento",
    "q12_pais_nac":     "pais_nacimiento",
    "q13_nacionalidad": "pais_nacionalidad",
    "q20_cedula":       "numero_id_tributario",
    "q21_ssn":          "ssn",
    "q22_tin":          "tin",
    "q23_dir1":         "direccion_rd",
    "q25_ciudad":       "ciudad_rd",
    "q26_provincia":    "provincia_rd",
    "q27_postal":       "codigo_postal",
    "q28_pais_res":     "pais_residencia",
    "q33_tel":          "telefono_principal",
    "q34_tel2":         "telefono_secundario",
    "q35_tel_trab":     "telefono_trabajo",
    "q36_email":        "email",
    "q38_red1":         "red_social_1",
    "q39_user1":        "usuario_red_1",
    "q40_red2":         "red_social_2",
    "q41_user2":        "usuario_red_2",
    "q42_tipo_pas":     "tipo_pasaporte",
    "q43_numpas":       "numero_pasaporte",
    "q44_libreta":      "libreta_pasaporte",
    "q45_pais_pas":     "pais_emisor_pasaporte",
    "q46_ciudad_emision": "ciudad_emision_pasaporte",
    "q48_emision":      "fecha_emision_pasaporte",
    "q49_vence":        "fecha_vencimiento_pasaporte",
    "q55_proposito":    "proposito_viaje",
    "q56_planes":       "tiene_planes",
    "q57_llegada":      "fecha_llegada",
    "q60_salida":       "fecha_salida",
    "q63_llegada_est":  "fecha_llegada_estimada",
    "q64_duracion":     "duracion_estancia",
    "q65_dir_hospedaje":"itinerario",
    "q66_ciudad_hosp":  "ciudad_eeuu",
    "q67_estado_hosp":  "estado_eeuu",
    "q68_paga":         "paga_viaje",
    "q76_compan":       "viaja_acompanado",
    "q82_estuvo":       "viajo_antes_eeuu",
    "q83_fecha_vis1":   "fecha_visita_1",
    "q84_dur_vis1":     "duracion_visita_1",
    "q87_visa_prev":    "visa_previa",
    "q88_visa_emision": "fecha_visa_previa",
    "q89_visa_num":     "numero_visa_previa",
    "q93_negacion":     "visa_negada_antes",
    "q94_negacion_donde": "donde_negaron",
    "q95_razon_neg":    "detalle_visa_negada",
    "q96_peticion":     "peticion_inmigracion",
    "q98_cont_ap":      "apellido_contacto_eeuu",
    "q99_cont_nom":     "nombre_contacto_eeuu",
    "q100_cont_org":    "organizacion_contacto",
    "q101_cont_rel":    "relacion_contacto_eeuu",
    "q102_cont_dir":    "direccion_eeuu",
    "q103_cont_ciudad": "ciudad_contacto_eeuu",
    "q104_cont_estado": "estado_contacto_eeuu",
    "q105_cont_zip":    "zip_eeuu",
    "q106_cont_tel":    "telefono_contacto_eeuu",
    "q107_cont_email":  "email_contacto",
    "q108_padre_ap":    "apellido_padre",
    "q109_padre_nom":   "nombre_padre",
    "q110_padre_dob":   "fecha_nac_padre",
    "q113_madre_ap":    "apellido_madre",
    "q114_madre_nom":   "nombre_madre",
    "q115_madre_dob":   "fecha_nac_madre",
    "q119_fam1_ap":     "apellido_familiar_eeuu",
    "q120_fam1_nom":    "nombre_familiar_eeuu",
    "q121_fam1_rel":    "relacion_familiar_eeuu",
    "q122_fam1_estatus":"estatus_familiar_eeuu",
    "q125_con_ap":      "apellido_conyuge",
    "q126_con_nom":     "nombre_conyuge",
    "q127_con_dob":     "fecha_nac_conyuge",
    "q128_con_pais_nac":"pais_nac_conyuge",
    "q129_con_ciudadania":"ciudadania_conyuge",
    "q130_con_dir":     "direccion_conyuge",
    "q131_ocupacion":   "ocupacion_actual",
    "q132_empleador":   "empleador_actual",
    "q133_dir_emp1":    "direccion_empleador",
    "q134_emp_ciudad":  "ciudad_empleador",
    "q136_emp_pais":    "pais_empleador",
    "q138_emp_tel":     "telefono_empleador",
    "q139_emp_inicio":  "fecha_inicio_trabajo",
    "q140_salario":     "salario_mensual",
    "q141_funciones":   "descripcion_trabajo",
    "q143_emp_ant_nom": "empleador_anterior",
    "q146_cargo_ant":   "cargo_anterior",
    "q147_inicio_ant":  "inicio_empleo_anterior",
    "q148_fin_ant":     "fin_empleo_anterior",
    "q149_func_ant":    "funciones_anteriores",
    "q152_escuela":     "nombre_institucion",
    "q153_escuela_dir": "direccion_institucion",
    "q154_carrera":     "nivel_educacion",
    "q155_edu_inicio":  "inicio_estudios",
    "q156_edu_fin":     "fin_estudios",
    "q159_paises":      "paises_visitados",
    "q160_idiomas":     "idiomas",
    "q162_org_nom":     "nombre_organizacion",
    "q164_habilidades_exp": "detalle_habilidades",
    "q166_mil_pais":    "pais_servicio_militar",
    "q167_mil_rama":    "rama_militar",
    "q168_mil_rango":   "rango_militar",
    "q174":             "enfermedad_comunicable",
    "q175":             "trastorno_mental",
    "q176":             "adiccion_drogas",
    "q177":             "arrestado",
    "q178_arresto":     "detalle_arresto",
    "q185":             "deportado_alguna_vez",
    "q187":             "actividad_terrorista",
    "q199":             "presente_eeuu_sin_permiso",
    "q208_ca1_ap":      "contacto_adicional_1_apellido",
    "q209_ca1_nom":     "contacto_adicional_1_nombre",
    "q210_ca1_tel":     "contacto_adicional_1_telefono",
    "q211_ca1_email":   "contacto_adicional_1_email",
    "q212_ca2_ap":      "contacto_adicional_2_apellido",
    "q213_ca2_nom":     "contacto_adicional_2_nombre",
    "q214_ca2_tel":     "contacto_adicional_2_telefono",
    "q215_ca2_email":   "contacto_adicional_2_email",
    "q223_asist_ap":    "apellido_asistente",
    "q224_asist_nom":   "nombre_asistente",
    "q225_asist_org":   "organizacion_asistente",
    "q226_asist_dir":   "direccion_asistente",
    "q227_asist_tel":   "telefono_asistente",
}

# ── ORDEN OFICIAL CEAC (q1 → q227) ──────────────────────────────────────────
ORDER = [
    "q1_apellido","q2_nombre","q3_otros_nombres","q4_otro_apellido","q5_otro_nombre",
    "q6_nombre_nativo","q7_sexo","q8_civil","q9_dob","q10_ciudad_nac","q11_prov_nac",
    "q12_pais_nac","q13_nacionalidad","q14_otra_nac","q15_otra_nac_pais",
    "q16_pas_otra_nac","q17_pas_otro","q18_emision_otro","q19_vence_otro",
    "q20_cedula","q21_ssn","q22_tin",
    "q23_dir1","q24_dir2","q25_ciudad","q26_provincia","q27_postal","q28_pais_res",
    "q29_dir_ant","q30_dir_ant","q31_ciudad_ant","q32_pais_ant",
    "q33_tel","q34_tel2","q35_tel_trab","q36_email",
    "q37_redes","q38_red1","q39_user1","q40_red2","q41_user2",
    "q42_tipo_pas","q43_numpas","q44_libreta","q45_pais_pas",
    "q46_ciudad_emision","q47_prov_emision","q48_emision","q49_vence",
    "q50_perdio_pas","q51_pas_perdido","q52_pais_pas_perdido","q53_explicacion_perdido",
    "q54_solicitante","q55_proposito","q56_planes",
    "q57_llegada","q58_vuelo_lleg","q59_ciudad_lleg",
    "q60_salida","q61_vuelo_sal","q62_ciudad_sal","q63_llegada_est",
    "q64_duracion","q65_dir_hospedaje","q66_ciudad_hosp","q67_estado_hosp",
    "q68_paga","q69_pat_apellido","q70_pat_nombre","q71_pat_tel",
    "q72_pat_email","q73_pat_relacion","q74_empresa_pat","q75_dir_empresa",
    "q76_compan","q77_grupo","q78_grupo_nom",
    "q79_comp1_ap","q80_comp1_nom","q81_comp1_rel",
    "q82_estuvo","q83_fecha_vis1","q84_dur_vis1","q85_fecha_vis2","q86_dur_vis2",
    "q87_visa_prev","q88_visa_emision","q89_visa_num",
    "q90_mismo_tipo","q91_mismo_pais","q92_diez_anos",
    "q93_negacion","q94_negacion_donde","q95_razon_neg",
    "q96_peticion","q97_peticion_exp",
    "q98_cont_ap","q99_cont_nom","q100_cont_org","q101_cont_rel",
    "q102_cont_dir","q103_cont_ciudad","q104_cont_estado","q105_cont_zip",
    "q106_cont_tel","q107_cont_email",
    "q108_padre_ap","q109_padre_nom","q110_padre_dob","q111_padre_eeuu","q112_padre_estatus",
    "q113_madre_ap","q114_madre_nom","q115_madre_dob","q116_madre_eeuu","q117_madre_estatus",
    "q118_fam_inm","q119_fam1_ap","q120_fam1_nom","q121_fam1_rel","q122_fam1_estatus",
    "q123_otros_fam","q124_otros_fam_exp",
    "q125_con_ap","q126_con_nom","q127_con_dob","q128_con_pais_nac",
    "q129_con_ciudadania","q130_con_dir",
    "q131_ocupacion","q132_empleador","q133_dir_emp1","q134_emp_ciudad",
    "q135_emp_prov","q136_emp_pais","q137_emp_postal","q138_emp_tel",
    "q139_emp_inicio","q140_salario","q141_funciones",
    "q142_emp_ant","q143_emp_ant_nom","q144_dir_emp_ant","q145_tel_emp_ant",
    "q146_cargo_ant","q147_inicio_ant","q148_fin_ant","q149_func_ant",
    "q151_edu","q152_escuela","q153_escuela_dir","q154_carrera",
    "q155_edu_inicio","q156_edu_fin",
    "q157_clan","q158_clan_nom",
    "q159_paises","q160_idiomas",
    "q161_org","q162_org_nom",
    "q163_habilidades","q164_habilidades_exp",
    "q165_militar","q166_mil_pais","q167_mil_rama","q168_mil_rango",
    "q169_mil_esp","q170_mil_inicio","q171_mil_fin",
    "q172_paramilitar","q173_paramilitar_exp",
    "q174","q175","q176",
    "q177","q178_arresto",
    "q179","q180",
    "q181","q182",
    "q183","q184",
    "q185","q186",
    "q187","q188",
    "q189","q190",
    "q191","q192",
    "q193","q194",
    "q195","q196",
    "q197","q198",
    "q199","q200",
    "q201","q202",
    "q203",
    "q204","q205",
    "q206","q207",
    "q208_ca1_ap","q209_ca1_nom","q210_ca1_tel","q211_ca1_email",
    "q212_ca2_ap","q213_ca2_nom","q214_ca2_tel","q215_ca2_email",
    "q222_asistido","q223_asist_ap","q224_asist_nom",
    "q225_asist_org","q226_asist_dir","q227_asist_tel",
]

# ── LABELS CEAC en español e inglés ─────────────────────────────────────────
LABELS = {
    "q1_apellido":       {"es":"Apellido(s)","en":"Surname"},
    "q2_nombre":         {"es":"Nombre(s)","en":"Given Names"},
    "q3_otros_nombres":  {"es":"¿Ha usado otros nombres?","en":"Other Names Used"},
    "q4_otro_apellido":  {"es":"Apellido anterior","en":"Other Surname"},
    "q5_otro_nombre":    {"es":"Nombre anterior","en":"Other Given Names"},
    "q6_nombre_nativo":  {"es":"Nombre en alfabeto nativo","en":"Full Name in Native Alphabet"},
    "q7_sexo":           {"es":"Sexo","en":"Sex"},
    "q8_civil":          {"es":"Estado civil","en":"Marital Status"},
    "q9_dob":            {"es":"Fecha de nacimiento","en":"Date of Birth"},
    "q10_ciudad_nac":    {"es":"Ciudad de nacimiento","en":"City of Birth"},
    "q11_prov_nac":      {"es":"Provincia de nacimiento","en":"State/Province of Birth"},
    "q12_pais_nac":      {"es":"País de nacimiento","en":"Country of Birth"},
    "q13_nacionalidad":  {"es":"Nacionalidad","en":"Nationality"},
    "q14_otra_nac":      {"es":"¿Tiene otra nacionalidad?","en":"Other Nationality"},
    "q20_cedula":        {"es":"Cédula / ID Nacional","en":"National ID Number"},
    "q21_ssn":           {"es":"Seguro Social EE.UU.","en":"U.S. Social Security Number"},
    "q22_tin":           {"es":"Contribuyente EE.UU.","en":"U.S. Taxpayer ID"},
    "q23_dir1":          {"es":"Dirección línea 1","en":"Home Address Line 1"},
    "q24_dir2":          {"es":"Dirección línea 2","en":"Home Address Line 2"},
    "q25_ciudad":        {"es":"Ciudad","en":"City"},
    "q26_provincia":     {"es":"Provincia","en":"State/Province"},
    "q27_postal":        {"es":"Código postal","en":"ZIP/Postal Code"},
    "q28_pais_res":      {"es":"País de residencia","en":"Country of Residence"},
    "q33_tel":           {"es":"Teléfono principal","en":"Primary Phone"},
    "q34_tel2":          {"es":"Teléfono secundario","en":"Secondary Phone"},
    "q35_tel_trab":      {"es":"Teléfono trabajo","en":"Work Phone"},
    "q36_email":         {"es":"Correo electrónico","en":"Email Address"},
    "q37_redes":         {"es":"¿Tiene redes sociales?","en":"Social Media Presence"},
    "q38_red1":          {"es":"Red social 1","en":"Social Media Platform 1"},
    "q39_user1":         {"es":"Usuario red 1","en":"Social Media Handle 1"},
    "q42_tipo_pas":      {"es":"Tipo de pasaporte","en":"Passport Type"},
    "q43_numpas":        {"es":"Número de pasaporte","en":"Passport Number"},
    "q45_pais_pas":      {"es":"País emisor pasaporte","en":"Passport Issuing Country"},
    "q46_ciudad_emision":{"es":"Ciudad de emisión","en":"City of Issuance"},
    "q48_emision":       {"es":"Fecha de expedición","en":"Issuance Date"},
    "q49_vence":         {"es":"Fecha de vencimiento","en":"Expiration Date"},
    "q50_perdio_pas":    {"es":"¿Perdió pasaporte?","en":"Lost/Stolen Passport"},
    "q55_proposito":     {"es":"Propósito del viaje","en":"Purpose of Trip"},
    "q56_planes":        {"es":"¿Tiene planes fijos?","en":"Specific Travel Plans"},
    "q57_llegada":       {"es":"Fecha de llegada","en":"Intended Arrival Date"},
    "q60_salida":        {"es":"Fecha de salida","en":"Intended Departure Date"},
    "q63_llegada_est":   {"es":"Fecha llegada estimada","en":"Estimated Arrival Date"},
    "q64_duracion":      {"es":"Duración de la estadía","en":"Intended Length of Stay"},
    "q65_dir_hospedaje": {"es":"Dirección de hospedaje","en":"U.S. Address Where Staying"},
    "q66_ciudad_hosp":   {"es":"Ciudad de hospedaje","en":"U.S. City"},
    "q67_estado_hosp":   {"es":"Estado de hospedaje","en":"U.S. State"},
    "q68_paga":          {"es":"¿Quién paga el viaje?","en":"Who Is Paying for Your Trip"},
    "q76_compan":        {"es":"¿Viaja acompañado?","en":"Traveling with Others"},
    "q82_estuvo":        {"es":"¿Ha estado en EE.UU.?","en":"Previously in U.S."},
    "q87_visa_prev":     {"es":"¿Tiene visa anterior?","en":"Previously Issued U.S. Visa"},
    "q88_visa_emision":  {"es":"Fecha visa anterior","en":"Last Visa Issue Date"},
    "q89_visa_num":      {"es":"Número visa anterior","en":"Last Visa Number"},
    "q93_negacion":      {"es":"¿Le negaron visa?","en":"U.S. Visa Refused"},
    "q94_negacion_donde":{"es":"¿Dónde y cuándo?","en":"Refusal Location & Year"},
    "q95_razon_neg":     {"es":"Razón de la negación","en":"Reason for Refusal"},
    "q96_peticion":      {"es":"¿Petición USCIS?","en":"Immigrant Petition Filed"},
    "q98_cont_ap":       {"es":"Apellido contacto EE.UU.","en":"U.S. Contact Surname"},
    "q99_cont_nom":      {"es":"Nombre contacto EE.UU.","en":"U.S. Contact Given Names"},
    "q100_cont_org":     {"es":"Organización contacto","en":"U.S. Contact Organization"},
    "q101_cont_rel":     {"es":"Relación con contacto","en":"Relationship to You"},
    "q102_cont_dir":     {"es":"Dirección contacto","en":"U.S. Contact Address"},
    "q103_cont_ciudad":  {"es":"Ciudad contacto","en":"U.S. Contact City"},
    "q104_cont_estado":  {"es":"Estado contacto","en":"U.S. Contact State"},
    "q105_cont_zip":     {"es":"ZIP contacto","en":"U.S. Contact ZIP"},
    "q106_cont_tel":     {"es":"Teléfono contacto","en":"U.S. Contact Phone"},
    "q107_cont_email":   {"es":"Email contacto","en":"U.S. Contact Email"},
    "q108_padre_ap":     {"es":"Apellido del padre","en":"Father's Surname"},
    "q109_padre_nom":    {"es":"Nombre del padre","en":"Father's Given Names"},
    "q110_padre_dob":    {"es":"Fecha nacimiento padre","en":"Father's Date of Birth"},
    "q111_padre_eeuu":   {"es":"¿Padre en EE.UU.?","en":"Father in U.S."},
    "q113_madre_ap":     {"es":"Apellido de la madre","en":"Mother's Surname"},
    "q114_madre_nom":    {"es":"Nombre de la madre","en":"Mother's Given Names"},
    "q115_madre_dob":    {"es":"Fecha nacimiento madre","en":"Mother's Date of Birth"},
    "q116_madre_eeuu":   {"es":"¿Madre en EE.UU.?","en":"Mother in U.S."},
    "q118_fam_inm":      {"es":"¿Familiares inmigrantes?","en":"Immediate Relatives in U.S."},
    "q119_fam1_ap":      {"es":"Apellido familiar EE.UU.","en":"Relative 1 Surname"},
    "q120_fam1_nom":     {"es":"Nombre familiar EE.UU.","en":"Relative 1 Given Names"},
    "q121_fam1_rel":     {"es":"Relación familiar","en":"Relative 1 Relationship"},
    "q122_fam1_estatus": {"es":"Estatus familiar EE.UU.","en":"Relative 1 U.S. Status"},
    "q123_otros_fam":    {"es":"¿Otros familiares EE.UU.?","en":"Other Relatives in U.S."},
    "q124_otros_fam_exp":{"es":"Detalle otros familiares","en":"Other Relatives Explanation"},
    "q125_con_ap":       {"es":"Apellido cónyuge","en":"Spouse Surname"},
    "q126_con_nom":      {"es":"Nombre cónyuge","en":"Spouse Given Names"},
    "q127_con_dob":      {"es":"Fecha nacimiento cónyuge","en":"Spouse Date of Birth"},
    "q128_con_pais_nac": {"es":"País nacimiento cónyuge","en":"Spouse Country of Birth"},
    "q131_ocupacion":    {"es":"Ocupación actual","en":"Primary Occupation"},
    "q132_empleador":    {"es":"Empleador/Institución","en":"Employer/School Name"},
    "q133_dir_emp1":     {"es":"Dirección empleador","en":"Employer Address"},
    "q134_emp_ciudad":   {"es":"Ciudad empleador","en":"Employer City"},
    "q136_emp_pais":     {"es":"País empleador","en":"Employer Country"},
    "q138_emp_tel":      {"es":"Teléfono empleador","en":"Employer Phone"},
    "q139_emp_inicio":   {"es":"Fecha inicio empleo","en":"Employment Start Date"},
    "q140_salario":      {"es":"Salario mensual","en":"Monthly Salary"},
    "q141_funciones":    {"es":"Descripción de funciones","en":"Describe Your Duties"},
    "q142_emp_ant":      {"es":"¿Empleo anterior?","en":"Previously Employed"},
    "q143_emp_ant_nom":  {"es":"Empleador anterior","en":"Previous Employer Name"},
    "q146_cargo_ant":    {"es":"Cargo anterior","en":"Previous Job Title"},
    "q147_inicio_ant":   {"es":"Inicio empleo anterior","en":"Previous Job Start Date"},
    "q148_fin_ant":      {"es":"Fin empleo anterior","en":"Previous Job End Date"},
    "q149_func_ant":     {"es":"Funciones anteriores","en":"Previous Job Duties"},
    "q151_edu":          {"es":"¿Estudió educación superior?","en":"Attended Educational Institutions"},
    "q152_escuela":      {"es":"Institución educativa","en":"School Name"},
    "q153_escuela_dir":  {"es":"Dirección institución","en":"School Address"},
    "q154_carrera":      {"es":"Carrera/Programa","en":"Course of Study"},
    "q155_edu_inicio":   {"es":"Inicio estudios","en":"School Start Date"},
    "q156_edu_fin":      {"es":"Fin estudios","en":"School End Date"},
    "q159_paises":       {"es":"Países visitados (5 años)","en":"Countries Visited Last 5 Years"},
    "q160_idiomas":      {"es":"Idiomas que habla","en":"Languages Spoken"},
    "q161_org":          {"es":"¿Pertenece a organizaciones?","en":"Professional/Social Orgs"},
    "q162_org_nom":      {"es":"Nombre de organizaciones","en":"Organization Names"},
    "q163_habilidades":  {"es":"¿Habilidades especiales?","en":"Specialized Skills"},
    "q165_militar":      {"es":"¿Sirvió en el ejército?","en":"Military Service"},
    "q172_paramilitar":  {"es":"¿Grupos paramilitares?","en":"Paramilitary Groups"},
    "q174":              {"es":"Enfermedad comunicable","en":"Communicable Disease"},
    "q175":              {"es":"Trastorno mental/físico","en":"Mental/Physical Disorder"},
    "q176":              {"es":"Adicción a drogas","en":"Drug Addiction"},
    "q177":              {"es":"¿Arrestado alguna vez?","en":"Arrested/Convicted"},
    "q178_arresto":      {"es":"Detalle arresto","en":"Criminal Explanation"},
    "q179":              {"es":"Tráfico de drogas","en":"Drug Trafficking"},
    "q181":              {"es":"Prostitución","en":"Prostitution/Procuring"},
    "q183":              {"es":"Delitos de turpitud moral","en":"Crimes of Moral Turpitude"},
    "q185":              {"es":"Deportado de EE.UU.","en":"Excluded/Deported from U.S."},
    "q186":              {"es":"Detalle deportación","en":"Deportation Explanation"},
    "q187":              {"es":"Terrorismo/Espionaje","en":"Terrorism/Espionage"},
    "q188":              {"es":"Detalle terrorismo","en":"Terrorism Explanation"},
    "q189":              {"es":"Apoyo financiero terrorismo","en":"Terrorist Support"},
    "q191":              {"es":"Partido comunista","en":"Communist/Totalitarian Party"},
    "q193":              {"es":"Genocidio","en":"Genocide/Crimes Against Humanity"},
    "q195":              {"es":"Tortura/ejecuciones","en":"Torture/Extrajudicial Killing"},
    "q197":              {"es":"Reclutamiento menores","en":"Child Soldier Recruitment"},
    "q199":              {"es":"Sobreestadía EE.UU.","en":"Overstay U.S."},
    "q200":              {"es":"Detalle sobreestadía","en":"Overstay Explanation"},
    "q201":              {"es":"Fraude de visa","en":"Visa Fraud"},
    "q203":              {"es":"Renuncia ciudadanía USA","en":"U.S. Citizenship Renounced"},
    "q204":              {"es":"Custodia ilegal de menores","en":"Custodial Interference"},
    "q206":              {"es":"Voto ilegal EE.UU.","en":"Illegal Voting"},
    "q208_ca1_ap":       {"es":"Contacto adicional 1 — Apellidos","en":"Additional Contact 1 Surname"},
    "q209_ca1_nom":      {"es":"Contacto adicional 1 — Nombres","en":"Additional Contact 1 Given Names"},
    "q210_ca1_tel":      {"es":"Contacto adicional 1 — Teléfono","en":"Additional Contact 1 Phone"},
    "q211_ca1_email":    {"es":"Contacto adicional 1 — Email","en":"Additional Contact 1 Email"},
    "q212_ca2_ap":       {"es":"Contacto adicional 2 — Apellidos","en":"Additional Contact 2 Surname"},
    "q213_ca2_nom":      {"es":"Contacto adicional 2 — Nombres","en":"Additional Contact 2 Given Names"},
    "q214_ca2_tel":      {"es":"Contacto adicional 2 — Teléfono","en":"Additional Contact 2 Phone"},
    "q215_ca2_email":    {"es":"Contacto adicional 2 — Email","en":"Additional Contact 2 Email"},
    "q222_asistido":     {"es":"¿Asistido por tercero?","en":"Third-Party Assistance"},
    "q223_asist_ap":     {"es":"Apellido del asistente","en":"Preparer Surname"},
    "q224_asist_nom":    {"es":"Nombre del asistente","en":"Preparer Given Names"},
    "q225_asist_org":    {"es":"Organización del asistente","en":"Preparer Organization"},
    "q226_asist_dir":    {"es":"Dirección del asistente","en":"Preparer Address"},
    "q227_asist_tel":    {"es":"Teléfono del asistente","en":"Preparer Phone"},
}

OUT_DIR = '/var/www/crm/ds160/exports'
os.makedirs(OUT_DIR, exist_ok=True)


def get_val(datos, campo):
    """Busca el valor de un campo en múltiples fuentes."""
    # 1. Directo por clave qXXX
    v = datos.get(campo)
    if v and str(v).strip() and str(v) not in ['null','None','nan']: return v

    # 2. Por LEGACY map
    if campo in LEGACY:
        v = datos.get(LEGACY[campo])
        if v and str(v).strip() and str(v) not in ['null','None','nan']: return v

    # 3. Por base del campo (qXX_base → base)
    base = re.sub(r'^q\d+_', '', campo)
    if base and base != campo:
        v = datos.get(base)
        if v and str(v).strip() and str(v) not in ['null','None','nan']: return v

    return None


def normalizar(v):
    """Normaliza valores para CEAC."""
    if v is None: return None
    if isinstance(v, bool): return "YES" if v else "NO"
    s = str(v).strip()
    if not s or s in ['null','None','nan','']: return None
    # Normalizar YES/NO
    if s.lower() in ['si','sí','yes','true','1']: return "YES"
    if s.lower() in ['no','false','0']: return "NO"
    # Normalizar DNA
    if s.lower() in ['does not apply','dna','n/a','na']: return "Does Not Apply"
    return s


def export_caso(rec):
    datos = rec.get('datos') or {}
    fields = {}
    labels_out = {}

    for k in ORDER:
        v = get_val(datos, k)
        v_norm = normalizar(v)
        fields[k] = v_norm
        if k in LABELS:
            labels_out[k] = {
                "es": LABELS[k]["es"],
                "en": LABELS[k]["en"],
                "value": v_norm
            }

    filled = sum(1 for v in fields.values() if v)
    nombre   = datos.get('q2_nombre','') or datos.get('nombre','')
    apellido = datos.get('q1_apellido','') or datos.get('apellido_primario','')
    email    = datos.get('q36_email','') or datos.get('email','caso')
    pasaporte= datos.get('q43_numpas','') or datos.get('numero_pasaporte','')

    # Campos críticos faltantes
    CRITICOS = [
        'q1_apellido','q2_nombre','q7_sexo','q8_civil','q9_dob',
        'q12_pais_nac','q13_nacionalidad','q20_cedula','q23_dir1',
        'q25_ciudad','q33_tel','q36_email','q42_tipo_pas','q43_numpas',
        'q45_pais_pas','q46_ciudad_emision','q48_emision','q49_vence',
        'q55_proposito','q64_duracion','q65_dir_hospedaje',
        'q66_ciudad_hosp','q67_estado_hosp',
        'q98_cont_ap','q99_cont_nom','q101_cont_rel','q102_cont_dir',
        'q103_cont_ciudad','q104_cont_estado','q105_cont_zip','q106_cont_tel',
        'q108_padre_ap','q109_padre_nom','q113_madre_ap','q114_madre_nom',
        'q131_ocupacion','q132_empleador','q141_funciones','q160_idiomas',
    ]
    criticos_faltantes = [k for k in CRITICOS if not fields.get(k)]

    export = {
        "meta": {
            "caso_id":            rec['id'],
            "email":              email,
            "nombre":             nombre,
            "apellido":           apellido,
            "pasaporte":          pasaporte,
            "advisor_notes":      rec.get('revision_notas','') or '',
            "generated_by":       "TengoVisaRD CRM",
            "generated_at":       datetime.now().isoformat(),
            "form_version":       "DS-160-2025",
            "embassy":            "Santo Domingo, Dominican Republic",
            "total_fields":       len(ORDER),
            "filled_fields":      filled,
            "completeness_pct":   round((filled / len(ORDER)) * 100),
            "criticos_faltantes": criticos_faltantes,
            "criticos_completos": len(CRITICOS) - len(criticos_faltantes),
            "criticos_total":     len(CRITICOS),
        },
        "fields": fields,
        "fields_labeled": labels_out,
    }

    safe  = email.replace('@','_').replace('.','_')
    fname = f"{OUT_DIR}/ds160_{safe}_{rec['id'][:8]}.json"
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    return fname, filled, nombre, apellido, criticos_faltantes


# ── MAIN ──────────────────────────────────────────────────────────────────────
caso_id = sys.argv[1] if len(sys.argv) > 1 else 'all'

if caso_id == 'all':
    recs = sb.schema('crm').table('ds160_casos').select('*').order('created_at', desc=True).execute().data
else:
    recs = sb.schema('crm').table('ds160_casos').select('*').eq('id', caso_id).execute().data

if not recs:
    print("No se encontraron registros")
    sys.exit(1)

for rec in recs:
    fname, filled, nombre, apellido, faltantes = export_caso(rec)
    pct = round((filled / len(ORDER)) * 100)
    print(f"✓ {nombre} {apellido}")
    print(f"  Archivo : {fname}")
    print(f"  Campos  : {filled}/{len(ORDER)} ({pct}%)")
    if faltantes:
        print(f"  ⚠️  Críticos faltantes ({len(faltantes)}): {', '.join(faltantes[:5])}{'...' if len(faltantes)>5 else ''}")
    print()

print(f"Exports en: {OUT_DIR}/")
