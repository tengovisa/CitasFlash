
const API='/api',KEY='TengoVisa2026API';
const hdr=()=>({'x-api-key':KEY,'Content-Type':'application/json'});
const S={ds160:[],evals:[],ge:[],tab:'dash',CID:null,CA:null,CEval:null,CGE:null,charts:{}};

// ─── GEO ─────────────────────────────────────────────────
const PROVS=['AZUA','BAHORUCO','BARAHONA','DAJABÓN','DISTRITO NACIONAL','DUARTE','EL SEIBO','ELÍAS PIÑA','ESPAILLAT','HATO MAYOR','HERMANAS MIRABAL','INDEPENDENCIA','LA ALTAGRACIA','LA ROMANA','LA VEGA','MARÍA TRINIDAD SÁNCHEZ','MONSEÑOR NOUEL','MONTE CRISTI','MONTE PLATA','PEDERNALES','PERAVIA','PUERTO PLATA','SAMANÁ','SAN CRISTÓBAL','SAN JOSÉ DE OCOA','SAN JUAN','SAN PEDRO DE MACORÍS','SÁNCHEZ RAMÍREZ','SANTIAGO','SANTIAGO RODRÍGUEZ','SANTO DOMINGO','VALVERDE'];
const CITIES=['SANTO DOMINGO','SANTIAGO','LA ROMANA','SAN PEDRO DE MACORÍS','PUERTO PLATA','LA VEGA','SAN FRANCISCO DE MACORÍS','BARAHONA','MOCA','BONAO','HIGÜEY','AZUA','BANÍ','SAN JUAN DE LA MAGUANA','ENRIQUILLO','MONTE PLATA','COTUÍ','NAGUA','SAMANÁ','MONTE CRISTI','PEDERNALES','BOCA CHICA','SAN CRISTÓBAL','HATO MAYOR','VILLA ALTAGRACIA','NEYBA','JIMANÍ','DAJABÓN'];
const PAISES=['REPÚBLICA DOMINICANA','ESTADOS UNIDOS DE AMERICA','CANADA','ESPAÑA','ITALIA','FRANCE','ALEMANIA','REINO UNIDO','HAITÍ','CUBA','VENEZUELA','COLOMBIA','MEXICO','BRASIL','ARGENTINA','CHILE','PERÚ','ECUADOR','PANAMA','CHINA','JAPÓN','INDIA','AUSTRALIA','COSTA RICA','GUATEMALA'];
const ESTADOS_US=['ALABAMA','ALASKA','ARIZONA','ARKANSAS','CALIFORNIA','COLORADO','CONNECTICUT','DELAWARE','FLORIDA','GEORGIA','HAWAII','IDAHO','ILLINOIS','INDIANA','IOWA','KANSAS','KENTUCKY','LOUISIANA','MAINE','MARYLAND','MASSACHUSETTS','MICHIGAN','MINNESOTA','MISSISSIPPI','MISSOURI','MONTANA','NEBRASKA','NEVADA','NEW HAMPSHIRE','NEW JERSEY','NEW MEXICO','NEW YORK','NORTH CAROLINA','NORTH DAKOTA','OHIO','OKLAHOMA','OREGON','PENNSYLVANIA','RHODE ISLAND','SOUTH CAROLINA','SOUTH DAKOTA','TENNESSEE','TEXAS','UTAH','VERMONT','VIRGINIA','WASHINGTON','WEST VIRGINIA','WISCONSIN','WYOMING'];

// ─── MAPEO DUAL ESQUEMA ──────────────────────────────────
const MAP={
  apellido:['q1_apellido','apellido_primario'],nombre:['q2_nombre','nombre'],
  sexo:['q7_sexo','sexo'],civil:['q8_civil','estado_civil'],
  dob:['q9_dob','fecha_nacimiento'],ciudad_nac:['q10_ciudad_nac','ciudad_nacimiento'],
  pais_nac:['q12_pais_nac','pais_nacimiento'],nacionalidad:['q13_nacionalidad','pais_nacionalidad'],
  otra_nac:['q14_otra_nac','tiene_doble_nac'],cedula:['q20_cedula','numero_id_tributario'],
  ssn:['q21_ssn'],tin:['q22_tin'],dir1:['q23_dir1','direccion_rd'],
  ciudad:['q25_ciudad','ciudad_rd'],provincia:['q26_provincia','provincia_rd'],
  pais_res:['q28_pais_res'],tel:['q33_tel','telefono_principal'],
  tel2:['q34_tel2','telefono_adicional'],tel_trab:['q35_tel_trab'],email:['email'],
  red1:['q38_red1','redes_sociales'],tipo_pas:['q42_tipo_pas','tipo_pasaporte'],
  numpas:['q43_numpas','numero_pasaporte'],libreta:['q44_libreta'],
  pais_pas:['q45_pais_pas','pais_emisor_pasaporte'],ciudad_emision:['q46_ciudad_emision'],
  emision:['q48_emision','fecha_emision_pasaporte'],vence:['q49_vence','fecha_vencimiento_pasaporte'],
  perdio_pas:['q50_perdio_pas'],proposito:['q55_proposito','proposito_viaje'],
  planes:['q56_planes'],llegada:['q57_llegada','fecha_llegada_prevista'],
  duracion:['q64_duracion','duracion_estancia'],hosp_dir:['q65_dir_hospedaje','direccion_eeuu','itinerario'],
  hosp_ciudad:['q66_ciudad_hosp','ciudad_eeuu'],hosp_estado:['q67_estado_hosp','estado_eeuu'],
  paga:['q68_paga','paga_viaje'],compan:['q76_compan'],
  estuvo:['q82_estuvo','viajo_antes_eeuu'],visa_prev:['q87_visa_prev'],
  visa_num:['q89_visa_num'],negacion:['q93_negacion','visa_negada_antes'],
  razon_neg:['q95_razon_neg','detalle_visa_negada'],peticion:['q96_peticion'],
  cont_ap:['q98_cont_ap','nombre_contacto_eeuu'],cont_nom:['q99_cont_nom'],
  cont_org:['q100_cont_org'],cont_rel:['q101_cont_rel','relacion_contacto_eeuu'],
  cont_dir:['q102_cont_dir'],cont_ciudad:['q103_cont_ciudad','ciudad_eeuu'],
  cont_estado:['q104_cont_estado','estado_eeuu'],cont_zip:['q105_cont_zip','zip_eeuu'],
  cont_tel:['q106_cont_tel','telefono_contacto_eeuu'],cont_email:['q107_cont_email','email_contacto'],
  padre_ap:['q108_padre_ap','nombre_padre'],padre_nom:['q109_padre_nom'],
  padre_dob:['q110_padre_dob','fecha_nac_padre'],padre_eeuu:['q111_padre_eeuu'],
  madre_ap:['q113_madre_ap','nombre_madre'],madre_nom:['q114_madre_nom'],
  madre_dob:['q115_madre_dob','fecha_nac_madre'],madre_eeuu:['q116_madre_eeuu'],
  fam_inm:['q118_fam_inm'],con_ap:['q125_con_ap','nombre_conyuge'],con_nom:['q126_con_nom'],
  con_dob:['q127_con_dob','fecha_nac_conyuge'],con_pais_nac:['q128_con_pais_nac','pais_nac_conyuge'],
  ocupacion:['q131_ocupacion','ocupacion_actual'],empleador:['q132_empleador','empleador_actual'],
  dir_emp:['q133_dir_emp1','direccion_empleador'],ciudad_emp:['q134_emp_ciudad','ciudad_institucion'],
  tel_emp:['q138_emp_tel','telefono_empleador'],emp_inicio:['q139_emp_inicio','fecha_inicio_trabajo'],
  salario:['q140_salario'],funciones:['q141_funciones','descripcion_trabajo'],emp_ant:['q142_emp_ant'],
  edu:['q151_edu'],escuela:['q152_escuela','nombre_institucion'],
  carrera:['q154_carrera','nivel_educacion'],edu_inicio:['q155_edu_inicio'],edu_fin:['q156_edu_fin'],
  clan:['q157_clan'],paises_vis:['q159_paises'],idiomas:['q160_idiomas'],
  org:['q161_org'],habilidades:['q163_habilidades'],militar:['q165_militar'],
  paramilitar:['q172_paramilitar'],enfermedad:['q174','enfermedad_comunicable'],
  trastorno:['q175','trastorno_mental'],drogas:['q176','adiccion_drogas'],
  arrestado:['q177','arrestado'],trafico_drog:['q179','trafico_drogas'],
  prostitucion:['q181','prostitucion'],lavado:['q183','lavado_dinero'],
  deportado:['q185','deportado_alguna_vez'],terrorismo:['q187','actividad_terrorista'],
  overstay:['q199'],fraude_visa:['q201'],custodia:['q204'],voto_ilegal:['q206'],
  asistido:['q222_asistido'],nombre_nativo:['q6_nombre_nativo','apellido_nativo'],
};
function gm(d,c){for(const k of(MAP[c]||[c])){const v=d[k];if(v!==undefined&&v!==null&&String(v).trim()&&v!=='null'&&v!=='None')return String(v).trim();}return'';}
function realKey(c,d){for(const k of(MAP[c]||[c])){if(k in d)return k;}return(MAP[c]||[c])[0];}

