<?php
// ═══════════════════════════════════════════════════
// INSTALADOR LANDINGS — TENGO VISA RD
// Ejecutar UNA sola vez desde el navegador.
// Se auto-elimina al terminar.
// ═══════════════════════════════════════════════════

$BASE  = '/var/www/html';
$SUPA  = 'https://lbttnpcpqdjmpktuoegs.supabase.co';
$KEY   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxidHRucGNwcWRqbXBrdHVvZWdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2NjAyNDEsImV4cCI6MjA5MTIzNjI0MX0.GsuZUkJIOmOITdl0hATt_P603a7vaI01j72nzG94O60';
$WA    = '18499189998';

$log = [];

function mkd($path) {
    if (!is_dir($path)) {
        mkdir($path, 0755, true);
        return "Creado: $path";
    }
    return "Ya existe: $path";
}

function writeFile($path, $content) {
    file_put_contents($path, $content);
    return "Escrito: $path (" . round(strlen($content)/1024,1) . " KB)";
}

// ── CSS COMPARTIDO ───────────────────────────────────
$css = <<<CSS
:root{--navy:#1B2A4A;--navydk:#0f1e3a;--red:#E31837;--off:#F8F9FC;--gray:#64748b;--border:#dde3ee;--green:#16a34a;}
*{margin:0;padding:0;box-sizing:border-box;}html{scroll-behavior:smooth;}
body{font-family:system-ui,sans-serif;background:var(--off);color:var(--navy);overflow-x:hidden;}a{text-decoration:none;}
nav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(27,42,74,.97);backdrop-filter:blur(14px);height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;border-bottom:1px solid rgba(227,24,55,.2);}
.logo{display:flex;flex-direction:column;line-height:1;}.logo span.t{color:#fff;font-weight:900;font-style:italic;font-size:14px;font-family:Georgia,serif;}.logo span.v{color:#E31837;font-weight:900;font-style:italic;font-size:22px;font-family:Georgia,serif;}.logo span.s{background:var(--navy);border-radius:3px;padding:2px 5px;font-size:6px;color:#E31837;letter-spacing:1px;display:inline-block;margin-bottom:1px;}
.ncta{background:#E31837;color:#fff;border-radius:8px;padding:9px 18px;font-weight:700;font-size:12px;}
.hero{min-height:100vh;background:linear-gradient(150deg,var(--navydk) 0%,var(--navy) 58%,#1a1a2e 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:110px 24px 80px;text-align:center;}
.badge{display:inline-flex;align-items:center;gap:7px;background:rgba(227,24,55,.12);border:1px solid rgba(227,24,55,.3);border-radius:100px;padding:7px 18px;margin-bottom:24px;color:#ff8a96;font-size:12px;font-weight:700;letter-spacing:1.2px;}
h1{font-family:Georgia,serif;font-size:clamp(2rem,6vw,3.8rem);font-weight:900;color:#fff;line-height:1.1;margin-bottom:10px;}
h1 span{color:#E31837;font-style:italic;}
.sub{font-size:clamp(1rem,2.4vw,1.15rem);color:rgba(255,255,255,.68);max-width:560px;line-height:1.85;margin-bottom:12px;}
.sub2{font-size:13px;color:rgba(255,255,255,.38);max-width:480px;line-height:1.7;margin-bottom:40px;font-style:italic;}
.bhero{background:#E31837;color:#fff;border-radius:14px;padding:18px 40px;font-weight:800;font-size:clamp(14px,2.2vw,17px);box-shadow:0 10px 36px rgba(227,24,55,.5);display:inline-block;transition:transform .2s;}
.bhero:hover{transform:translateY(-2px);}
.hnote{margin-top:48px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:18px 28px;max-width:500px;display:flex;align-items:center;gap:14px;}
.hnote p{color:rgba(255,255,255,.55);font-size:13px;line-height:1.7;text-align:left;}
sec{padding:80px 24px;}.ctr{max-width:960px;margin:0 auto;}
.slbl{text-align:center;color:#E31837;font-weight:700;font-size:11px;letter-spacing:2.5px;margin-bottom:12px;}
.stit{text-align:center;font-family:Georgia,serif;font-size:clamp(1.5rem,4vw,2.2rem);font-weight:900;margin-bottom:12px;}
.ssub{text-align:center;color:var(--gray);font-size:15px;max-width:450px;margin:0 auto 48px;line-height:1.7;}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:22px;}
.paso{padding:28px 20px;border-radius:14px;border:1px solid #eaecf2;background:var(--off);position:relative;overflow:hidden;}
.paso .pn{position:absolute;top:8px;right:12px;font-size:3rem;font-weight:900;color:rgba(227,24,55,.05);}
.paso .pi{font-size:24px;margin-bottom:10px;}.paso h3{font-weight:800;margin-bottom:6px;font-size:.93rem;}.paso p{color:var(--gray);line-height:1.6;font-size:13px;}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px;}
.ben{background:#fff;border-radius:14px;padding:22px;box-shadow:0 2px 14px rgba(27,42,74,.05);border-left:3px solid #E31837;display:flex;gap:12px;align-items:flex-start;}
.ben .bi{font-size:20px;flex-shrink:0;margin-top:2px;}.ben h3{font-weight:800;margin-bottom:4px;font-size:.9rem;}.ben p{color:var(--gray);font-size:13px;line-height:1.6;}
.hum{background:linear-gradient(135deg,var(--navy),var(--navydk));border-radius:18px;padding:32px;display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;margin-top:28px;}
.hum h3{color:#fff;font-weight:900;font-size:1rem;margin-bottom:8px;}.hum p{color:rgba(255,255,255,.6);font-size:14px;line-height:1.8;}
.fw{max-width:640px;margin:0 auto;}
.fb{background:var(--off);border-radius:16px;padding:clamp(20px,5vw,40px);box-shadow:0 4px 28px rgba(27,42,74,.07);border:1px solid #e8ecf2;}
.fld{margin-bottom:16px;}.fld label{display:block;font-weight:700;margin-bottom:6px;font-size:14px;}
.fld input,.fld select,.fld textarea{width:100%;padding:13px 15px;border-radius:10px;border:1.5px solid var(--border);font-size:14px;outline:none;background:#fff;color:var(--navy);font-family:inherit;transition:border-color .2s;box-sizing:border-box;}
.fld input:focus,.fld select:focus,.fld textarea:focus{border-color:#E31837;}
.rg{display:flex;gap:8px;flex-wrap:wrap;}
.rl{flex:1;padding:12px;border-radius:10px;border:1.5px solid var(--border);cursor:pointer;text-align:center;font-weight:600;font-size:13px;color:var(--gray);transition:all .2s;min-width:120px;}
.rl.on{border-color:#E31837;background:rgba(227,24,55,.05);color:#E31837;}
.fld input[type=radio]{display:none;}
.warn{background:#fffbeb;border:1px solid #f59e0b;border-radius:8px;padding:10px 14px;margin-top:8px;color:#92400e;font-size:13px;line-height:1.6;}
.err{background:rgba(227,24,55,.07);border:1px solid rgba(227,24,55,.22);border-radius:8px;padding:10px 14px;margin-bottom:16px;color:#b01226;font-size:14px;line-height:1.6;}
.blk{background:#fffbeb;border:1.5px solid #f59e0b;border-radius:12px;padding:24px;margin-bottom:24px;text-align:center;}
.blk p{color:#92400e;font-size:14px;line-height:1.75;}
.suc{background:#f0fdf4;border:2px solid #22c55e;border-radius:14px;padding:40px 28px;text-align:center;}
.suc h3{font-weight:900;color:#166534;font-size:1.3rem;margin-bottom:10px;}.suc p{color:#15803d;font-size:14px;line-height:1.8;}
.bsub{width:100%;background:#E31837;color:#fff;border:none;border-radius:12px;padding:17px;font-weight:800;font-size:15px;cursor:pointer;box-shadow:0 6px 22px rgba(227,24,55,.4);font-family:inherit;}
.bsub:disabled{background:#aaa;box-shadow:none;cursor:not-allowed;}
.fnote{text-align:center;font-size:11px;color:#94a3b8;margin-top:14px;line-height:1.65;}
.ctaf{background:linear-gradient(135deg,var(--navy),var(--navydk));text-align:center;}
.ctaf h2{font-family:Georgia,serif;font-size:clamp(1.5rem,4vw,2.3rem);font-weight:900;color:#fff;max-width:520px;margin:0 auto 12px;line-height:1.2;}
.ctaf p{color:rgba(255,255,255,.5);font-size:15px;max-width:400px;margin:0 auto 32px;line-height:1.7;}
.bctaf{background:#E31837;color:#fff;border-radius:12px;padding:17px 36px;font-weight:800;font-size:15px;display:inline-block;box-shadow:0 8px 30px rgba(227,24,55,.5);}
footer{padding:40px 24px;background:#0a1628;text-align:center;border-top:1px solid rgba(255,255,255,.05);}
.flinks{display:flex;gap:18px;justify-content:center;flex-wrap:wrap;margin:14px 0 20px;}
.flinks a{color:rgba(255,255,255,.45);font-size:13px;}
.legal{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:14px 20px;max-width:600px;margin:0 auto 18px;}
.legal p{color:rgba(255,255,255,.28);font-size:11px;line-height:1.8;}
.fcopy{color:rgba(255,255,255,.14);font-size:11px;}
@media(max-width:600px){.rg{flex-direction:column;}.hum{flex-direction:column;}}
CSS;

// ── JS COMPARTIDO ────────────────────────────────────
function jsBase($supa, $key, $wa, $tabla, $ctaText, $fields_code) {
    return <<<JS
const SUPA="$supa",KEY="$key",WA="$wa",TABLA="$tabla";
const rd={};
function sel(g,v){rd[g]=v;document.querySelectorAll('input[name="'+g+'"]').forEach(r=>{r.closest('.rl').classList.toggle('on',r.value===v);});}
function hide(id){document.getElementById(id).style.display='none';}
function show(id,d){document.getElementById(id).style.display=d||'block';}
function setErr(msg){const e=document.getElementById('err');e.textContent=msg;show('err');}
$fields_code
JS;
}

// ══════════════════════════════════════════════════════
// LANDING A — CLIENTE CON CITA
// ══════════════════════════════════════════════════════
$htmlA = <<<HTML
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>¿Tu cita consular está muy lejos? | Tengo Visa RD</title>
<meta name="description" content="Seguimiento personalizado de disponibilidad consular para intentar acercar tu cita ya programada."/>
<style>$css</style></head><body>
<nav><div class="logo"><span class="s">★★★★★</span><div><span class="t">tengo</span><span class="v">Visa</span></div></div><a class="ncta" href="#form">SOLICITAR AHORA</a></nav>

<div class="hero">
  <div class="badge">✈️ SOLO PARA CITAS YA PROGRAMADAS · ACCESO AIS REQUERIDO</div>
  <h1>¿Tu cita consular<br/><span>está muy lejos?</span></h1>
  <p class="sub">Nuestro equipo realiza <strong style="color:#fff">seguimiento personalizado de disponibilidad consular</strong> para identificar oportunidades de fechas más cercanas cuando el sistema oficial las habilite.</p>
  <p class="sub2">Servicio exclusivo para personas con cita consular programada y acceso activo a su cuenta AIS.</p>
  <a href="#form" class="bhero">SOLICITAR ACERCAR MI CITA</a>
  <div class="hnote"><span style="font-size:24px;flex-shrink:0">👥</span><p><strong style="color:#fff">Revisión manual, equipo humano.</strong> Sin programas automatizados ni sistemas externos.</p></div>
</div>

<sec style="background:#fff"><div class="ctr">
  <p class="slbl">EL PROCESO</p><h2 class="stit">¿Cómo funciona?</h2><p class="ssub">Cuatro pasos. Un asesor humano. Sin automatizaciones.</p>
  <div class="grid4">
    <div class="paso"><div class="pn">01</div><div class="pi">📝</div><h3>Completa el formulario</h3><p>Comparte los datos básicos de tu cita actual.</p></div>
    <div class="paso"><div class="pn">02</div><div class="pi">🔎</div><h3>Verificamos si calificas</h3><p>Confirmamos cita activa, acceso AIS y disposición para iniciar.</p></div>
    <div class="paso"><div class="pn">03</div><div class="pi">🤝</div><h3>Asignamos seguimiento</h3><p>Un asesor realiza revisión periódica de disponibilidad consular.</p></div>
    <div class="paso"><div class="pn">04</div><div class="pi">📲</div><h3>Te contactamos si procede</h3><p>Si se identifica una oportunidad viable, te coordinamos por WhatsApp.</p></div>
  </div>
</div></sec>

<sec style="background:var(--off)"><div class="ctr">
  <p class="slbl">LO QUE INCLUYE</p><h2 class="stit">Lo que incluye el acompañamiento</h2>
  <div class="grid3">
    <div class="ben"><span class="bi">🔍</span><div><h3>Revisión periódica</h3><p>Revisión manual y constante del sistema consular. Sin automatizaciones.</p></div></div>
    <div class="ben"><span class="bi">🤝</span><div><h3>Atención personalizada</h3><p>Un asesor humano atiende tu caso de principio a fin.</p></div></div>
    <div class="ben"><span class="bi">✅</span><div><h3>Solo citas programadas</h3><p>Exclusivo para quienes ya cuentan con una cita consular vigente.</p></div></div>
    <div class="ben"><span class="bi">🔒</span><div><h3>Solo casos calificados</h3><p>Contacto directo solo con quienes cumplen el perfil del servicio.</p></div></div>
    <div class="ben"><span class="bi">💬</span><div><h3>Lenguaje transparente</h3><p>Te explicamos qué hacemos, cómo y cuáles son los límites.</p></div></div>
    <div class="ben"><span class="bi">🚫</span><div><h3>Sin promesas falsas</h3><p>Trabajamos con lo que el sistema oficial habilita, nada más.</p></div></div>
  </div>
  <div class="hum"><span style="font-size:36px;flex-shrink:0">👥</span><div><h3>Trabajo 100% humano y manual</h3><p>No utilizamos programas automatizados, bots ni sistemas externos. Cada caso es atendido por un asesor humano dedicado.</p></div></div>
</div></sec>

<sec style="background:#fff" id="form"><div class="fw">
  <p class="slbl">EVALUACIÓN DE SOLICITUD</p>
  <h2 class="stit">Solicitar acercar mi cita</h2>
  <p class="ssub" style="margin-bottom:32px">Solo clientes con cita activa y acceso AIS son evaluados.</p>
  <div id="blk" class="blk" style="display:none"><div style="font-size:36px;margin-bottom:10px">ℹ️</div><p id="blk-t"></p></div>
  <div id="suc" class="suc" style="display:none"><div style="font-size:48px;margin-bottom:12px">✅</div><h3>¡Solicitud recibida!</h3><p>Serás redirigido a WhatsApp para hablar con nuestro asesor.</p></div>
  <div id="fbox" class="fb">
    <div class="fld"><label>Nombre completo *</label><input type="text" id="nombre" placeholder="Ej. Juan Pérez González"/></div>
    <div class="fld"><label>WhatsApp *</label><input type="tel" id="wa" placeholder="+1 (849) 000-0000"/></div>
    <div class="fld"><label>Fecha actual de cita consular *</label><input type="date" id="fecha"/></div>
    <div class="fld"><label>Cantidad de solicitantes *</label>
      <select id="sol"><option value="">— Selecciona —</option><option>1 solicitante</option><option>2 solicitantes</option><option>3 solicitantes</option><option>4 solicitantes</option><option>5 o más solicitantes</option></select>
    </div>
    <div class="fld"><label>¿Tiene acceso a su cuenta AIS? *</label>
      <div class="rg">
        <label class="rl" id="ais-si"><input type="radio" name="ais" value="si" onchange="sel('ais','si')"/> ✅ Sí, tengo acceso</label>
        <label class="rl" id="ais-no"><input type="radio" name="ais" value="no" onchange="sel('ais','no')"/> ❌ No tengo acceso</label>
      </div>
      <div id="ais-w" class="warn" style="display:none">⚠️ El acceso AIS es necesario para realizar el seguimiento de disponibilidad consular.</div>
    </div>
    <div class="fld"><label>¿Está dispuesto/a a iniciar hoy si califica? *</label>
      <div class="rg">
        <label class="rl" id="ini-si"><input type="radio" name="ini" value="hoy" onchange="sel('ini','hoy')"/> ✅ Sí, deseo iniciar hoy</label>
        <label class="rl" id="ini-no"><input type="radio" name="ini" value="pensar" onchange="sel('ini','pensar')"/> 🤔 Necesito pensarlo</label>
      </div>
    </div>
    <div class="fld"><label>Comentario adicional <span style="font-weight:400;color:#94a3b8">(opcional)</span></label><textarea id="com" rows="3" placeholder="Cuéntanos brevemente tu situación..."></textarea></div>
    <div id="err" class="err" style="display:none"></div>
    <button class="bsub" id="btn" onclick="enviar()">SOLICITAR ACERCAR MI CITA</button>
    <p class="fnote">🔒 Información confidencial. Un asesor real te responderá.<br/>Servicio sujeto a disponibilidad del sistema oficial.</p>
  </div>
</div></sec>

<sec class="ctaf"><div class="ctr">
  <h2>El sistema consular libera fechas sin previo aviso</h2>
  <p>Nuestro equipo está pendiente todos los días. Acompañamiento humano y transparente.</p>
  <a href="#form" class="bctaf">SOLICITAR ACERCAR MI CITA →</a>
</div></sec>

<footer>
  <div class="flinks"><a href="https://tengovisard.com" target="_blank">🌐 tengovisard.com</a><a href="https://instagram.com/visaeeuu" target="_blank">📷 @visaeeuu</a></div>
  <div class="legal"><p><strong style="color:rgba(255,255,255,.4)">Aviso legal:</strong> Tengo Visa RD ofrece acompañamiento privado y seguimiento de disponibilidad consular. No somos representantes del consulado ni garantizamos fechas. Toda disponibilidad depende del sistema oficial.</p></div>
  <p class="fcopy">© 2025 Tengo Visa RD · @visaeeuu</p>
</footer>

<script>
const SUPA="$SUPA",KEY="$KEY",WA="$WA";
const rd={};
function sel(g,v){rd[g]=v;document.querySelectorAll('input[name="'+g+'"]').forEach(r=>{r.closest('.rl').classList.toggle('on',r.value===v);});if(g==='ais')document.getElementById('ais-w').style.display=v==='no'?'block':'none';}
async function enviar(){
  const n=document.getElementById('nombre').value.trim(),w=document.getElementById('wa').value.trim(),f=document.getElementById('fecha').value,s=document.getElementById('sol').value,a=rd['ais']||'',i=rd['ini']||'',c=document.getElementById('com').value.trim();
  document.getElementById('err').style.display='none';
  if(!n||!w||!f||!s||!a||!i){document.getElementById('err').textContent='Por favor completa todos los campos requeridos para evaluar tu solicitud.';document.getElementById('err').style.display='block';return;}
  if(a==='no'){document.getElementById('fbox').style.display='none';document.getElementById('blk').style.display='block';document.getElementById('blk-t').textContent='Gracias por tu información. Este servicio requiere acceso activo a la cuenta AIS para poder realizar el seguimiento de disponibilidad.';return;}
  if(i==='pensar'){document.getElementById('fbox').style.display='none';document.getElementById('blk').style.display='block';document.getElementById('blk-t').textContent='Gracias por tu interés. Este formulario está diseñado para personas listas para iniciar. Puedes volver cuando estés preparado/a.';return;}
  const btn=document.getElementById('btn');btn.disabled=true;btn.textContent='Enviando...';
  try{await fetch(SUPA+'/rest/v1/leads_cita',{method:'POST',headers:{'apikey':KEY,'Authorization':'Bearer '+KEY,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({nombre:n,whatsapp:w,fecha_cita:f,solicitantes:s,tiene_ais:a,inicia_hoy:i,comentario:c||null,status:'nuevo'})});}catch(e){}
  document.getElementById('fbox').style.display='none';document.getElementById('suc').style.display='block';
  const msg=encodeURIComponent('Hola Tengo Visa RD. Deseo solicitar el servicio para intentar acercar mi cita.\n\nNombre: '+n+'\nWhatsApp: '+w+'\nFecha cita: '+f+'\nSolicitantes: '+s+'\nAcceso AIS: Sí\nInicia hoy: Sí'+(c?'\nComentario: '+c:''));
  window.open('https://wa.me/'+WA+'?text='+msg,'_blank');
}
</script></body></html>
HTML;

// ══════════════════════════════════════════════════════
// LANDING B — ASESORES
// ══════════════════════════════════════════════════════
$htmlB = <<<HTML
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>¿Tus clientes tienen citas para 2027? | Tengo Visa RD</title>
<meta name="description" content="Plan profesional para asesores migratorios, abogados y preparadores con casos consulares activos."/>
<style>$css</style></head><body>
<nav><div class="logo"><span class="s">★★★★★</span><div><span class="t">tengo</span><span class="v">Visa</span></div></div><a class="ncta" href="#form">SOLICITAR PLAN PROFESIONAL</a></nav>

<div class="hero">
  <div class="badge">💼 EXCLUSIVO PARA PROFESIONALES MIGRATORIOS</div>
  <h1>¿Tus clientes tienen citas<br/><span>para 2027?</span></h1>
  <p class="sub">Ofrecemos <strong style="color:#fff">seguimiento personalizado de disponibilidad consular</strong> para los casos activos de tus clientes — coordinando directamente contigo.</p>
  <p class="sub2">Diseñado para asesores migratorios, preparadores de formularios y abogados de inmigración.</p>
  <a href="#form" class="bhero">SOLICITAR PLAN PROFESIONAL →</a>
  <div class="hnote"><span style="font-size:24px;flex-shrink:0">👥</span><p><strong style="color:#fff">100% trabajo humano, caso por caso.</strong> Sin automatizaciones ni sistemas externos.</p></div>
</div>

<sec style="background:#fff"><div class="ctr">
  <p class="slbl">CÓMO TRABAJAMOS</p><h2 class="stit">¿Cómo trabajamos juntos?</h2><p class="ssub">Un asesor coordina contigo directamente. Sin intermediarios.</p>
  <div class="grid4">
    <div class="paso"><div class="pn">01</div><div class="pi">📝</div><h3>Completa el formulario</h3><p>Comparte tu perfil profesional y los datos de tus casos activos.</p></div>
    <div class="paso"><div class="pn">02</div><div class="pi">🔎</div><h3>Verificamos si calificas</h3><p>Confirmamos que tengas casos activos con acceso AIS disponible.</p></div>
    <div class="paso"><div class="pn">03</div><div class="pi">🤝</div><h3>Coordinamos contigo</h3><p>Un asesor trabaja directamente contigo como colega profesional.</p></div>
    <div class="paso"><div class="pn">04</div><div class="pi">📲</div><h3>Seguimiento caso a caso</h3><p>Revisión periódica de disponibilidad consular por cada caso.</p></div>
  </div>
</div></sec>

<sec style="background:var(--off)"><div class="ctr">
  <p class="slbl">PLAN PROFESIONAL</p><h2 class="stit">Lo que incluye trabajar con nosotros</h2>
  <div class="grid3">
    <div class="ben"><span class="bi">🔍</span><div><h3>Seguimiento por caso</h3><p>Cada caso recibe atención individual con revisión manual periódica.</p></div></div>
    <div class="ben"><span class="bi">🤝</span><div><h3>Coordinación directa</h3><p>Trabajamos contigo como profesional, no con tu cliente final.</p></div></div>
    <div class="ben"><span class="bi">📋</span><div><h3>Sin volumen mínimo</h3><p>Puedes iniciar con un solo caso. Sin compromisos de cantidad.</p></div></div>
    <div class="ben"><span class="bi">💼</span><div><h3>Tarifa preferencial</h3><p>Asesores, preparadores y abogados acceden a condiciones especiales.</p></div></div>
    <div class="ben"><span class="bi">💬</span><div><h3>Comunicación clara</h3><p>Sabes exactamente qué hace nuestro equipo y cuándo.</p></div></div>
    <div class="ben"><span class="bi">🚫</span><div><h3>Sin garantías irreales</h3><p>La disponibilidad depende del sistema oficial. Trabajamos con honestidad.</p></div></div>
  </div>
  <div class="hum"><span style="font-size:34px;flex-shrink:0">💼</span><div><h3>Trabajamos con el profesional, no con el cliente final</h3><p>Tu relación con tu cliente es tuya. No la comprometemos. Somos el soporte operativo.</p></div></div>
</div></sec>

<sec style="background:#fff" id="form"><div class="fw">
  <p class="slbl">PLAN PROFESIONAL</p>
  <h2 class="stit">Solicitar Plan Profesional</h2>
  <p class="ssub" style="margin-bottom:32px">Solo para asesores, preparadores y abogados con casos consulares activos.</p>
  <div id="blk" class="blk" style="display:none"><div style="font-size:36px;margin-bottom:10px">ℹ️</div><p id="blk-t"></p></div>
  <div id="suc" class="suc" style="display:none"><div style="font-size:48px;margin-bottom:12px">✅</div><h3>¡Solicitud recibida!</h3><p>Serás redirigido a WhatsApp para coordinar el Plan Profesional.</p></div>
  <div id="fbox" class="fb">
    <div class="fld"><label>Nombre completo *</label><input type="text" id="nombre" placeholder="Nombre completo"/></div>
    <div class="fld"><label>WhatsApp profesional *</label><input type="tel" id="wa" placeholder="+1 (849) 000-0000"/></div>
    <div class="fld"><label>Tipo de perfil profesional *</label>
      <select id="tipo"><option value="">— Selecciona tu perfil —</option><option>Asesor migratorio independiente</option><option>Abogado de inmigración</option><option>Preparador de formularios</option><option>Oficina / Agencia migratoria</option><option>Otro profesional del área</option></select>
    </div>
    <div class="fld"><label>¿Cuántos clientes con cita activa tienes actualmente? *</label>
      <select id="cli"><option value="">— Selecciona —</option><option value="0">Ninguno por ahora</option><option value="1-3">1 a 3 clientes</option><option value="4-10">4 a 10 clientes</option><option value="10+">Más de 10 clientes</option></select>
    </div>
    <div class="fld"><label>¿Tienes acceso AIS de tus clientes? *</label>
      <div class="rg">
        <label class="rl"><input type="radio" name="ais" value="Sí, tengo acceso" onchange="sel('ais','Sí, tengo acceso')"/> ✅ Sí, tengo acceso</label>
        <label class="rl"><input type="radio" name="ais" value="Ellos lo manejan" onchange="sel('ais','Ellos lo manejan')"/> 🔄 Ellos lo manejan</label>
        <label class="rl"><input type="radio" name="ais" value="No en todos" onchange="sel('ais','No en todos')"/> ⚠️ No en todos</label>
      </div>
    </div>
    <div class="fld"><label>¿Buscas servicio puntual o relación continua? *</label>
      <div class="rg">
        <label class="rl"><input type="radio" name="rel" value="Caso puntual" onchange="sel('rel','Caso puntual')"/> 📁 Caso puntual</label>
        <label class="rl"><input type="radio" name="rel" value="Relación continua" onchange="sel('rel','Relación continua')"/> 🤝 Relación continua</label>
        <label class="rl"><input type="radio" name="rel" value="pensar" onchange="sel('rel','pensar')"/> 🤔 Aún lo evalúo</label>
      </div>
    </div>
    <div class="fld"><label>Comentario <span style="font-weight:400;color:#94a3b8">(opcional)</span></label><textarea id="com" rows="3" placeholder="Cuéntanos sobre tus casos..."></textarea></div>
    <div id="err" class="err" style="display:none"></div>
    <button class="bsub" id="btn" onclick="enviar()">SOLICITAR PLAN PROFESIONAL</button>
    <p class="fnote">🔒 Solo profesionales calificados son contactados por nuestro equipo.</p>
  </div>
</div></sec>

<sec class="ctaf"><div class="ctr">
  <h2>Sé el profesional que tiene solución para sus clientes</h2>
  <p>Seguimiento personalizado, coordinación directa y tarifa preferencial para el gremio migratorio.</p>
  <a href="#form" class="bctaf">SOLICITAR PLAN PROFESIONAL →</a>
</div></sec>

<footer>
  <div class="flinks"><a href="https://tengovisard.com" target="_blank">🌐 tengovisard.com</a><a href="https://instagram.com/visaeeuu" target="_blank">📷 @visaeeuu</a></div>
  <div class="legal"><p><strong style="color:rgba(255,255,255,.4)">Aviso legal:</strong> Tengo Visa RD ofrece acompañamiento privado y seguimiento de disponibilidad consular. No somos representantes del consulado ni garantizamos fechas específicas.</p></div>
  <p class="fcopy">© 2025 Tengo Visa RD · @visaeeuu</p>
</footer>

<script>
const SUPA="$SUPA",KEY="$KEY",WA="$WA";
const rd={};
function sel(g,v){rd[g]=v;document.querySelectorAll('input[name="'+g+'"]').forEach(r=>{r.closest('.rl').classList.toggle('on',r.value===v);});}
async function enviar(){
  const n=document.getElementById('nombre').value.trim(),w=document.getElementById('wa').value.trim(),t=document.getElementById('tipo').value,c=document.getElementById('cli').value,a=rd['ais']||'',r=rd['rel']||'',com=document.getElementById('com').value.trim();
  document.getElementById('err').style.display='none';
  if(!n||!w||!t||!c||!a||!r){document.getElementById('err').textContent='Por favor completa todos los campos requeridos para evaluar tu solicitud.';document.getElementById('err').style.display='block';return;}
  if(c==='0'){document.getElementById('fbox').style.display='none';document.getElementById('blk').style.display='block';document.getElementById('blk-t').textContent='Gracias por tu interés. Este servicio está diseñado para profesionales con casos activos. Puedes volver cuando tengas clientes con citas vigentes.';return;}
  if(r==='pensar'){document.getElementById('fbox').style.display='none';document.getElementById('blk').style.display='block';document.getElementById('blk-t').textContent='Gracias por explorar el servicio. Puedes volver cuando estés listo para coordinar casos activos.';return;}
  const btn=document.getElementById('btn');btn.disabled=true;btn.textContent='Enviando...';
  try{await fetch(SUPA+'/rest/v1/leads_asesores',{method:'POST',headers:{'apikey':KEY,'Authorization':'Bearer '+KEY,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({nombre:n,whatsapp:w,tipo_perfil:t,clientes_activos:c,tiene_ais:a,tipo_relacion:r,comentario:com||null,status:'nuevo'})});}catch(e){}
  document.getElementById('fbox').style.display='none';document.getElementById('suc').style.display='block';
  const msg=encodeURIComponent('Hola Tengo Visa RD. Soy un profesional migratorio y deseo solicitar el Plan Profesional.\n\nNombre: '+n+'\nWhatsApp: '+w+'\nTipo perfil: '+t+'\nClientes activos: '+c+'\nAcceso AIS: '+a+'\nRelación: '+r+(com?'\nComentario: '+com:''));
  window.open('https://wa.me/'+WA+'?text='+msg,'_blank');
}
</script></body></html>
HTML;

// ══════════════════════════════════════════════════════
// LANDING C — EVALUACIÓN DE PERFIL
// ══════════════════════════════════════════════════════
$htmlC = <<<HTML
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>¿Sabes si tu perfil califica para la visa? | Tengo Visa RD</title>
<meta name="description" content="Evaluación de perfil B1/B2 con criterios reales del consulado. Virtual RD\$2,500 · Presencial RD\$3,500. 30 días de vigencia."/>
<style>$css
.planes{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:22px;margin-bottom:28px;}
.plan{background:#fff;border-radius:16px;border:2px solid var(--border);overflow:hidden;transition:transform .3s;}
.plan:hover{transform:translateY(-4px);}
.plan.top{border-color:#E31837;box-shadow:0 8px 36px rgba(227,24,55,.15);}
.plan-hd{background:#E31837;color:#fff;text-align:center;padding:7px;font-size:12px;font-weight:700;letter-spacing:1px;}
.plan-bd{padding:26px;}
.plan-ico{font-size:34px;margin-bottom:10px;}
.plan h3{font-weight:900;font-size:1.2rem;margin-bottom:6px;}
.plan-d{color:var(--gray);font-size:13px;line-height:1.6;margin-bottom:18px;}
.plan-p{font-size:2.3rem;font-weight:900;color:#E31837;margin-bottom:4px;}
.plan-dur{font-size:12px;color:var(--green);font-weight:700;background:rgba(22,163,74,.08);border:1px solid rgba(22,163,74,.2);border-radius:6px;padding:5px 10px;margin-bottom:18px;display:inline-block;}
.plan-i{display:flex;gap:7px;margin-bottom:7px;font-size:13px;}
.plan-i span{color:var(--green);font-weight:700;flex-shrink:0;}
.plan-btn{width:100%;margin-top:18px;padding:13px;border-radius:10px;border:none;font-weight:800;font-size:14px;cursor:pointer;font-family:inherit;}
.pb-r{background:#E31837;color:#fff;}.pb-n{background:var(--navy);color:#fff;}
.sel-box{background:var(--navy);border-radius:12px;padding:16px 20px;margin-bottom:22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;}
.sel-box span{color:rgba(255,255,255,.55);font-size:11px;}
.sel-box strong{color:#fff;font-size:15px;font-weight:800;}
.sel-price{color:#E31837;font-size:1.7rem;font-weight:900;}
.cb-btn{background:none;border:none;color:rgba(255,255,255,.4);font-size:12px;cursor:pointer;font-family:inherit;}
.consent{background:rgba(27,42,74,.04);border:1px solid rgba(27,42,74,.1);border-radius:12px;padding:16px 20px;margin-bottom:22px;}
.consent p{font-size:13px;color:var(--gray);line-height:1.7;margin-bottom:10px;}
.consent label{display:flex;gap:8px;align-items:flex-start;cursor:pointer;font-size:13px;font-weight:600;color:var(--navy);}
.consent input[type=checkbox]{margin-top:2px;accent-color:#E31837;width:15px;height:15px;flex-shrink:0;}
</style></head><body>
<nav><div class="logo"><span class="s">★★★★★</span><div><span class="t">tengo</span><span class="v">Visa</span></div></div><a class="ncta" href="#planes">EVALUAR MI PERFIL</a></nav>

<div class="hero">
  <div class="badge">📋 EVALUACIÓN DE PERFIL · VISA B1/B2</div>
  <h1>¿Sabes si tu perfil<br/><span>califica para la visa?</span></h1>
  <p class="sub">Evaluamos tu perfil con <strong style="color:#fff">criterios reales del consulado</strong> antes de que inviertas tiempo y dinero en el proceso.</p>
  <p class="sub2">Para personas que aplican por primera vez o que fueron negadas y quieren entender su situación real antes de intentarlo de nuevo.</p>
  <a href="#planes" class="bhero">VER PLANES Y PRECIOS →</a>
  <div class="hnote"><span style="font-size:24px;flex-shrink:0">🛡️</span><p><strong style="color:#fff">Diagnóstico honesto, sin promesas.</strong> No garantizamos aprobaciones. Te decimos lo que vemos en tu perfil para que decidas con información real.</p></div>
</div>

<sec style="background:#fff" id="planes"><div class="ctr">
  <p class="slbl">SELECCIONA TU PLAN</p><h2 class="stit">¿Qué tipo de evaluación prefieres?</h2>
  <p class="ssub">Ambos planes incluyen el mismo rigor de análisis. La diferencia es el formato y la profundidad de la sesión.</p>
  <div class="planes">
    <div class="plan">
      <div class="plan-bd">
        <div class="plan-ico">💻</div><h3>Evaluación Virtual</h3>
        <p class="plan-d">Evaluación completa de forma virtual. Recibes un informe detallado por escrito.</p>
        <div class="plan-p">RD\$2,500</div>
        <div class="plan-dur">📅 30 días de vigencia · 30-45 min con cita previa</div>
        <div class="plan-i"><span>✓</span>Análisis de los 4 pilares consulares</div>
        <div class="plan-i"><span>✓</span>Diagnóstico de fortalezas y riesgos</div>
        <div class="plan-i"><span>✓</span>Recomendaciones personalizadas</div>
        <div class="plan-i"><span>✓</span>Informe escrito 30 días de vigencia</div>
        <div class="plan-i"><span>✓</span>Sesión virtual de orientación</div>
        <button class="plan-btn pb-n" onclick="elegirPlan('virtual','RD\$2,500',2500)">SELECCIONAR VIRTUAL →</button>
      </div>
    </div>
    <div class="plan top">
      <div class="plan-hd">⭐ MÁS COMPLETO</div>
      <div class="plan-bd">
        <div class="plan-ico">🤝</div><h3>Evaluación Presencial</h3>
        <p class="plan-d">Evaluación en persona, con revisión de documentos originales y orientación cara a cara.</p>
        <div class="plan-p">RD\$3,500</div>
        <div class="plan-dur">📅 30 días de vigencia · 30-45 min con cita previa</div>
        <div class="plan-i"><span>✓</span>Todo lo del plan virtual</div>
        <div class="plan-i"><span>✓</span>Revisión de documentos físicos</div>
        <div class="plan-i"><span>✓</span>Orientación presencial personalizada</div>
        <div class="plan-i"><span>✓</span>Práctica de preguntas de entrevista</div>
        <div class="plan-i"><span>✓</span>Informe escrito 30 días de vigencia</div>
        <button class="plan-btn pb-r" onclick="elegirPlan('presencial','RD\$3,500',3500)">SELECCIONAR PRESENCIAL →</button>
      </div>
    </div>
  </div>
  <div style="background:rgba(27,42,74,.04);border:1px solid rgba(27,42,74,.1);border-radius:10px;padding:14px 18px;text-align:center;">
    <p style="color:var(--gray);font-size:13px;line-height:1.7">📋 <strong style="color:var(--navy)">Vigencia 30 días:</strong> El reporte tiene validez de 30 días calendario desde su emisión.</p>
  </div>
</div></sec>

<sec style="background:var(--off)" id="form"><div class="fw">
  <div id="sel-box" class="sel-box" style="display:none">
    <div><span>Plan seleccionado</span><br/><strong id="sp-n"></strong></div>
    <div class="sel-price" id="sp-p"></div>
    <button class="cb-btn" onclick="volverPlanes()">Cambiar</button>
  </div>
  <p class="slbl">PASO 2 — TUS DATOS</p>
  <h2 class="stit">Completa tu información</h2>
  <p class="ssub" style="margin-bottom:28px">Un asesor se comunicará contigo para coordinar la cita de evaluación.</p>
  <div id="blk" class="blk" style="display:none"><div style="font-size:36px;margin-bottom:10px">ℹ️</div><p id="blk-t"></p></div>
  <div id="suc" class="suc" style="display:none"><div style="font-size:48px;margin-bottom:12px">✅</div><h3>¡Solicitud recibida!</h3><p>Serás redirigido a WhatsApp para coordinar tu evaluación de perfil.</p></div>
  <div id="nop" style="text-align:center;padding:40px;color:var(--gray)">
    <div style="font-size:44px;margin-bottom:10px">👆</div>
    <p>Selecciona un plan de evaluación arriba para continuar.</p>
    <a href="#planes" style="display:inline-block;margin-top:14px;background:#E31837;color:#fff;border-radius:8px;padding:11px 22px;font-weight:700;font-size:14px">Ver planes →</a>
  </div>
  <div id="fbox" class="fb" style="display:none">
    <div class="fld"><label>Nombre completo *</label><input type="text" id="nombre" placeholder="Ej. Juan Pérez González"/></div>
    <div class="fld"><label>WhatsApp *</label><input type="tel" id="wa" placeholder="+1 (849) 000-0000"/></div>
    <div class="fld"><label>¿Cuál es tu situación actual? *</label>
      <select id="sit"><option value="">— Selecciona —</option><option>Quiero aplicar por primera vez</option><option>Fui negado y quiero volver a intentarlo</option><option>Tengo cita pero quiero evaluar mi perfil antes</option><option>Quiero saber si vale la pena aplicar</option></select>
    </div>
    <div class="fld"><label>¿Has sido negado/a anteriormente? *</label>
      <div class="rg">
        <label class="rl"><input type="radio" name="neg" value="No, es mi primera vez" onchange="sel('neg','No, es mi primera vez')"/> ✅ No, primera vez</label>
        <label class="rl"><input type="radio" name="neg" value="Sí, una vez" onchange="sel('neg','Sí, una vez')"/> ⚠️ Sí, una vez</label>
        <label class="rl"><input type="radio" name="neg" value="Sí, más de una vez" onchange="sel('neg','Sí, más de una vez')"/> ❌ Más de una</label>
      </div>
    </div>
    <div class="fld">
      <label>¿Tienes documentos de arraigo disponibles? *</label>
      <p style="font-size:12px;color:var(--gray);margin-bottom:7px">Empleo, negocio, bienes, cuenta bancaria, familia en RD</p>
      <div class="rg">
        <label class="rl"><input type="radio" name="doc" value="Sí, tengo varios" onchange="sel('doc','Sí, tengo varios')"/> ✅ Sí, varios</label>
        <label class="rl"><input type="radio" name="doc" value="Algunos, no todos" onchange="sel('doc','Algunos, no todos')"/> ⚠️ Algunos</label>
        <label class="rl"><input type="radio" name="doc" value="Pocos o ninguno" onchange="sel('doc','Pocos o ninguno')"/> ❌ Pocos</label>
      </div>
    </div>
    <div class="fld"><label>Comentario breve <span style="font-weight:400;color:#94a3b8">(opcional)</span></label><textarea id="com" rows="3" placeholder="Ej: trabajo estable, casa propia, negado por 214(b)..."></textarea></div>
    <div class="consent">
      <p>Al solicitar la evaluación, entiendo y acepto que:</p>
      <p>• Evaluación <strong>virtual RD\$2,500</strong> / <strong>presencial RD\$3,500</strong> — con cita previa.</p>
      <p>• Duración: <strong>30 a 45 minutos</strong>. Reporte con <strong>vigencia de 30 días</strong>.</p>
      <p>• <strong>No se garantiza</strong> la aprobación de ninguna visa. Es un diagnóstico profesional honesto.</p>
      <label><input type="checkbox" id="ok"/> Entiendo y acepto las condiciones del servicio.</label>
    </div>
    <div id="err" class="err" style="display:none"></div>
    <button class="bsub" id="btn" onclick="enviar()">EVALUAR MI PERFIL AHORA</button>
    <p class="fnote">🔒 Información confidencial. Un asesor real te contacta directamente.</p>
  </div>
</div></sec>

<sec class="ctaf"><div class="ctr">
  <h2>No inviertas a ciegas. Conoce tu situación real primero.</h2>
  <p>Una orientación honesta hoy puede ahorrarte tiempo, dinero y frustraciones mañana.</p>
  <a href="#planes" class="bctaf">EVALUAR MI PERFIL AHORA →</a>
</div></sec>

<footer>
  <div class="flinks"><a href="https://tengovisard.com" target="_blank">🌐 tengovisard.com</a><a href="https://instagram.com/visaeeuu" target="_blank">📷 @visaeeuu</a></div>
  <div class="legal"><p><strong style="color:rgba(255,255,255,.4)">Aviso legal:</strong> Tengo Visa RD ofrece orientación y evaluación de perfil migratorio como servicio de asesoría privada. No somos representantes del consulado ni garantizamos la aprobación. La decisión final corresponde al oficial consular.</p></div>
  <p class="fcopy">© 2025 Tengo Visa RD · @visaeeuu</p>
</footer>

<script>
const SUPA="$SUPA",KEY="$KEY",WA="$WA";
const rd={};let plan=null,planN='',planM=0;
function sel(g,v){rd[g]=v;document.querySelectorAll('input[name="'+g+'"]').forEach(r=>{r.closest('.rl').classList.toggle('on',r.value===v);});}
function elegirPlan(id,lbl,m){
  plan=id;planN=lbl;planM=m;
  document.getElementById('nop').style.display='none';
  document.getElementById('fbox').style.display='block';
  document.getElementById('sel-box').style.display='flex';
  document.getElementById('sp-n').textContent=id==='virtual'?'Evaluación Virtual':'Evaluación Presencial';
  document.getElementById('sp-p').textContent=lbl;
  document.getElementById('form').scrollIntoView({behavior:'smooth'});
}
function volverPlanes(){
  plan=null;
  document.getElementById('nop').style.display='block';
  document.getElementById('fbox').style.display='none';
  document.getElementById('sel-box').style.display='none';
  document.getElementById('planes').scrollIntoView({behavior:'smooth'});
}
async function enviar(){
  if(!plan){alert('Selecciona un plan primero');return;}
  const n=document.getElementById('nombre').value.trim(),w=document.getElementById('wa').value.trim(),s=document.getElementById('sit').value,neg=rd['neg']||'',doc=rd['doc']||'',com=document.getElementById('com').value.trim(),ok=document.getElementById('ok').checked;
  document.getElementById('err').style.display='none';
  if(!n||!w||!s||!neg||!doc){document.getElementById('err').textContent='Por favor completa todos los campos requeridos.';document.getElementById('err').style.display='block';return;}
  if(!ok){document.getElementById('err').textContent='Debes aceptar las condiciones del servicio para continuar.';document.getElementById('err').style.display='block';return;}
  const btn=document.getElementById('btn');btn.disabled=true;btn.textContent='Enviando...';
  try{
    await fetch(SUPA+'/rest/v1/leads_evaluacion',{method:'POST',headers:{'apikey':KEY,'Authorization':'Bearer '+KEY,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({nombre:n,whatsapp:w,situacion:s,negado_antes:neg,tiene_documentos:doc,listo_para_avanzar:'Sí',comentario:com||null,status:'nuevo'})});
    await fetch(SUPA+'/rest/v1/pagos_evaluacion',{method:'POST',headers:{'apikey':KEY,'Authorization':'Bearer '+KEY,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({nombre:n,whatsapp:w,plan:plan,monto:planM,metodo_pago:'pendiente',status:'pendiente'})});
  }catch(e){}
  document.getElementById('fbox').style.display='none';document.getElementById('sel-box').style.display='none';document.getElementById('suc').style.display='block';
  const msg=encodeURIComponent('Hola Tengo Visa RD. Deseo solicitar una evaluación de mi perfil para visa B1/B2.\n\nPlan: '+(plan==='virtual'?'Virtual - RD$2,500':'Presencial - RD$3,500')+'\nNombre: '+n+'\nWhatsApp: '+w+'\nSituación: '+s+'\nNegado antes: '+neg+'\nDocumentos: '+doc+(com?'\nComentario: '+com:''));
  window.open('https://wa.me/'+WA+'?text='+msg,'_blank');
}
</script></body></html>
HTML;

// ═══════════════════════════════════════════════════
// CREAR ARCHIVOS
// ═══════════════════════════════════════════════════

$log[] = mkd("$BASE/landing-cita");
$log[] = mkd("$BASE/landing-asesores");
$log[] = mkd("$BASE/landing-evaluacion");

$log[] = writeFile("$BASE/landing-cita/index.html",       $htmlA);
$log[] = writeFile("$BASE/landing-asesores/index.html",   $htmlB);
$log[] = writeFile("$BASE/landing-evaluacion/index.html", $htmlC);

// Verificar que los archivos existen
$urls = [
    'landing-cita'       => "$BASE/landing-cita/index.html",
    'landing-asesores'   => "$BASE/landing-asesores/index.html",
    'landing-evaluacion' => "$BASE/landing-evaluacion/index.html",
];
$ok = true;
foreach ($urls as $name => $path) {
    if (file_exists($path)) {
        $log[] = "✅ $name — OK (" . round(filesize($path)/1024,1) . " KB)";
    } else {
        $log[] = "❌ $name — NO SE CREÓ";
        $ok = false;
    }
}

// Auto-eliminar este script
@unlink(__FILE__);
$log[] = "🗑️ Script eliminado del servidor.";

// Reporte
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/><title>Instalador Landings — TengoVisa RD</title>
<style>body{font-family:system-ui,sans-serif;max-width:700px;margin:40px auto;padding:20px;background:#f8f9fc;}h1{color:#1B2A4A;margin-bottom:24px;}li{padding:6px 0;border-bottom:1px solid #eee;font-size:14px;}.ok{color:#16a34a;font-weight:700;}.err{color:#E31837;font-weight:700;}a{display:inline-block;margin:6px 4px;padding:10px 18px;background:#1B2A4A;color:#fff;text-decoration:none;border-radius:8px;font-size:13px;font-weight:700;}</style>
</head>
<body>
<h1><?= $ok ? '✅ Instalación completada' : '⚠️ Instalación con errores' ?></h1>
<ul>
<?php foreach($log as $l): ?>
  <li><?= htmlspecialchars($l) ?></li>
<?php endforeach; ?>
</ul>
<h2 style="margin-top:28px;color:#1B2A4A">Verificar estas URLs:</h2>
<a href="https://crm.tengovisard.com/landing-cita/" target="_blank">Landing A — Cliente con Cita</a>
<a href="https://crm.tengovisard.com/landing-asesores/" target="_blank">Landing B — Asesores</a>
<a href="https://crm.tengovisard.com/landing-evaluacion/" target="_blank">Landing C — Evaluación</a>
</body>
</html>