// ─── FASES ───────────────────────────────────────────────
const FASES=[
  {id:'p1',icon:'👤',t:'P1 — Información Personal',campos:[
    ['Apellido(s)','apellido','tx'],['Nombre(s)','nombre','tx'],
    ['Sexo','sexo','sexo'],['Estado civil','civil','civil'],
    ['Fecha de nacimiento','dob','fecha'],['Ciudad de nacimiento','ciudad_nac','ciudad_rd'],
    ['País de nacimiento','pais_nac','pais'],['Nacionalidad','nacionalidad','pais'],
    ['Nombre nativo completo','nombre_nativo','tx'],
  ]},
  {id:'p2',icon:'📋',t:'P2 — Documentos de Identidad',campos:[
    ['¿Tiene otra nacionalidad?','otra_nac','sino'],
    ['Cédula / ID Nacional','cedula','cedula'],['SSN EE.UU.','ssn','dna'],['TIN EE.UU.','tin','dna'],
  ]},
  {id:'p3',icon:'🏠',t:'P3 — Dirección y Contacto',campos:[
    ['Dirección','dir1','tx'],['Ciudad','ciudad','ciudad_rd'],
    ['Provincia','provincia','prov_rd'],['País de residencia','pais_res','pais'],
    ['Teléfono principal','tel','tel'],['Teléfono secundario','tel2','tel'],
    ['Teléfono trabajo','tel_trab','dna'],['Email','email','email'],
    ['Redes sociales','red1','tx'],
  ]},
  {id:'p4',icon:'🛂',t:'P4 — Pasaporte',campos:[
    ['Tipo de pasaporte','tipo_pas','tipopas'],['Número de pasaporte','numpas','tx'],
    ['# Libreta','libreta','dna'],['País emisor','pais_pas','pais'],
    ['Ciudad de emisión','ciudad_emision','ciudad_rd'],
    ['Fecha de expedición','emision','fecha'],['Fecha de vencimiento','vence','fecha'],
    ['¿Perdió algún pasaporte?','perdio_pas','sino'],
  ]},
  {id:'p5',icon:'✈️',t:'P5 — Información del Viaje',campos:[
    ['Propósito del viaje','proposito','prop'],['¿Tiene planes fijos?','planes','sino'],
    ['Fecha de llegada prevista','llegada','fecha'],['Duración de la estadía','duracion','tx'],
    ['Dirección de hospedaje','hosp_dir','tx'],['Ciudad EE.UU.','hosp_ciudad','tx'],
    ['Estado EE.UU.','hosp_estado','estado_us'],['¿Quién paga el viaje?','paga','pagador'],
    ['¿Viaja acompañado?','compan','sino'],
  ]},
  {id:'p67',icon:'🗺️',t:'P6-P7 — Viajes Previos',campos:[
    ['¿Ha estado en EE.UU.?','estuvo','sino'],['¿Tiene visa anterior?','visa_prev','sino'],
    ['Número de visa anterior','visa_num','tx'],['¿Le negaron visa antes?','negacion','sino'],
    ['Razón de la negación','razon_neg','tx'],['¿Tiene petición USCIS?','peticion','sino'],
  ]},
  {id:'p8',icon:'📞',t:'P8 — Contacto en EE.UU.',campos:[
    ['Apellido del contacto','cont_ap','tx'],['Nombre del contacto','cont_nom','tx'],
    ['Organización','cont_org','dna'],['Relación con el contacto','cont_rel','relacion'],
    ['Dirección del contacto','cont_dir','tx'],['Ciudad','cont_ciudad','tx'],
    ['Estado','cont_estado','tx'],['ZIP Code','cont_zip','tx'],
    ['Teléfono del contacto','cont_tel','tel'],['Email del contacto','cont_email','email'],
  ]},
  {id:'p9a',icon:'👨‍👩‍👦',t:'P9A — Padre y Madre',campos:[
    ['Apellido del padre','padre_ap','tx'],['Nombre del padre','padre_nom','tx'],
    ['Fecha nac. padre','padre_dob','fecha'],['¿Padre vive en EE.UU.?','padre_eeuu','sino'],
    ['Apellido de la madre','madre_ap','tx'],['Nombre de la madre','madre_nom','tx'],
    ['Fecha nac. madre','madre_dob','fecha'],['¿Madre vive en EE.UU.?','madre_eeuu','sino'],
    ['¿Tiene familiares inmigrantes?','fam_inm','sino'],
  ]},
  {id:'p9b',icon:'💑',t:'P9B — Cónyuge',oculta:true,campos:[
    ['Apellido del cónyuge','con_ap','tx'],['Nombre del cónyuge','con_nom','tx'],
    ['Fecha de nac. del cónyuge','con_dob','fecha'],['País de nac. del cónyuge','con_pais_nac','pais'],
  ]},
  {id:'p10',icon:'💼',t:'P10 — Trabajo Actual',campos:[
    ['Ocupación principal','ocupacion','ocup'],['Nombre del empleador','empleador','tx'],
    ['Dirección del empleador','dir_emp','tx'],['Ciudad del empleador','ciudad_emp','tx'],
    ['Teléfono del empleador','tel_emp','tel'],['Fecha de inicio de empleo','emp_inicio','fecha'],
    ['Salario mensual (DOP)','salario','num'],['Descripción de funciones','funciones','area'],
    ['¿Tuvo empleo anterior?','emp_ant','sino'],
  ]},
  {id:'p1112',icon:'🎓',t:'P11-P12 — Educación e Info Adicional',campos:[
    ['¿Cursó estudios?','edu','sino'],['Institución educativa','escuela','tx'],
    ['Carrera / Programa','carrera','tx'],['Fecha inicio estudios','edu_inicio','fecha'],
    ['Fecha fin estudios','edu_fin','fecha'],['Idiomas que habla','idiomas','tx'],
    ['Países visitados','paises_vis','tx'],['¿Pertenece a organizaciones?','org','sino'],
    ['¿Tiene habilidades especiales?','habilidades','sino'],
    ['¿Sirvió en fuerzas militares?','militar','sino'],
    ['¿Perteneció a grupos paramilitares?','paramilitar','sino'],
  ]},
  {id:'p1314',icon:'🔐',t:'P13-P14 — Seguridad: Salud y Criminal',campos:[
    ['Enfermedad comunicable','enfermedad','sino'],['Trastorno mental','trastorno','sino'],
    ['Adicción a drogas','drogas','sino'],['Arrestado alguna vez','arrestado','sino'],
    ['Tráfico de drogas','trafico_drog','sino'],['Prostitución','prostitucion','sino'],
    ['Lavado de dinero','lavado','sino'],['Deportado de algún país','deportado','sino'],
  ]},
  {id:'p1516',icon:'🚨',t:'P15-P16 — Seguridad: Terrorismo y Otros',campos:[
    ['Actividad terrorista','terrorismo','sino'],['Overstay en EE.UU.','overstay','sino'],
    ['Fraude de visa','fraude_visa','sino'],['Custodia ilegal de menores','custodia','sino'],
    ['Votó ilegalmente en EE.UU.','voto_ilegal','sino'],
    ['¿Formulario preparado por otro?','asistido','sino'],
  ]},
];

const CREQ=['apellido','nombre','sexo','civil','dob','ciudad_nac','pais_nac','nacionalidad',
'cedula','dir1','ciudad','provincia','tel','email','tipo_pas','numpas','pais_pas',
'emision','vence','proposito','duracion','hosp_dir','hosp_ciudad','cont_ap','cont_rel',
'padre_ap','madre_ap','ocupacion','idiomas'];
const CLBLS={apellido:'Apellido',nombre:'Nombre',sexo:'Sexo',civil:'Estado civil',dob:'Fecha nac.',
ciudad_nac:'Ciudad nac.',pais_nac:'País nac.',nacionalidad:'Nacionalidad',cedula:'Cédula',
dir1:'Dirección',ciudad:'Ciudad',provincia:'Provincia',tel:'Teléfono',email:'Email',
tipo_pas:'Tipo pasaporte',numpas:'N° Pasaporte',pais_pas:'País emisor',emision:'Emisión pas.',
vence:'Vto. pasaporte',proposito:'Propósito',duracion:'Duración',hosp_dir:'Hospedaje',
hosp_ciudad:'Ciudad EE.UU.',cont_ap:'Contacto EE.UU.',cont_rel:'Relación contacto',
padre_ap:'Nombre padre',madre_ap:'Nombre madre',ocupacion:'Ocupación',idiomas:'Idiomas'};

const TPLS=[
  {id:'rec',ico:'✅',nm:'Solicitud recibida',
  txt:'Hola {nombre}! 👋\n\nHemos recibido tu solicitud DS-160. Tu caso es *{caso}*.\n\nNuestro equipo revisará tu información y te contactará pronto.\n\n_TengoVisaRD · tengovisard.com_'},
  {id:'pend',ico:'⚠️',nm:'Información pendiente',
  txt:'Hola {nombre}! 👋\n\nRevisando tu expediente notamos que faltan datos importantes:\n\n{faltantes}\n\nCompleta tu formulario aquí:\n👉 {link}\n\n_TengoVisaRD · tengovisard.com_'},
  {id:'comp',ico:'🎉',nm:'Formulario completo',
  txt:'Hola {nombre}! 🎉\n\nTu formulario DS-160 está *completo y listo*.\n\nPróximos pasos:\n1️⃣ Pago tarifa MRV\n2️⃣ Agendar entrevista consular\n3️⃣ Preparar documentos de soporte\n\n_TengoVisaRD · tengovisard.com_'},
  {id:'cita',ico:'📅',nm:'Cita programada',
  txt:'Hola {nombre}! 📅\n\n*Tu cita consular:*\n📍 Fecha: {fecha}\n📍 Hora: {hora}\n📍 Embajada EE.UU. Santo Domingo\n\n*Llevar:* Pasaporte · DS-160 · Foto 2x2 · Comprobante MRV\n\n_TengoVisaRD · tengovisard.com_'},
  {id:'apr',ico:'🎊',nm:'¡Visa aprobada!',
  txt:'Hola {nombre}! 🎊🇺🇸\n\n¡FELICIDADES! Tu visa *B1/B2* fue APROBADA! 🥳\n\nTu pasaporte estará listo en 3-5 días hábiles.\n\nFue un placer acompañarte. ¡Recomiéndanos!\n\n_TengoVisaRD · tengovisard.com_'},
  {id:'neg',ico:'😔',nm:'Resultado negativo',
  txt:'Hola {nombre},\n\nLamentablemente tu solicitud fue negada en esta ocasión.\n\nEsto no es el final. Podemos analizar tu caso y trabajar en las mejoras necesarias. ¿Te gustaría una consulta?\n\n_TengoVisaRD · tengovisard.com_'},
];

// ─── UTILIDADES ──────────────────────────────────────────
const esc=v=>v?String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'):'';
const up=v=>(v||'').toUpperCase();
const ini=nm=>(nm||'').split(' ').map(x=>x[0]||'').slice(0,2).join('').toUpperCase()||'?';
const pctC=p=>p>=80?'#16A34A':p>=50?'#F59E0B':'#E24B4A';
function calcPct(d){let ok=0;CREQ.forEach(c=>{if(gm(d,c))ok++;});return Math.round(ok/CREQ.length*100);}
function faltantes(d){return CREQ.filter(c=>!gm(d,c)).map(c=>CLBLS[c]||c);}
function isCasado(d){return['casado','casada','married','union libre'].includes((gm(d,'civil')||'').toLowerCase());}
function cleanNotas(raw){
  if(!raw)return'';const t=String(raw).trim();
  if(t.startsWith('{')){try{const p=JSON.parse(t);return p.notas_texto||p.notas||p.revision_notas||'';}catch{}}
  return t;
}
function toast(m,t=''){const e=document.getElementById('toast');e.textContent=m;e.className='toast'+(t?' '+t:'');e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2600);}
function openM(id){document.getElementById(id).classList.add('open');}
function closeM(id){document.getElementById(id).classList.remove('open');}
document.addEventListener('click',e=>{if(e.target.classList.contains('mov'))e.target.classList.remove('open');});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.mov.open').forEach(m=>m.classList.remove('open'));});
function setTab(tab,btn){
  S.tab=tab;
  document.querySelectorAll('.tc').forEach(el=>el.classList.remove('on'));
  document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('on'));
  const tabEl=document.getElementById('tab-'+tab);
  if(tabEl)tabEl.classList.add('on');
  if(btn)btn.classList.add('on');
  if(tab==='dash')renderDash();
  if(tab==='ds160')renderD();
  if(tab==='eval')renderE();
  if(tab==='rrss')renderR();
  if(tab==='ge')renderG();
}


// ─── RRSS RENDER ─────────────────────────────────────────
function renderR(){
  const q=(document.getElementById('q-r')?.value||'').toLowerCase();
  const plan=document.getElementById('st-r')?.value||'';
  let lista=S.evals.filter(e=>{
    const d=e.datos||{};
    return d.fuente==='rrss'||d.plan||d.ref_code;
  }).map(e=>{
    const d=e.datos||{};
    e._nombre=d.nombre||'';e._apellido=d.apellido||'';
    e._email=d.email||'';e._plan=d.plan||'';
    return e;
  });
  if(plan)lista=lista.filter(e=>e._plan===plan);
  if(q)lista=lista.filter(e=>(e._nombre+e._apellido+e._email).toLowerCase().includes(q));
  document.getElementById('tb-r').textContent=lista.length;
  if(!lista.length){
    document.getElementById('list-r').innerHTML='<div class="empty-s"><div class="empty-ico">📱</div>Sin evaluaciones RRSS</div>';
    return;
  }
  const planColors={'basico':'b-bl','full':'b-yn'};
  const planLabels={'basico':'💙 Básico RD$1,490','full':'⭐ Full RD$2,490'};
  document.getElementById('list-r').innerHTML=lista.map(ev=>{
    const nm=((ev._nombre||'')+(ev._apellido?' '+ev._apellido:'')).trim().toUpperCase()||'Sin nombre';
    const dec=ev.decision_ia||'PENDIENTE';
    const dc={APLICAR:'b-gn',MEJORAR:'b-yn','NO APLICAR':'b-rd',PENDIENTE:'b-bl'};
    return `<div class="item" onclick="openEval('${ev.id}')">
      <div class="av pu">${ini(nm)}</div>
      <div class="ii">
        <div class="inm">${esc(nm)}</div>
        <div class="iem">${esc(ev._email||'—')}</div>
        <div class="imeta">
          ${ev._plan?`<span class="badge ${planColors[ev._plan]||'b-bl'}">${planLabels[ev._plan]||ev._plan}</span>`:''}
          <span class="badge ${dc[dec]||'b-bl'}">${dec}</span>
          ${ev.score_ia?`<span class="badge b-pu">Score: ${ev.score_ia}</span>`:''}
        </div>
      </div>
      <div class="idate">${(ev.created_at||'').substring(0,10)}</div>
    </div>`;
  }).join('');
}

// ─── IA MODAL ────────────────────────────────────────────
function openIAModal(){
  // Poblar selector con casos DS-160
  const sel=document.getElementById('ia-sel');
  sel.innerHTML='<option value="">— Seleccionar cliente —</option>';
  S.ds160.forEach(c=>{
    const nm=((c._nombre||'')+(c._apellido?' '+c._apellido:'')).trim().toUpperCase()||'Sin nombre';
    const pct=c._pct||0;
    const opt=document.createElement('option');
    opt.value=c.id;
    opt.textContent=nm+' · '+pct+'% · '+(c._email||'—');
    sel.appendChild(opt);
  });
  document.getElementById('ia-result-modal').innerHTML='';
  document.getElementById('ia-loading').style.display='none';
  document.getElementById('ia-preview').style.display='none';
  document.getElementById('ia-pdf-btn').style.display='none';
  openM('m-ia');
}

function previewIACliente(){
  const id=document.getElementById('ia-sel').value;
  if(!id){document.getElementById('ia-preview').style.display='none';return;}
  const caso=S.ds160.find(c=>c.id===id);
  if(!caso){return;}
  const d=caso.datos||{};
  const nm=((caso._nombre||'')+(caso._apellido?' '+caso._apellido:'')).trim().toUpperCase()||'Sin nombre';
  const pct=caso._pct||0;const pc=pctC(pct);
  document.getElementById('ia-prev-content').innerHTML=`
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-weight:700;font-size:12px">${nm}</div>
        <div style="font-size:10px;color:var(--s3)">${caso._email||'—'} · 🛂 ${d.q43_numpas||d.numero_pasaporte||'—'}</div>
        <div style="font-size:10px;color:var(--s3);margin-top:1px">📱 ${caso._tel||'—'} · ${caso.estado||'—'}</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:22px;font-weight:900;color:${pc}">${pct}%</div>
        <div style="font-size:9px;color:var(--s3)">Completitud</div>
      </div>
    </div>`;
  document.getElementById('ia-preview').style.display='block';
}

let iaResultData=null;
async function runIAModal(){
  const id=document.getElementById('ia-sel').value;
  if(!id){toast('Selecciona un cliente primero','err');return;}
  document.getElementById('ia-loading').style.display='block';
  document.getElementById('ia-result-modal').innerHTML='';
  document.getElementById('ia-pdf-btn').style.display='none';
  iaResultData=null;
  try{
    const r=await fetch(`${API}/evaluacion/ia/${id}`,{method:'POST',headers:hdr()});
    const d=await r.json();
    document.getElementById('ia-loading').style.display='none';
    const txt=d.resultado||d.ia_texto||JSON.stringify(d);
    iaResultData={id,txt,nombre:document.getElementById('ia-sel').selectedOptions[0]?.text||''};
    // Renderizar resultado formateado
    const lines=txt.split('\n');
    let html='';let inBlock=false;
    lines.forEach(line=>{
      line=esc(line);
      if(line.startsWith('##')||line.startsWith('**')){
        html+=`<div style="font-size:11px;font-weight:800;color:var(--pri);margin:10px 0 4px;padding-bottom:3px;border-bottom:1px solid var(--bd)">${line.replace(/[*#]/g,'')}</div>`;
      } else if(line.startsWith('- ')||line.startsWith('• ')){
        html+=`<div style="font-size:10.5px;padding:2px 0 2px 12px;border-left:2px solid var(--bd);margin-left:4px;color:var(--tx)">${line.substring(2)}</div>`;
      } else if(line.trim()){
        html+=`<div style="font-size:10.5px;line-height:1.6;color:var(--tx);margin-bottom:2px">${line}</div>`;
      }
    });
    document.getElementById('ia-result-modal').innerHTML=`
      <div style="background:linear-gradient(135deg,var(--prl),var(--pul));border:1px solid #B5D4F4;border-radius:9px;padding:11px;margin-bottom:10px">
        <div style="font-size:10px;font-weight:800;color:var(--pri);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">🧠 Análisis Consultar IA — TengoVisaRD</div>
        <div style="font-size:9.5px;color:var(--s2)">Basado en 20 años de experiencia como ex-oficial consular del Dept. de Estado EE.UU.</div>
      </div>
      <div style="font-size:10.5px;line-height:1.7">${html}</div>`;
    document.getElementById('ia-pdf-btn').style.display='inline-flex';
    toast('✓ Análisis IA generado','ok');
    sendPush('🧠 Análisis IA completado','Cliente: '+iaResultData.nombre.split('·')[0]);
  }catch(e){
    document.getElementById('ia-loading').style.display='none';
    document.getElementById('ia-result-modal').innerHTML=`<div style="padding:20px;text-align:center;color:var(--rd)">Error: ${e.message}</div>`;
  }
}

function exportIApdf(){
  if(!iaResultData)return;
  const w=window.open('','_blank','width=800,height:950');
  if(!w){toast('Permite ventanas emergentes','warn');return;}
  const now=new Date().toLocaleDateString('es-DO',{day:'2-digit',month:'long',year:'numeric'});
  w.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Análisis IA — TengoVisaRD</title>
  <style>body{font-family:Arial,sans-serif;padding:24px 28px;color:#0F172A}
  @media print{body{padding:14px 16px}@page{margin:12mm}}
  .wm{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-35deg);font-size:68px;font-weight:900;color:rgba(0,31,115,0.055);white-space:nowrap;pointer-events:none;z-index:0}</style>
  </head><body>
  <div class="wm">DOCUMENTO NO OFICIAL</div>
  <div style="background:linear-gradient(135deg,#001F73,#3B0764);color:#fff;padding:16px 20px;border-radius:9px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between">
    <div>
      <div style="font-size:17px;font-weight:800">🧠 TengoVisaRD · Análisis IA Consular</div>
      <div style="font-size:9.5px;opacity:.75">Asesoría Migratoria · Santo Domingo, RD · tengovisard.com</div>
    </div>
    <div style="text-align:right;font-size:10px;opacity:.85">${now}</div>
  </div>
  <div style="background:#f8fafc;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:10.5px">
    <strong>Cliente:</strong> ${esc(iaResultData.nombre)} &nbsp;·&nbsp; <strong>Caso:</strong> ${iaResultData.id.substring(0,8)}
  </div>
  <div style="font-size:10.5px;line-height:1.8;white-space:pre-wrap">${esc(iaResultData.txt)}</div>
  <div style="margin-top:18px;padding-top:9px;border-top:2px solid #E2E8F0;display:flex;justify-content:space-between;font-size:9px;color:#94A3B8">
    <span>TengoVisaRD · Asesoría Migratoria · Santo Domingo, RD</span>
    <span style="color:#E24B4A;font-weight:700">DOCUMENTO NO OFICIAL — USO INTERNO</span>
  </div>
  \u003Cscript>window.onload=()=>setTimeout(()=>window.print(),600);<\/script>
  \u003C/script>
\u003C/script>
</body></html>`);
  w.document.close();
}

// ─── PUSH NOTIFICATIONS ──────────────────────────────────
async function sendPush(title,msg){
  try{
    await fetch(`https://tengovisard.com/push/api.php?token=tgvsa&user_id=tengovisa%40gmail.com&title=${encodeURIComponent(title)}&message=${encodeURIComponent(msg)}`);
  }catch(e){}
}

// ─── LINK TIPO ───────────────────────────────────────────
function updLinkTipo(){
  const t=document.getElementById('gl-tipo').value;
  const info={
    ds160:'🛂 Formulario DS-160 de 15 pasos. El cliente llenará datos personales, pasaporte, viaje y más.',
    evaluacion:'📋 Evaluación de perfil B1/B2. El cliente responde preguntas sobre su situación migratoria para análisis IA.',
    rrss:'📱 Evaluación de redes sociales. Análisis de huella digital antes de la entrevista. Plan Básico RD$1,490 / Full RD$2,490.',
    globalentry:'🌐 Global Entry / TSA PreCheck. Solicitud de pre-aprobación para entrada rápida a EE.UU.',
  };
  const el=document.getElementById('gl-tipo-info');
  if(el)el.textContent=info[t]||'';
}

// ─── FIX setTab para RRSS ────────────────────────────────
const _origSetTab=window.setTab;

// ─── CARGA ───────────────────────────────────────────────
async function loadAll(){
  try{
    const [r1,r2,r3]=await Promise.all([
      fetch(`${API}/ds160/all/v2`,{headers:hdr()}),
      fetch(`${API}/evaluacion/all`,{headers:hdr()}),
      fetch(`${API}/globalentry/all`,{headers:hdr()}),
    ]);
    const [d1,d2,d3]=await Promise.all([r1.json(),r2.json(),r3.json()]);
    const rawD=(d1['casos']||d1.casos||d1.records||[]).filter(c=>c.estado!=='archivado');
    S.ds160=rawD.map(c=>{
      const d=c.datos||{};
      c._nombre=d.q2_nombre||d.nombre||'';
      c._apellido=d.q1_apellido||d.apellido_primario||'';
      c._email=d.email||'';
      c._pasaporte=d.q43_numpas||d.numero_pasaporte||'';
      c._tel=d.q33_tel||d.telefono_principal||'';
      // Calcular % real
      const req=['q1_apellido','apellido_primario','q2_nombre','nombre','q7_sexo','sexo',
        'q8_civil','estado_civil','q9_dob','fecha_nacimiento','q10_ciudad_nac','ciudad_nacimiento',
        'q12_pais_nac','pais_nacimiento','q13_nacionalidad','pais_nacionalidad',
        'q20_cedula','numero_id_tributario','q23_dir1','direccion_rd','q25_ciudad','ciudad_rd',
        'q26_provincia','provincia_rd','q33_tel','telefono_principal','email',
        'q42_tipo_pas','tipo_pasaporte','q43_numpas','numero_pasaporte',
        'q45_pais_pas','pais_emisor_pasaporte','q48_emision','fecha_emision_pasaporte',
        'q49_vence','fecha_vencimiento_pasaporte','q55_proposito','proposito_viaje',
        'q64_duracion','duracion_estancia','q65_dir_hospedaje','direccion_eeuu',
        'q66_ciudad_hosp','ciudad_eeuu','q98_cont_ap','nombre_contacto_eeuu',
        'q101_cont_rel','relacion_contacto_eeuu','q108_padre_ap','nombre_padre',
        'q113_madre_ap','nombre_madre','q131_ocupacion','ocupacion_actual','q160_idiomas'];
      const pares=[['q1_apellido','apellido_primario'],['q2_nombre','nombre'],
        ['q7_sexo','sexo'],['q8_civil','estado_civil'],['q9_dob','fecha_nacimiento'],
        ['q10_ciudad_nac','ciudad_nacimiento'],['q12_pais_nac','pais_nacimiento'],
        ['q13_nacionalidad','pais_nacionalidad'],['q20_cedula','numero_id_tributario'],
        ['q23_dir1','direccion_rd'],['q25_ciudad','ciudad_rd'],['q26_provincia','provincia_rd'],
        ['q33_tel','telefono_principal'],['email'],['q42_tipo_pas','tipo_pasaporte'],
        ['q43_numpas','numero_pasaporte'],['q45_pas_pas','pais_emisor_pasaporte'],
        ['q48_emision','fecha_emision_pasaporte'],['q49_vence','fecha_vencimiento_pasaporte'],
        ['q55_proposito','proposito_viaje'],['q64_duracion','duracion_estancia'],
        ['q65_dir_hospedaje','direccion_eeuu'],['q66_ciudad_hosp','ciudad_eeuu'],
        ['q98_cont_ap','nombre_contacto_eeuu'],['q101_cont_rel','relacion_contacto_eeuu'],
        ['q108_padre_ap','nombre_padre'],['q113_madre_ap','nombre_madre'],
        ['q131_ocupacion','ocupacion_actual'],['q160_idiomas']];
      let ok=0;
      pares.forEach(ks=>{if(ks.some(k=>d[k]&&String(d[k]).trim()&&d[k]!=='null'))ok++;});
      c._pct=Math.round(ok/pares.length*100);
      return c;
    });
    S.evals=d2['casos']||d2.evaluaciones||d2.items||d2.data||[];
    S.ge=d3['casos']||d3.solicitudes||d3.items||d3.data||[];
    document.getElementById('tb-d').textContent=S.ds160.length;
    const rrssCount=S.evals.filter(e=>{const d=e.datos||{};return d.fuente==='rrss'||d.plan;}).length;
    document.getElementById('tb-e').textContent=S.evals.length-rrssCount;
    document.getElementById('tb-r').textContent=rrssCount;
    document.getElementById('tb-g').textContent=S.ge.length;
    if(S.tab==='dash')renderDash();
    if(S.tab==='ds160')renderD();
    if(S.tab==='eval')renderE();
    if(S.tab==='ge')renderG();
  }catch(e){toast('Error cargando datos','err');}
}
// ─── DASHBOARD ───────────────────────────────────────────
function renderDash(){
  // DS-160 métricas
  const n=S.ds160.length;
  const rev=S.ds160.filter(c=>c.estado==='revision').length;
  const bor=S.ds160.filter(c=>c.estado==='borrador').length;
  const apr=S.ds160.filter(c=>c.estado==='aprobado').length;
  const pcts=S.ds160.map(c=>c._pct||0);
  const avgPct=pcts.length?Math.round(pcts.reduce((a,b)=>a+b,0)/pcts.length):0;
  const comp=S.ds160.filter(c=>(c._pct||0)>=80).length;
  const incompletos=S.ds160.filter(c=>(c._pct||0)<50).length;
  // Evaluaciones métricas
  const evTotal=S.evals.length;
  const evApr=S.evals.filter(e=>e.decision_ia==='APLICAR').length;
  const evMej=S.evals.filter(e=>e.decision_ia==='MEJORAR').length;
  const evNo=S.evals.filter(e=>e.decision_ia==='NO APLICAR').length;
  const evP=S.evals.filter(e=>!e.decision_ia||e.decision_ia==='PENDIENTE').length;
  // Clientes únicos (por email)
  const emails=new Set([...S.ds160.map(c=>c._email),...S.evals.map(e=>(e.datos||{}).email||''),...S.ge.map(g=>(g.datos||{}).email||'')].filter(Boolean));
  const clientes=emails.size;
  // Multi-servicio
  const multi=S.ds160.filter(c=>S.evals.some(e=>((e.datos||{}).email||'')===(c._email||''))||S.ge.some(g=>((g.datos||{}).email||'')===(c._email||''))).length;
  // Esta semana
  const ahora=new Date();const semana=new Date(ahora-7*24*3600*1000).toISOString();
  const semDs=S.ds160.filter(c=>(c.created_at||'')>semana).length;
  const semEv=S.evals.filter(e=>(e.created_at||'')>semana).length;

  document.getElementById('stats').innerHTML=`
    <div class="sc" style="cursor:pointer" onclick="setTab('ds160',document.querySelectorAll('.tab-btn')[1])">
      <div class="sico" style="background:var(--prl)">🛂</div>
      <div><div class="sn" style="color:var(--pri)">${n}</div><div class="sl">Expedientes DS-160</div>
      <div style="font-size:9px;color:var(--s3);margin-top:2px">📝${bor} borrador · 🔍${rev} revisión · ✅${apr} aprobado</div></div>
    </div>
    <div class="sc" style="cursor:pointer" onclick="setTab('eval',document.querySelectorAll('.tab-btn')[2])">
      <div class="sico" style="background:var(--pul)">📋</div>
      <div><div class="sn" style="color:var(--pu)">${evTotal}</div><div class="sl">Evaluaciones B1/B2</div>
      <div style="font-size:9px;color:var(--s3);margin-top:2px">✅${evApr} aplicar · ⚠️${evMej} mejorar · ❌${evNo} no</div></div>
    </div>
    <div class="sc" style="cursor:pointer" onclick="setTab('ge',document.querySelectorAll('.tab-btn')[3])">
      <div class="sico" style="background:var(--gnl)">🌐</div>
      <div><div class="sn" style="color:var(--gn)">${S.ge.length}</div><div class="sl">Global Entry</div>
      <div style="font-size:9px;color:var(--s3);margin-top:2px">Solicitudes recibidas</div></div>
    </div>
    <div class="sc">
      <div class="sico" style="background:#E0F2FE">👥</div>
      <div><div class="sn" style="color:#0284C7">${clientes}</div><div class="sl">Clientes únicos</div>
      <div style="font-size:9px;color:var(--s3);margin-top:2px">🔗 ${multi} con múltiples servicios</div></div>
    </div>
    <div class="sc">
      <div class="sico" style="background:${avgPct>=70?'var(--gnl)':'var(--ynl)'}">📊</div>
      <div>
        <div class="sn" style="color:${avgPct>=70?'var(--gn)':'var(--yn)'}">${avgPct}%</div>
        <div class="sl">Completitud promedio</div>
        <div style="font-size:9px;color:var(--s3);margin-top:2px">✅${comp} ≥80% · ⚠️${incompletos} &lt;50%</div>
      </div>
    </div>
    <div class="sc">
      <div class="sico" style="background:var(--prl)">📅</div>
      <div><div class="sn" style="color:var(--pri)">${semDs+semEv}</div><div class="sl">Esta semana</div>
      <div style="font-size:9px;color:var(--s3);margin-top:2px">🛂${semDs} DS-160 · 📋${semEv} eval</div></div>
    </div>`;
  initCharts();renderClientes();
}
function initCharts(){
  const est={revision:0,borrador:0,aprobado:0,otro:0};
  S.ds160.forEach(c=>{const e=c.estado||'otro';est[e]=(est[e]||0)+1;});
  mkDonut('ch-d',['Revisión','Borrador','Aprobado','Otro'],[est.revision,est.borrador,est.aprobado,est.otro],['#001F73','#F59E0B','#16A34A','#94A3B8']);
  const dec={APLICAR:0,MEJORAR:0,'NO APLICAR':0,PENDIENTE:0};
  S.evals.forEach(e=>{const d=e.decision_ia||'PENDIENTE';dec[d]=(dec[d]||0)+1;});
  mkDonut('ch-e',['Puede Aplicar','Mejorar','No Aplicar','Pendiente'],[dec.APLICAR,dec.MEJORAR,dec['NO APLICAR'],dec.PENDIENTE],['#16A34A','#F59E0B','#DC2626','#94A3B8']);
  const mes={};[...S.ds160,...S.evals,...S.ge].forEach(x=>{const dt=(x.created_at||'').substring(0,7);if(dt)mes[dt]=(mes[dt]||0)+1;});
  const sorted=Object.keys(mes).sort().slice(-5);
  const ml=['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  mkBar('ch-m',sorted.map(m=>ml[parseInt(m.split('-')[1])]),sorted.map(m=>mes[m]));
}
function mkDonut(id,labels,data,colors){
  const cv=document.getElementById(id);if(!cv)return;
  if(S.charts[id])S.charts[id].destroy();
  S.charts[id]=new Chart(cv,{type:'doughnut',data:{labels,datasets:[{data,backgroundColor:colors,borderWidth:2,borderColor:'#fff'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:8,font:{size:8}}}},cutout:'65%'}});
}
function mkBar(id,labels,data){
  const cv=document.getElementById(id);if(!cv)return;
  if(S.charts[id])S.charts[id].destroy();
  S.charts[id]=new Chart(cv,{type:'bar',data:{labels,datasets:[{data,backgroundColor:'#001F73',borderRadius:4,label:'Registros'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{stepSize:1,font:{size:8}}}}}});
}
function renderClientes(){
  const em={};
  S.ds160.forEach(c=>{const e=(c._email||'').toLowerCase();if(e)em[e]={ds160:c,ev:null,ge:null};});
  S.evals.forEach(ev=>{const e=((ev.datos||{}).email||'').toLowerCase();if(e){if(!em[e])em[e]={ds160:null,ev:null,ge:null};em[e].ev=ev;}});
  S.ge.forEach(g=>{const e=((g.datos||{}).email||'').toLowerCase();if(e){if(!em[e])em[e]={ds160:null,ev:null,ge:null};em[e].ge=g;}});
  const cls=Object.entries(em).slice(0,15);
  if(!cls.length){document.getElementById('dash-cl').innerHTML='';return;}
  let html=`<div style="background:#fff;border:1px solid var(--bd);border-radius:10px;overflow:hidden">
    <div style="padding:9px 12px;border-bottom:1px solid var(--bd);font-size:9.5px;font-weight:800;color:var(--s3);text-transform:uppercase;letter-spacing:.05em;display:flex;justify-content:space-between">
      <span>👥 Clientes (${cls.length})</span><span style="font-weight:400">DS-160 + Eval + GE unificados por email</span></div>`;
  cls.forEach(([email,data])=>{
    const nm=data.ds160?((data.ds160._nombre||'')+(data.ds160._apellido?' '+data.ds160._apellido:'')).trim():(data.ev?((data.ev.datos||{}).nombre||''):email);
    const pct=data.ds160?(data.ds160._pct||0):0;const pc=pctC(pct);
    const cid=data.ds160?.id;
    html+=`<div class="item" style="margin:0;border:none;border-bottom:1px solid #f8fafc;border-radius:0" ${cid?`onclick="setTab('ds160',document.querySelector('.tab-btn:nth-child(2)'));setTimeout(()=>openDS160('${cid}'),150)"`:''}>
      <div class="av" style="width:30px;height:30px;font-size:10.5px">${ini(nm)}</div>
      <div class="ii"><div class="inm">${esc(nm)||'—'}</div><div class="iem">${esc(email)}</div></div>
      <div style="display:flex;gap:3px;flex-shrink:0">
        <span class="cl-b ${data.ds160?'on':'off'}">DS-160</span>
        <span class="cl-b ${data.ev?'on':'off'}">Eval.</span>
        <span class="cl-b ${data.ge?'on':'off'}">GE</span>
      </div>
      <div style="text-align:right;flex-shrink:0;margin-left:7px">
        <div class="pl" style="color:${pc}">${pct}%</div>
        <div class="pb"><div class="pf" style="width:${pct}%;background:${pc}"></div></div>
      </div>
    </div>`;
  });
  html+='</div>';
  document.getElementById('dash-cl').innerHTML=html;
}

// ─── LISTAS ──────────────────────────────────────────────
function renderD(){
  const q=(document.getElementById('q-d')?.value||'').toLowerCase();
  const st=document.getElementById('st-d')?.value||'';
  let lista=S.ds160;
  if(st)lista=lista.filter(c=>c.estado===st);
  if(q)lista=lista.filter(c=>((c._nombre||'')+(c._apellido||'')+(c._email||'')+(c._pasaporte||'')).toLowerCase().includes(q));
  if(!lista.length){document.getElementById('list-d').innerHTML='<div class="empty-s"><div class="empty-ico">📂</div>Sin resultados</div>';return;}
  const bc={revision:'b-bl',borrador:'b-yn',aprobado:'b-gn',pendiente:'b-pu'};
  document.getElementById('list-d').innerHTML=lista.map(c=>{
    const nm=((c._nombre||'')+(c._apellido?' '+c._apellido:'')).trim()||'Sin nombre';
    const pct=c._pct||0;const pc=pctC(pct);
    const hasEval=S.evals.some(ev=>((ev.datos||{}).email||'').toLowerCase()===(c._email||'').toLowerCase());
    return `<div class="item" onclick="openDS160('${c.id}')">
      <div class="av">${ini(nm)}</div>
      <div class="ii">
        <div class="inm">${esc(nm)}</div>
        <div class="iem">${esc(c._email||'—')}${c._pasaporte?' · 🛂 '+esc(c._pasaporte):''}</div>
        <div class="imeta">
          <span class="badge ${bc[c.estado]||'b-bl'}">${c.estado||'—'}</span>
          ${hasEval?'<span class="badge b-pu">+ Eval</span>':''}
          <div class="pr"><span class="pl" style="color:${pc}">${pct}%</span><span class="pb"><span class="pf" style="width:${pct}%;background:${pc}"></span></span></div>
        </div>
      </div>
      <div class="idate">${(c.created_at||'').substring(0,10)}</div>
    </div>`;
  }).join('');
}
function renderE(){
  const q=(document.getElementById('q-e')?.value||'').toLowerCase();
  const st=document.getElementById('st-e')?.value||'';
  let lista=S.evals.map(e=>{
    const d=e.datos||{};
    e._nombre=d.nombre||d.q2_nombre||'';
    e._apellido=d.apellido||d.q1_apellido||'';
    e._email=d.email||'';
    e._ciudad=d.ciudad||'';
    return e;
  });
  if(st)lista=lista.filter(e=>e.estado===st);
  if(q)lista=lista.filter(e=>(e._nombre+e._apellido+e._email).toLowerCase().includes(q));
  if(!lista.length){document.getElementById('list-e').innerHTML='<div class="empty-s"><div class="empty-ico">📋</div>Sin evaluaciones</div>';return;}
  const dc={APLICAR:'b-gn',MEJORAR:'b-yn','NO APLICAR':'b-rd',PENDIENTE:'b-bl'};
  document.getElementById('list-e').innerHTML=lista.map(ev=>{
    const d=ev.datos||{};
    const nm=up((ev._nombre||'')+(ev._apellido?' '+ev._apellido:'')).trim()||'Sin nombre';
    const dec=ev.decision_ia||'PENDIENTE';
    return `<div class="item" onclick="openEval('${ev.id}')">
      <div class="av pu">${ini(nm)}</div>
      <div class="ii">
        <div class="inm">${esc(nm)}</div>
        <div class="iem">${esc(d.email||'—')} · ${esc(d.ciudad||'—')}</div>
        <div class="imeta">
          <span class="badge ${dc[dec]||'b-bl'}">${dec}</span>
          <span class="badge b-bl">${ev.estado||'—'}</span>
          ${ev.score_ia?`<span class="badge b-pu">Score: ${ev.score_ia}</span>`:''}
        </div>
      </div>
      <div class="idate">${(ev.created_at||'').substring(0,10)}</div>
    </div>`;
  }).join('');
}
function renderG(){
  const q=(document.getElementById('q-g')?.value||'').toLowerCase();
  let lista=S.ge.map(g=>{
    const d=g.datos||{};
    g._nombre=d.f_nombre||d.nombre||'';
    g._apellido=d.f_apellido1||d.apellido||'';
    g._email=d.email||'';
    return g;
  });
  if(q)lista=lista.filter(g=>(g._nombre+g._apellido+g._email).toLowerCase().includes(q));
  if(!lista.length){document.getElementById('list-g').innerHTML='<div class="empty-s"><div class="empty-ico">🌐</div>Sin solicitudes</div>';return;}
  document.getElementById('list-g').innerHTML=lista.map(g=>{
    const d=g.datos||{};
    const nm=up((g._nombre||'')+(g._apellido?' '+g._apellido:'')).trim()||'Sin nombre';
    return `<div class="item" onclick="openGE('${g.id}')">
      <div class="av gn">${ini(nm)}</div>
      <div class="ii">
        <div class="inm">${esc(nm)}</div>
        <div class="iem">${esc(d.email||'—')} · ${esc(d.programa||'Global Entry')}</div>
        <div class="imeta"><span class="badge b-gn">${g.estado||'recibido'}</span></div>
      </div>
      <div class="idate">${(g.created_at||'').substring(0,10)}</div>
    </div>`;
  }).join('');
}

// ─── DS-160 MODAL ────────────────────────────────────────
async function openDS160(id){
  S.CID=id;S.CA=null;
  openM('m-ds160');
  document.getElementById('mbody').innerHTML='<div class="empty-s"><div class="empty-ico">⏳</div>Cargando...</div>';
  try{
    const r=await fetch(`${API}/ds160/${id}`,{headers:hdr()});
    const d=await r.json();
    if(d.detail){document.getElementById('mbody').innerHTML=`<div class="empty-s">Error: ${d.detail}</div>`;return;}
    S.CA=d;
    const dat=d.datos||{};
    const nm=(gm(dat,'nombre')+' '+gm(dat,'apellido')).trim()||'Sin nombre';
    document.getElementById('mttl').textContent=nm;
    document.getElementById('msub').textContent=`ID: ${id.substring(0,8)} · ${d.estado||'—'} · ${(d.created_at||'').substring(0,10)}`;
    updPct(dat);
    buildModal(dat,cleanNotas(d.revision_notas||''));
  }catch(e){document.getElementById('mbody').innerHTML=`<div class="empty-s">Error: ${e.message}</div>`;}
}
function updPct(dat){
  const pct=calcPct(dat),pc=pctC(pct);
  const bar=document.getElementById('mpf'),lbl=document.getElementById('mpp');
  if(bar){bar.style.width=pct+'%';bar.style.background=pc;}
  if(lbl)lbl.textContent=pct+'%';
  const idx=S.ds160.findIndex(c=>c.id===S.CID);
  if(idx>-1){S.ds160[idx]._pct=pct;if(S.tab==='ds160')renderD();}
}
function buildModal(dat,notas){
  const miss=faltantes(dat),casado=isCasado(dat);
  let html=miss.length
    ?`<div class="alerta warn">⚠️ Faltan ${miss.length} campo${miss.length>1?'s':''}: ${miss.slice(0,5).join(', ')}${miss.length>5?'...':''}</div>`
    :'<div class="alerta ok">✅ Todos los campos requeridos completos</div>';
  FASES.forEach((fase,fi)=>{
    const ocultar=fase.oculta&&!casado;
    html+=`<div class="fase" id="fase-${fase.id}" ${ocultar?'style="display:none"':''}>
      <div class="fhdr" onclick="togF(${fi})"><span>${fase.icon} ${fase.t}</span><span id="fa-${fi}">▾</span></div>
      <div class="fbody" id="fc-${fi}">
        ${fase.campos.map(([lbl,canon,tipo])=>{
          const v=gm(dat,canon)||dat[canon]||'';
          return `<div class="frow" id="fr-${canon}">
            <div class="flbl">${lbl}</div>
            <div class="fval${v?'':' empty'}" id="fv-${canon}" onclick="togE('${canon}')">${v?esc(up(v)):'➕ Completar'}</div>
            <div class="finp" id="fi-${canon}">${mkInp(canon,tipo,v)}</div>
            <div class="fbtns" id="fb-${canon}">
              <button class="fsv" onclick="svF('${canon}')">💾</button>
              <button class="fcn" onclick="cancelE('${canon}')">✕</button>
            </div>
          </div>`;
        }).join('')}
      </div>
    </div>`;
  });
  html+=`<div class="nw">
    <div style="font-size:9.5px;font-weight:800;color:var(--s3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">📝 Notas del Asesor</div>
    <textarea class="nta" id="ntarea" placeholder="Escribe notas internas...">${esc(notas)}</textarea>
    <button class="ntsv" onclick="saveNotas()">💾 Guardar notas</button>
    <div id="ia-wrap" style="margin-top:7px"></div>
  </div>`;
  document.getElementById('mbody').innerHTML=html;
}
function togF(i){
  const el=document.getElementById('fc-'+i),ar=document.getElementById('fa-'+i);
  if(!el)return;
  const oculto=el.style.display==='none';
  el.style.display=oculto?'':'none';
  if(ar)ar.textContent=oculto?'▾':'▸';
}

// ─── INPUT BUILDER ───────────────────────────────────────
function mkInp(canon,tipo,v){
  const kd=`onkeydown="if(event.key==='Enter')svF('${canon}');if(event.key==='Escape')cancelE('${canon}')"`;
  const sc=`onchange="svF('${canon}')"`;
  const UPattr=`oninput="this.value=this.value.toUpperCase()"`;
  const sty=`style="text-transform:uppercase"`;
  function sel(ops,cur){
    const vl=(cur||'').toLowerCase();const vu=up(cur);
    return `<select id="fe-${canon}" ${sc}><option value="">—</option>`+ops.map(([a,b])=>`<option value="${a}"${(a.toLowerCase()===vl||a===vu)?' selected':''}>${b}</option>`).join('')+'</select>';
  }
  function selGeo(arr,cur){
    return `<select id="fe-${canon}" ${sc}><option value="">—</option>`+arr.map(v=>`<option${up(cur)===v?' selected':''}>${v}</option>`).join('')+'</select>';
  }
  if(tipo==='fecha')return`<input id="fe-${canon}" type="date" value="${v}" onchange="svF('${canon}')" ${kd}>`;
  if(tipo==='email')return`<input id="fe-${canon}" type="email" value="${v}" ${kd}>`;
  if(tipo==='cedula')return`<input id="fe-${canon}" type="text" inputmode="numeric" maxlength="11" value="${up(v)}" placeholder="00100000001" ${kd} ${UPattr} ${sty}>`;
  if(tipo==='num')return`<input id="fe-${canon}" type="number" inputmode="numeric" value="${v}" ${kd}>`;
  if(tipo==='area')return`<textarea id="fe-${canon}" ${kd} style="min-height:45px;resize:vertical">${esc(up(v))}</textarea>`;
  if(tipo==='tel')return`<input id="fe-${canon}" type="tel" inputmode="tel" value="${up(v)}" ${kd} ${UPattr} ${sty}>`;
  if(tipo==='tx')return`<input id="fe-${canon}" type="text" value="${up(v)}" ${kd} ${UPattr} ${sty}>`;
  if(tipo==='ciudad_rd')return selGeo(CITIES,v);
  if(tipo==='prov_rd')return selGeo(PROVS,v);
  if(tipo==='pais')return selGeo(PAISES,v);
  if(tipo==='estado_us')return selGeo(ESTADOS_US,v);
  if(tipo==='sexo')return sel([['M','M — Masculino'],['F','F — Femenino']],v);
  if(tipo==='civil')return sel([['soltero','Soltero/a'],['casado','Casado/a'],['divorciado','Divorciado/a'],['viudo','Viudo/a'],['union libre','Unión libre'],['separado','Separado/a']],v);
  if(tipo==='sino')return sel([['si','✅ Sí'],['no','❌ No']],v);
  if(tipo==='ocup')return sel([['EMPLOYED','Empleado'],['SELF EMPLOYED','Cuenta propia'],['STUDENT','Estudiante'],['RETIRED','Jubilado/a'],['UNEMPLOYED','Desempleado/a'],['HOMEMAKER','Ama/o de casa'],['OTHER','Otro']],v);
  if(tipo==='prop')return sel([['B-1/B-2','B-1/B-2 Turismo/Negocios'],['B-1','B-1 Negocios'],['B-2','B-2 Turismo']],v);
  if(tipo==='pagador')return sel([['SELF','Yo mismo'],['OTHER PERSON','Otra persona'],['EMPLOYER','Empleador']],v);
  if(tipo==='tipopas')return sel([['REGULAR','Regular'],['OFFICIAL','Oficial'],['DIPLOMATIC','Diplomático']],v);
  if(tipo==='relacion')return sel([['FRIEND','Amigo/a'],['RELATIVE','Familiar'],['EMPLOYER','Empleador'],['HOTEL','Hotel'],['OTHER','Otro']],v);
  if(tipo==='dna')return sel([['Does Not Apply','Does Not Apply'],['','Otro valor...']],v);
  return`<input id="fe-${canon}" type="text" value="${up(v)}" ${kd} ${UPattr} ${sty}>`;
}

// ─── EDITOR ──────────────────────────────────────────────
function togE(canon){
  const fi=document.getElementById('fi-'+canon),fb=document.getElementById('fb-'+canon),fv=document.getElementById('fv-'+canon);
  if(!fi)return;
  document.querySelectorAll('.finp').forEach(el=>{
    if(el.id!=='fi-'+canon&&el.style.display==='block')cancelE(el.id.replace('fi-',''));
  });
  fv.style.display='none';fi.style.display='block';fb.style.display='flex';
  const inp=fi.querySelector('input,select,textarea');
  if(inp){inp.focus();if(inp.tagName==='INPUT'&&inp.type!=='date')inp.select();}
}
function cancelE(canon){
  const fi=document.getElementById('fi-'+canon),fb=document.getElementById('fb-'+canon),fv=document.getElementById('fv-'+canon);
  if(fi)fi.style.display='none';if(fb)fb.style.display='none';if(fv)fv.style.display='';
}
async function svF(canon){
  if(!S.CID||!S.CA)return;
  const fi=document.getElementById('fi-'+canon),fv=document.getElementById('fv-'+canon);
  if(!fi)return;
  const inp=fi.querySelector('input,select,textarea');if(!inp)return;
  const nv=up(inp.value).trim();
  const dat=S.CA.datos||{};
  const campo=realKey(canon,dat);
  try{
    await fetch(`${API}/ds160/field/v2/${S.CID}`,{method:'POST',headers:hdr(),body:JSON.stringify({field:campo,value:nv})});
    cancelE(canon);
    fv.textContent=nv||'➕ Completar';fv.className='fval'+(nv?'':' empty');
    dat[campo]=nv;dat[canon]=nv;
    // Actualizar estado civil → mostrar/ocultar cónyuge
    if(canon==='civil'){
      const sec=document.getElementById('fase-p9b');
      if(sec)sec.style.display=isCasado(dat)?'':'none';
    }
    updPct(dat);
    const miss=faltantes(dat);
    const al=document.querySelector('.alerta');
    if(al){
      if(miss.length){al.className='alerta warn';al.innerHTML=`⚠️ Faltan ${miss.length} campos: ${miss.slice(0,5).join(', ')}${miss.length>5?'...':''}`;}
      else{al.className='alerta ok';al.textContent='✅ Todos los campos requeridos completos';}
    }
    toast('✓ Guardado','ok');
  }catch(e){toast('Error guardando','err');}
}
async function saveNotas(){
  if(!S.CID)return;
  const n=document.getElementById('ntarea').value;
  await fetch(`${API}/ds160/notes/v2/${S.CID}`,{method:'POST',headers:hdr(),body:JSON.stringify({notes:n})});
  toast('✓ Notas guardadas','ok');
}
// ─── AUTO DNA ────────────────────────────────────────────
async function llenarDNA(){
  if(!S.CID||!S.CA){toast('Abre un caso primero','err');return;}
  const dat=S.CA.datos||{};
  const dna={'q21_ssn':'DOES NOT APPLY','q22_tin':'DOES NOT APPLY','q35_tel_trab':'DOES NOT APPLY',
    'q44_libreta':'DOES NOT APPLY','q100_cont_org':'DOES NOT APPLY','q3_otros_nombres':'NO',
    'q14_otra_nac':'NO','q29_dir_ant':'NO','q50_perdio_pas':'NO','q56_planes':'NO','q76_compan':'NO',
    'q77_grupo':'NO','q82_estuvo':'NO','q87_visa_prev':'NO','q93_negacion':'NO','q96_peticion':'NO',
    'q111_padre_eeuu':'NO','q116_madre_eeuu':'NO','q118_fam_inm':'NO','q123_otros_fam':'NO',
    'q142_emp_ant':'NO','q151_edu':'NO','q157_clan':'NO','q161_org':'NO','q163_habilidades':'NO',
    'q165_militar':'NO','q172_paramilitar':'NO','q222_asistido':'NO',
    'q174':'NO','q175':'NO','q176':'NO','q177':'NO','q179':'NO','q181':'NO','q183':'NO',
    'q185':'NO','q187':'NO','q199':'NO','q201':'NO','q204':'NO','q206':'NO'};
  let n=0;
  for(const[k,v]of Object.entries(dna)){
    if(!dat[k]||dat[k]===''){
      await fetch(`${API}/ds160/field/v2/${S.CID}`,{method:'POST',headers:hdr(),body:JSON.stringify({field:k,value:v})});
      dat[k]=v;
      const fv=document.getElementById('fv-'+k);
      if(fv){fv.textContent=v;fv.className='fval';}
      n++;
    }
  }
  updPct(dat);toast('⚡ '+n+' campos completados','ok');
}

// ─── ELIMINAR ────────────────────────────────────────────
function confirmDel(){if(!S.CID)return;openM('m-del');}
async function doEliminar(){
  if(!S.CID)return;
  try{
    await fetch(`${API}/ds160/field/v2/${S.CID}`,{method:'POST',headers:hdr(),body:JSON.stringify({field:'estado',value:'archivado'})});
    S.ds160=S.ds160.filter(c=>c.id!==S.CID);
    closeM('m-del');closeM('m-ds160');
    renderD();renderDash();
    toast('✓ Caso archivado','ok');
  }catch(e){toast('Error','err');}
}

// ─── EXPORT JSON ─────────────────────────────────────────
async function exportJSON(){
  if(!S.CID)return;
  const r=await fetch(`${API}/ds160/download/${S.CID}`,{headers:hdr()});
  const b=await r.blob();
  const url=URL.createObjectURL(b);
  const a=document.createElement('a');
  a.href=url;a.download=`ds160_${S.CID.substring(0,8)}.json`;a.click();
  URL.revokeObjectURL(url);toast('✓ JSON descargado','ok');
}

// ─── IA DS-160 ───────────────────────────────────────────
async function runIA(){
  if(!S.CID){toast('Abre un caso primero','err');return;}
  const iaw=document.getElementById('ia-wrap');
  if(iaw)iaw.innerHTML='<div class="ia-box">⏳ Analizando perfil consultar... (20-40 seg)</div>';
  try{
    const r=await fetch(`${API}/ds160/analizar/${S.CID}`,{method:'POST',headers:hdr()});
    const d=await r.json();
    const txt=d.resultado||d.ia_texto||JSON.stringify(d);
    if(iaw)iaw.innerHTML=`<div class="ia-box">${esc(txt).replace(/\n/g,'<br>')}</div>`;
    toast('✓ Análisis IA listo','ok');
  }catch(e){if(iaw)iaw.innerHTML=`<div class="ia-box">Error: ${e.message}</div>`;}
}

// ─── IA EVAL ─────────────────────────────────────────────
async function runIAEval(){
  if(!S.CEval){toast('Abre una evaluación primero','err');return;}
  toast('🧠 Analizando...','');
  try{
    const r=await fetch(`${API}/evaluacion/ia/${S.CEval.id}`,{method:'POST',headers:hdr()});
    const d=await r.json();
    const txt=d.resultado||d.ia_texto||JSON.stringify(d);
    const iaw=document.getElementById('eia-wrap');
    if(iaw)iaw.innerHTML=`<div class="ia-box">${esc(txt).replace(/\n/g,'<br>')}</div>`;
    toast('✓ IA lista','ok');
  }catch(e){toast('Error IA','err');}
}

// ─── PDF ─────────────────────────────────────────────────
function genPDF(){
  if(!S.CA){toast('Abre un caso primero','err');return;}
  const dat=S.CA.datos||{};
  const nm=(gm(dat,'nombre')+' '+gm(dat,'apellido')).trim()||'Sin nombre';
  const pct=calcPct(dat),pc=pctC(pct),miss=faltantes(dat);
  const now=new Date().toLocaleDateString('es-DO',{day:'2-digit',month:'long',year:'numeric'});
  let fasesHTML='';
  FASES.forEach(fase=>{
    const rows=fase.campos.map(([lbl,canon])=>{
      const v=gm(dat,canon)||dat[canon]||'';
      const req=CREQ.includes(canon);
      return`<tr><td style="padding:4px 9px;font-size:10px;color:#64748B;font-weight:600;width:34%;background:#f8fafc;vertical-align:top;border-bottom:1px solid #f1f5f9">${lbl}${req?'<span style="color:#E24B4A">*</span>':''}</td><td style="padding:4px 9px;font-size:10px;color:${v?'#0F172A':'#FCA5A5'};font-weight:${v?'600':'400'};border-bottom:1px solid #f1f5f9;background:${v?'#fff':'#fff8f8'}">${v?up(v):'⚠️ PENDIENTE'}</td></tr>`;
    }).join('');
    fasesHTML+=`<div style="margin-bottom:12px;border:1px solid #E2E8F0;border-radius:7px;overflow:hidden;page-break-inside:avoid">
      <div style="background:#001F73;color:#fff;padding:6px 10px;font-size:10px;font-weight:800">${fase.icon} ${fase.t}</div>
      <table style="width:100%;border-collapse:collapse">${rows}</table></div>`;
  });
  const missHTML=miss.length
    ?`<div style="background:#FCEBEB;border:1px solid #FCA5A5;border-radius:7px;padding:8px 12px;margin-bottom:12px">
      <div style="font-size:11px;font-weight:800;color:#991b1b;margin-bottom:4px">⚠️ Campos requeridos pendientes (${miss.length})</div>
      <div style="display:flex;flex-wrap:wrap;gap:3px">${miss.map(m=>`<span style="background:#fff;border:1px solid #FCA5A5;border-radius:4px;padding:1px 6px;font-size:9.5px;color:#991b1b">${m}</span>`).join('')}</div></div>`
    :`<div style="background:#EAF8EE;border:1px solid #86EFAC;border-radius:7px;padding:8px 12px;margin-bottom:12px;font-size:10.5px;font-weight:700;color:#15803d">✅ Todos los campos requeridos completos</div>`;
  const w=window.open('','_blank','width=880,height:1050');
  if(!w){toast('Permite ventanas emergentes en el navegador','warn');return;}
  w.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>DS-160 ${nm}</title>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:Arial,sans-serif;color:#0F172A;background:#fff;padding:24px 28px;position:relative}
  @media print{body{padding:14px 16px}@page{margin:12mm;size:A4}}
  .wm{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-35deg);font-size:68px;font-weight:900;color:rgba(0,31,115,0.055);white-space:nowrap;pointer-events:none;z-index:0;letter-spacing:4px}
  .wm2{position:fixed;top:22%;left:50%;transform:translate(-50%,-50%) rotate(-35deg);font-size:18px;font-weight:800;color:rgba(0,31,115,0.07);white-space:nowrap;pointer-events:none;z-index:0}
  .wm3{position:fixed;top:78%;left:50%;transform:translate(-50%,-50%) rotate(-35deg);font-size:18px;font-weight:800;color:rgba(0,31,115,0.07);white-space:nowrap;pointer-events:none;z-index:0}
  .ct{position:relative;z-index:1}</style></head><body>
  <div class="wm">DOCUMENTO NO OFICIAL</div>
  <div class="wm2">TENGOVISARD · DOCUMENTO NO OFICIAL · USO INTERNO</div>
  <div class="wm3">TENGOVISARD · DOCUMENTO NO OFICIAL · USO INTERNO</div>
  <div class="ct">
  <div style="display:flex;align-items:center;justify-content:space-between;background:#001F73;color:#fff;padding:14px 18px;border-radius:9px;margin-bottom:12px">
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:38px;height:38px;background:#fff;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:19px">🛂</div>
      <div><div style="font-size:16px;font-weight:800">TengoVisaRD</div>
      <div style="font-size:9px;opacity:.7">Asesoría Migratoria · Santo Domingo, RD · tengovisard.com</div></div>
    </div>
    <div style="text-align:right"><div style="font-size:11px;font-weight:700">Resumen DS-160</div>
    <div style="font-size:9px;opacity:.75">${now} · Caso: ${(S.CID||'').substring(0,8)}</div></div>
  </div>
  <div style="display:flex;gap:10px;margin-bottom:10px">
    <div style="flex:1;background:#f8fafc;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px">
      <div style="font-size:16px;font-weight:800">${up(nm)}</div>
      <div style="font-size:10px;color:#64748B;margin-top:2px">📧 ${up(gm(dat,'email'))||'—'} · 📱 ${gm(dat,'tel')||'—'}</div>
      <div style="font-size:10px;color:#64748B;margin-top:1px">🛂 ${gm(dat,'numpas')||'—'} · Estado: ${S.CA.estado||'—'}</div>
    </div>
    <div style="background:#f8fafc;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px;text-align:center;min-width:88px">
      <div style="font-size:28px;font-weight:900;color:${pc}">${pct}%</div>
      <div style="font-size:9px;color:#64748B">Completitud</div>
      <div style="height:5px;background:#E2E8F0;border-radius:5px;margin-top:5px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${pc};border-radius:5px"></div></div>
    </div>
  </div>
  <div style="background:#FFF4DE;border:1px solid #FDE68A;border-radius:7px;padding:6px 12px;margin-bottom:10px;font-size:9px;color:#92400e;font-weight:600">
  ⚠️ DOCUMENTO NO OFICIAL — Uso interno TengoVisaRD. No es un documento oficial DS-160. El solicitante debe verificar y confirmar todos los datos antes del envío oficial en ceac.state.gov.
  </div>
  ${missHTML}${fasesHTML}
  <div style="margin-top:14px;padding-top:9px;border-top:2px solid #E2E8F0;display:flex;justify-content:space-between;font-size:9px;color:#94A3B8">
    <span>TengoVisaRD · Asesoría Migratoria · Santo Domingo, RD</span>
    <span style="font-weight:700;color:#E24B4A">DOCUMENTO NO OFICIAL — USO INTERNO</span>
  </div></div>
  \u003Cscript>window.onload=()=>setTimeout(()=>window.print(),700);<\/script>
  </body></html>`);w.document.close();
}

// ─── GENERAR LINK ────────────────────────────────────────
async function doGenLink(){
  const nombre=document.getElementById('gl-n').value.trim();
  const apellido=document.getElementById('gl-a').value.trim();
  const email=document.getElementById('gl-e').value.trim();
  const tel=document.getElementById('gl-t').value.trim();
  if(!nombre||!email){toast('Nombre y email son requeridos','err');return;}
  try{
    const r=await fetch(`${API}/ds160/generar-link`,{method:'POST',headers:hdr(),body:JSON.stringify({nombre,apellido,email,tel})});
    const d=await r.json();
    if(d.ok){
      await navigator.clipboard.writeText(d.link).catch(()=>{});
      document.getElementById('gl-res').style.display='block';
      document.getElementById('gl-url').textContent=d.link;
      if(d.whatsapp)setTimeout(()=>window.open(d.whatsapp,'_blank'),600);
      loadAll();toast('✓ Link copiado','ok');
    }else toast('Error: '+(d.error||'desconocido'),'err');
  }catch(e){toast('Error: '+e.message,'err');}
}

// ─── PLANTILLAS WA ───────────────────────────────────────
let tplCtxData={};
function openTpl(ctx){tplCtxData=ctx||{};showTplList();openM('m-tpl');}
function openTplDS(){openTpl(S.CA);}
function showTplList(){
  document.getElementById('tpl-list').style.display='block';
  document.getElementById('tpl-edit').style.display='none';
  const dat=tplCtxData?.datos||tplCtxData||{};
  const nm=up((gm(dat,'nombre')||dat._nombre||'')+' '+(gm(dat,'apellido')||dat._apellido||'')).trim();
  document.getElementById('tpl-sub').textContent=nm?`Cliente: ${nm}`:'Selecciona un mensaje';
  const tplColors={rec:'#EAF8EE',pend:'#FFF4DE',comp:'#EAF8EE',cita:'#EAF0FF',apr:'#F3E8FF',neg:'#FCEBEB'};
const tplBorder={rec:'#86EFAC',pend:'#FDE68A',comp:'#86EFAC',cita:'#B5D4F4',apr:'#C4B5FD',neg:'#FCA5A5'};
document.getElementById('tpl-list').innerHTML=TPLS.map(t=>`
    <div class="tpl" onclick="selTpl('${t.id}')" style="background:${tplColors[t.id]||'#f8fafc'};border-color:${tplBorder[t.id]||'var(--bd)'}">
      <div class="tpl-nm" style="font-size:13px">${t.ico} ${t.nm}</div>
      <div class="tpl-p">${t.txt.substring(0,65)}...</div>
    </div>`).join('');
}
function selTpl(id){
  const tpl=TPLS.find(t=>t.id===id);if(!tpl)return;
  const dat=tplCtxData?.datos||tplCtxData||{};
  const nm=up((gm(dat,'nombre')||dat._nombre||dat.nombre||'Cliente')+' '+(gm(dat,'apellido')||dat._apellido||dat.apellido||'')).trim();
  const miss=faltantes(dat);
  let txt=tpl.txt
    .replace(/{nombre}/g,nm)
    .replace(/{caso}/g,(tplCtxData?.id||'').substring(0,8))
    .replace(/{faltantes}/g,miss.length?miss.map(m=>`• ${m}`).join('\n'):'Ninguno')
    .replace(/{link}/g,`crm.tengovisard.com/ds160/`)
    .replace(/{fecha}/g,'')
    .replace(/{hora}/g,'');
  document.getElementById('tpl-txt').value=txt;
  document.getElementById('tpl-list').style.display='none';
  document.getElementById('tpl-edit').style.display='block';
}
function sendWA(){
  const txt=document.getElementById('tpl-txt').value;
  const dat=tplCtxData?.datos||tplCtxData||{};
  const tel=gm(dat,'tel')||dat._tel||dat.telefono_principal||'';
  const num=tel.replace(/\D/g,'');
  const url=`https://wa.me/${num||'18095000000'}?text=${encodeURIComponent(txt)}`;
  window.open(url,'_blank');
}

// ─── EVAL MODAL ──────────────────────────────────────────
async function openEval(id){
  S.CEval=null;openM('m-eval');
  document.getElementById('ebody').innerHTML='<div class="empty-s"><div class="empty-ico">⏳</div>Cargando...</div>';
  try{
    const r=await fetch(`${API}/evaluacion/${id}`,{headers:hdr()});
    const d=await r.json();
    S.CEval=d;
    const dat=d.datos||{};
    const nm=up((dat.nombre||'')+(dat.apellido?' '+dat.apellido:''))||'Sin nombre';
    document.getElementById('ettl').textContent=nm;
    document.getElementById('esub').textContent=`${d.estado||'—'} · Decision IA: ${d.decision_ia||'Pendiente'} · ${(d.created_at||'').substring(0,10)}`;
    const campos=Object.entries(dat).filter(([k,v])=>v&&!['lead_id','_generado','_token'].includes(k));
    let html=`<div style="padding:11px 12px;display:grid;grid-template-columns:1fr 1fr;gap:6px">`;
    campos.forEach(([k,v])=>{
      html+=`<div style="background:#f8fafc;border:1px solid var(--bd);border-radius:7px;padding:6px 9px">
        <div style="font-size:9px;font-weight:700;color:var(--s3);text-transform:uppercase">${k.replace(/_/g,' ')}</div>
        <div style="font-size:11px;font-weight:600;margin-top:1px;word-break:break-word">${esc(up(String(v)))}</div>
      </div>`;
    });
    html+='</div>';
    if(d.resultado_ia){html+=`<div style="padding:0 11px 11px"><div class="ia-box">${esc(d.resultado_ia).replace(/\n/g,'<br>')}</div></div>`;}
    else{html+=`<div style="padding:0 11px 11px"><div id="eia-wrap"></div></div>`;}
    document.getElementById('ebody').innerHTML=html;
  }catch(e){document.getElementById('ebody').innerHTML=`<div class="empty-s">Error: ${e.message}</div>`;}
}

// ─── GE MODAL ────────────────────────────────────────────
async function openGE(id){
  S.CGE=null;openM('m-ge');
  document.getElementById('gbody').innerHTML='<div class="empty-s"><div class="empty-ico">⏳</div>Cargando...</div>';
  try{
    const r=await fetch(`${API}/globalentry/all`,{headers:hdr()});
    const d=await r.json();
    const items=d.solicitudes||d.items||d.data||[];
    const ge=items.find(g=>g.id===id);
    if(!ge){document.getElementById('gbody').innerHTML='<div class="empty-s">No encontrado</div>';return;}
    S.CGE=ge;
    const dat=ge.datos||{};
    const nm=up((dat.f_nombre||dat.nombre||'')+(dat.f_apellido1?' '+dat.f_apellido1:''))||'Sin nombre';
    document.getElementById('gttl').textContent=nm;
    document.getElementById('gsub').textContent=`${ge.estado||'recibido'} · ${(ge.created_at||'').substring(0,10)}`;
    const campos=Object.entries(dat).filter(([k,v])=>v&&!['lead_id','_generado'].includes(k));
    let html=`<div style="padding:11px 12px;display:grid;grid-template-columns:1fr 1fr;gap:6px">`;
    campos.forEach(([k,v])=>{
      html+=`<div style="background:#f8fafc;border:1px solid var(--bd);border-radius:7px;padding:6px 9px">
        <div style="font-size:9px;font-weight:700;color:var(--s3);text-transform:uppercase">${k.replace(/_/g,' ')}</div>
        <div style="font-size:11px;font-weight:600;margin-top:1px;word-break:break-word">${esc(up(String(v)))}</div>
      </div>`;
    });
    html+='</div>';
    document.getElementById('gbody').innerHTML=html;
  }catch(e){document.getElementById('gbody').innerHTML=`<div class="empty-s">Error: ${e.message}</div>`;}
}

// ─── INIT ────────────────────────────────────────────────
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
loadAll();
setInterval(loadAll,60000);
