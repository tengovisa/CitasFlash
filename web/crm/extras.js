// ── EXPORT UTILS ──
function exportToCSV(data,filename){
  if(!data||!data.length){toast('Sin datos','error');return;}
  var keys=Object.keys(data[0]);
  var header=keys.join(',');
  var rows=data.map(function(r){
    return keys.map(function(k){
      var v=r[k]===null||r[k]===undefined?'':String(r[k]);
      return '"'+v.replace(/"/g,'""')+'"';
    }).join(',');
  });
  var csv=[header].concat(rows).join('\r\n');
  var blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});
  var a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=filename+'_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
  toast('Descargado: '+filename+'.csv');
}

function exportToPDF(titulo,data,filename){
  if(!data||!data.length){toast('Sin datos','error');return;}
  var keys=Object.keys(data[0]);
  var rows=data.map(function(r){
    return '<tr>'+keys.map(function(k){return '<td>'+(r[k]||'')+'</td>';}).join('')+'</tr>';
  }).join('');
  var w=window.open('','_blank');
  w.document.write('<!DOCTYPE html><html><head><meta charset="utf-8"><title>'+titulo+'</title><style>body{font-family:Arial;font-size:11px;padding:20px}h1{color:#8b0000}table{width:100%;border-collapse:collapse}th{background:#8b0000;color:white;padding:6px;text-align:left}td{padding:4px 6px;border-bottom:1px solid #eee}</style></head><body><h1>TengoVisa RD — '+titulo+'</h1><p style="font-size:10px">'+new Date().toLocaleString('es-DO')+' | '+data.length+' registros</p><table><thead><tr>'+keys.map(function(k){return '<th>'+k+'</th>';}).join('')+'</tr></thead><tbody>'+rows+'</tbody></table><script>window.print();<\/script></body></html>');
}

function copyLink(path){
  var url=window.location.origin+path;
  navigator.clipboard.writeText(url).then(function(){toast('Link copiado');}).catch(function(){toast('Error','error');});
}

// ── EXPORT POR MÓDULO ──
async function exportEvals(){var d=await api('/crm/evaluaciones');exportToCSV(d,'evaluaciones');}
async function exportEvalsPDF(){var d=await api('/crm/evaluaciones');exportToPDF('Evaluaciones',d,'evaluaciones');}
async function exportPagosExcel(){var d=await api('/clientes/lista');exportToCSV(d,'pagos');}
async function exportPagosPDF(){var d=await api('/clientes/lista');exportToPDF('Pagos',d,'pagos');}
async function exportSeguimientos(){var d=await api('/clientes/lista');exportToCSV(d,'seguimientos');}
async function exportSeguimientosPDF(){var d=await api('/clientes/lista');exportToPDF('Seguimientos',d,'seguimientos');}
async function exportReporteExcel(){var d=await api('/clientes/lista');exportToCSV(d,'reporte');}
async function exportReportePDF(){var d=await api('/clientes/lista');exportToPDF('Reporte Ejecutivo',d,'reporte');}
async function exportProspectosExcel(){var d=await api('/leads');exportToCSV(d,'prospectos');}

// ── WA ──
function waCliente(whatsapp,nombre){
  var num=(whatsapp||'').replace(/\D/g,'');
  if(!num){toast('Sin WhatsApp','error');return;}
  var msg=encodeURIComponent('Hola '+( nombre||'')+', le contactamos de TengoVisa RD. ');
  window.open('https://wa.me/1'+num+'?text='+msg,'_blank');
}

async function agregarNotaSeguimiento(clienteId,nota){
  if(!nota){toast('Escribe una nota','error');return;}
  var r=await api('/clientes/'+clienteId,{method:'PUT',body:JSON.stringify({observaciones:nota,ultimo_contacto:new Date().toISOString().slice(0,10)})});
  if(r.ok) toast('Nota guardada');
  else toast('Error','error');
}

// ── PROSPECTOS ──
async function loadProspectos(){
  var leads=await api('/leads');
  if(!leads||!leads.length){
    if(document.getElementById('prospTabla')) document.getElementById('prospTabla').innerHTML='<div class="empty">Sin prospectos</div>';
    return;
  }
  S.allLeads=leads;
  var nuevo=leads.filter(function(l){return l.estado==='nuevo';}).length;
  var contactado=leads.filter(function(l){return l.estado==='contactado';}).length;
  var calificado=leads.filter(function(l){return l.estado==='calificado';}).length;
  if(document.getElementById('pst-total')) document.getElementById('pst-total').textContent=leads.length;
  if(document.getElementById('pst-nuevo')) document.getElementById('pst-nuevo').textContent=nuevo;
  if(document.getElementById('pst-contactado')) document.getElementById('pst-contactado').textContent=contactado;
  if(document.getElementById('pst-calificado')) document.getElementById('pst-calificado').textContent=calificado;
  var rows=leads.map(function(l){
    var waNum=(l.whatsapp||'').replace(/\D/g,'');
    var waLink=waNum?'https://wa.me/1'+waNum+'?text=Hola%20'+encodeURIComponent(l.nombre||'')+'%2C%20le%20contactamos%20de%20TengoVisa%20RD':'#';
    return '<div style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;padding:10px;border-bottom:1px solid var(--border);align-items:center;font-size:12px"><div><b>'+(l.nombre||'')+' '+(l.apellido||'')+'</b><br><span style="color:var(--text-faint)">'+(l.email||'')+'</span></div><div>'+(l.whatsapp||'—')+'<br><span style="color:var(--text-faint)">'+(l.origen||'directo')+'</span></div><div><span class="badge b-'+(l.estado==='calificado'?'success':l.estado==='nuevo'?'warning':'gray')+'">'+(l.estado||'nuevo')+'</span><br><span style="color:var(--text-faint)">Score: '+(l.score||0)+'</span></div><div style="display:flex;gap:4px;flex-wrap:wrap">'+(waNum?'<a href="'+waLink+'" target="_blank" class="btn btn-g btn-sm" style="text-decoration:none">💬 WA</a>':'')+'<button class="btn btn-p btn-sm" onclick="convertirLeadACliente(\''+l.id+'\')">👤 Crear</button></div></div>';
  }).join('');
  if(document.getElementById('prospTabla')) document.getElementById('prospTabla').innerHTML=rows;
}

async function guardarProspecto(){
  var data={
    nombre:document.getElementById('np-nombre')&&document.getElementById('np-nombre').value||'',
    apellido:document.getElementById('np-apellido')&&document.getElementById('np-apellido').value||'',
    whatsapp:document.getElementById('np-whatsapp')&&document.getElementById('np-whatsapp').value||'',
    email:document.getElementById('np-email')&&document.getElementById('np-email').value||'',
    origen:document.getElementById('np-origen')&&document.getElementById('np-origen').value||'directo',
    notas:document.getElementById('np-nota')&&document.getElementById('np-nota').value||'',
    estado:'nuevo'
  };
  if(!data.nombre){toast('Nombre requerido','error');return;}
  var r=await api('/leads',{method:'POST',body:JSON.stringify(data)});
  if(r.ok||r.id){
    toast('Prospecto guardado');
    ['np-nombre','np-apellido','np-whatsapp','np-email','np-nota'].forEach(function(id){var el=document.getElementById(id);if(el)el.value='';});
    loadProspectos();
  } else toast('Error: '+(r.error||''),'error');
}

async function convertirLeadACliente(leadId){
  if(!confirm('Crear cliente desde este prospecto?')) return;
  var leads=S.allLeads||[];
  var lead=leads.find(function(l){return l.id===leadId;});
  if(!lead){toast('Lead no encontrado','error');return;}
  var r=await api('/clientes',{method:'POST',body:JSON.stringify({nombre:lead.nombre,apellido:lead.apellido,correo:lead.email,whatsapp:lead.whatsapp,lead_id:leadId,estado_caso:'nuevo',fecha_inicio:new Date().toISOString().slice(0,10)})});
  if(r.ok){toast('Cliente '+r.codigo+' creado');navigate('clientes');}
  else toast('Error: '+(r.error||''),'error');
}

function crearClienteDesdeProspecto(){navigate('prospectos');}

// ── FORMULARIOS ──
function loadFormularios(){}

// ── CONFIG ──
async function loadConfig(){
  try{
    var t=await api('/tarifas');
    if(t&&t.length&&document.getElementById('cfgTarifas')){
      document.getElementById('cfgTarifas').innerHTML=t.map(function(tar){return '<div style="display:grid;grid-template-columns:1fr auto;gap:8px;padding:8px;border-bottom:1px solid var(--border);font-size:12px"><div><b>'+(tar.nombre||tar.servicio||'')+'</b></div><div style="font-weight:800;color:var(--success)">RD$ '+Number(tar.precio||0).toLocaleString('es-DO')+'</div></div>';}).join('');
    }
  }catch(e){}
  if(document.getElementById('cfgUsuarios')){
    document.getElementById('cfgUsuarios').innerHTML='<div style="font-size:12px;padding:8px"><div style="padding:6px 0;border-bottom:1px solid var(--border)"><b>admin@citaflash.com</b> — Administrador <span class="badge b-success">Activo</span></div><div style="padding:6px 0;border-bottom:1px solid var(--border)"><b>TengoVisa RD</b> — CRM Principal <span class="badge b-success">Activo</span></div></div>';
  }
}

// ── HISTORY BACK ──
window.addEventListener('popstate',function(e){
  if(e.state&&e.state.view) navigate(e.state.view,e.state.param);
  else navigate('dashboard');
});

// ── BOTONES EDITAR/ELIMINAR CLIENTES ──
async function eliminarCliente(id, nombre){
  if(!confirm('Eliminar cliente '+nombre+'? Esta acción no se puede deshacer.')) return;
  var r=await api('/clientes/'+id,{method:'DELETE'});
  if(r.ok){toast('Cliente eliminado');S.curCli=null;document.getElementById('cliDetalle').innerHTML='<div class="empty">Selecciona un cliente</div>';loadClientes();}
  else toast('Error: '+(r.error||''),'error');
}

async function guardarClienteRapido(id){
  if(!id){toast('Sin cliente','error');return;}
  var campos=['nombre','apellido','correo','whatsapp','cedula','ciudad','estado_caso','tipo_servicio','monto_total','observaciones'];
  var data={};
  campos.forEach(function(k){
    var el=document.getElementById('fc_'+k)||document.getElementById('fi_'+k);
    if(el) data[k]=el.value||'';
  });
  var r=await api('/clientes/'+id,{method:'PUT',body:JSON.stringify(data)});
  if(r.ok) toast('✅ Cliente guardado');
  else toast('Error: '+(r.error||''),'error');
}

// ── SEGUIMIENTOS — nota de gestión ──
async function agregarNotaGestion(clienteId){
  var nota=document.getElementById('nota-gestion-'+clienteId);
  if(!nota||!nota.value.trim()){toast('Escribe una nota','error');return;}
  var fecha=new Date().toLocaleDateString('es-DO');
  var c=S.clientes.find(function(x){return x.id===clienteId;})||{};
  var obs_anterior=c.observaciones||'';
  var nueva_obs='['+fecha+'] '+nota.value.trim()+(obs_anterior?'\n'+obs_anterior:'');
  var r=await api('/clientes/'+clienteId,{method:'PUT',body:JSON.stringify({
    observaciones:nueva_obs,
    ultimo_contacto:new Date().toISOString().slice(0,10)
  })});
  if(r.ok){
    toast('✅ Nota guardada');
    nota.value='';
    loadSeguimientos();
    loadClientes();
  } else toast('Error','error');
}

// ── REPORTES MEJORADOS ──
async function loadReportesCompleto(){
  var el=document.getElementById('repContent');
  if(el) el.innerHTML='<div class="empty">⏳ Cargando...</div>';
  var clientes=await api('/clientes/lista');
  var leads=await api('/leads');
  var c=Array.isArray(clientes)?clientes:[];
  var l=Array.isArray(leads)?leads:[];
  
  var total=c.length;
  var en_proceso=c.filter(function(x){return x.estado_caso==='en_proceso';}).length;
  var cita=c.filter(function(x){return x.estado_caso==='cita_agendada';}).length;
  var cobrado=c.reduce(function(s,x){return s+(x.monto_pagado||0);},0);
  var pendiente=c.reduce(function(s,x){return s+(x.monto_total||0)-(x.monto_pagado||0);},0);

  if(!el) return;
  el.innerHTML='<div class="stats-row" style="margin-bottom:14px">'
    +'<div class="stat-card"><div class="stat-ico" style="background:var(--info-soft)">👥</div><div class="stat-val">'+total+'</div><div class="stat-lbl">Clientes</div></div>'
    +'<div class="stat-card"><div class="stat-ico" style="background:var(--warning-soft)">⏳</div><div class="stat-val">'+en_proceso+'</div><div class="stat-lbl">En Proceso</div></div>'
    +'<div class="stat-card"><div class="stat-ico" style="background:var(--success-soft)">📅</div><div class="stat-val">'+cita+'</div><div class="stat-lbl">Citas</div></div>'
    +'<div class="stat-card"><div class="stat-ico" style="background:#F5F0FF">💰</div><div class="stat-val">RD$'+cobrado.toLocaleString('es-DO')+'</div><div class="stat-lbl">Cobrado</div></div>'
    +'<div class="stat-card"><div class="stat-ico" style="background:var(--tv-red-soft)">⏰</div><div class="stat-val">RD$'+pendiente.toLocaleString('es-DO')+'</div><div class="stat-lbl">Pendiente</div></div>'
    +'</div>'
    +'<div class="sec"><div class="sec-h"><div class="sec-t">📊 Clientes por Estado</div>'
    +'<div style="display:flex;gap:6px"><button class="btn btn-outline btn-sm" onclick="exportReporteExcel()">📥 Excel</button>'
    +'<button class="btn btn-outline btn-sm" onclick="exportReportePDF()">📄 PDF</button></div></div>'
    +'<div class="sec-b" id="repTabla"></div></div>'
    +'<div class="sec" style="margin-top:14px"><div class="sec-h"><div class="sec-t">📋 Prospectos ('+l.length+')</div>'
    +'<button class="btn btn-outline btn-sm" onclick="exportProspectosExcel()">📥 Excel</button></div>'
    +'<div class="sec-b" style="font-size:12px;padding:10px">'+l.length+' leads registrados | '
    +l.filter(function(x){return x.estado==='calificado';}).length+' calificados | '
    +l.filter(function(x){return x.estado==='nuevo';}).length+' nuevos</div></div>';

  // Tabla clientes
  var tbody=c.map(function(x){
    return '<tr><td><b>'+(x.nombre||'')+' '+(x.apellido||'')+'</b></td>'
      +'<td style="font-family:monospace;color:var(--tv-blue)">'+(x.codigo||'—')+'</td>'
      +'<td>'+(x.tipo_servicio||'—')+'</td>'
      +'<td><span class="badge b-'+(x.estado_caso==='en_proceso'?'warning':x.estado_caso==='cita_agendada'?'success':'gray')+'">'+(x.estado_caso||'nuevo')+'</span></td>'
      +'<td>RD$ '+(x.monto_total||0).toLocaleString('es-DO')+'</td>'
      +'<td>RD$ '+(x.monto_pagado||0).toLocaleString('es-DO')+'</td>'
      +'<td>'+(x.asesor||'—')+'</td></tr>';
  }).join('');
  var repTabla=document.getElementById('repTabla');
  if(repTabla) repTabla.innerHTML='<table class="tbl"><thead><tr><th>Cliente</th><th>Código</th><th>Servicio</th><th>Estado</th><th>Total</th><th>Pagado</th><th>Asesor</th></tr></thead><tbody>'+tbody+'</tbody></table>';
  S._reporteData=c;
}

// Override loadReportes
var _origLoadReportes=typeof loadReportes==='function'?loadReportes:null;
function loadReportes(){loadReportesCompleto();}


// ── SYNC SCHEDULE IDS GLOBAL ──
async function syncTodosSchedules(){
  toast('🔄 Sincronizando citas...');
  var r=await api('/sync/schedule-ids',{method:'POST',body:JSON.stringify({})});
  if(r.ok){
    toast('✅ '+r.actualizados+' actualizados');
    if(r.actualizados>0 && S.curCli) abrirCli(S.curCli.id);
  } else toast('Error: '+(r.error||''),'error');
}

// Agregar botón sync al dashboard
document.addEventListener('DOMContentLoaded',function(){
  setTimeout(function(){
    var hdr=document.querySelector('.top-bar .view-actions');
    if(hdr&&!document.getElementById('btnSyncSchedule')){
      var btn=document.createElement('button');
      btn.id='btnSyncSchedule';
      btn.className='btn btn-outline btn-sm';
      btn.innerHTML='🔄 Sync Citas';
      btn.onclick=syncTodosSchedules;
      hdr.prepend(btn);
    }
  },2000);
});
// ── HISTORY BACK ──
(function(){
  var _orig = window.navigate || function(){};
  var _nav = function(view, param){
    try{history.pushState({view:view,param:param||null},'','#'+view+(param?'/'+param:''));}catch(e){}
    if(typeof loadEvals==='function'&&window.navigate) window.navigate(view,param);
  };
  window.addEventListener('popstate',function(e){
    if(e.state&&e.state.view && typeof navigate==='function') navigate(e.state.view,e.state.param);
    else if(typeof navigate==='function') navigate('dashboard');
  });
})();

// ── MARKDOWN RENDERER PARA IA ──
function renderMarkdown(text){
  if(!text) return '';
  return text
    // Tablas
    .replace(/\|(.+)\|/g, function(match){
      var cells = match.split('|').filter(function(c){return c.trim();});
      var isHeader = false;
      return '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:11px">' +
        '<tr>' + cells.map(function(c){
          return '<td style="padding:4px 8px;border:1px solid var(--border);background:var(--bg-soft)">' + c.trim() + '</td>';
        }).join('') + '</tr></table>';
    })
    // Headers
    .replace(/^## (.+)$/gm,'<h3 style="font-size:13px;font-weight:800;color:var(--tv-blue);margin:14px 0 6px;border-bottom:1px solid var(--border);padding-bottom:4px">$1</h3>')
    .replace(/^### (.+)$/gm,'<h4 style="font-size:12px;font-weight:700;color:var(--text);margin:10px 0 4px">$1</h4>')
    .replace(/^# (.+)$/gm,'<h2 style="font-size:15px;font-weight:900;color:var(--tv-red);margin:12px 0 8px">$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g,'<b>$1</b>')
    // Italic
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    // Code blocks
    .replace(/```[\w]*\n?([\s\S]*?)```/gm,'<pre style="background:var(--bg-soft);padding:10px;border-radius:6px;font-size:10px;overflow-x:auto;border:1px solid var(--border)">$1</pre>')
    // Inline code
    .replace(/`(.+?)`/g,'<code style="background:var(--bg-soft);padding:2px 5px;border-radius:3px;font-size:10px">$1</code>')
    // Checkboxes
    .replace(/- \[ \] (.+)/g,'<div style="padding:3px 0;display:flex;gap:6px;align-items:center"><input type="checkbox" style="cursor:pointer"> <span style="font-size:11px">$1</span></div>')
    .replace(/- \[x\] (.+)/gi,'<div style="padding:3px 0;display:flex;gap:6px;align-items:center"><input type="checkbox" checked style="cursor:pointer"> <span style="font-size:11px;text-decoration:line-through;color:var(--text-faint)">$1</span></div>')
    // Lists
    .replace(/^- (.+)$/gm,'<div style="padding:2px 0 2px 12px;font-size:11px">• $1</div>')
    .replace(/^\d+\. (.+)$/gm,'<div style="padding:2px 0 2px 12px;font-size:11px">$1</div>')
    // Blockquote
    .replace(/^> (.+)$/gm,'<blockquote style="border-left:3px solid var(--tv-blue);padding:6px 10px;margin:6px 0;background:var(--info-soft);font-size:11px;border-radius:0 4px 4px 0">$1</blockquote>')
    // Emojis score colores
    .replace(/🟢/g,'<span style="color:#16a34a">🟢</span>')
    .replace(/🔴/g,'<span style="color:#dc2626">🔴</span>')
    .replace(/🟡/g,'<span style="color:#ca8a04">🟡</span>')
    .replace(/🟠/g,'<span style="color:#ea580c">🟠</span>')
    // Separadores
    .replace(/^---$/gm,'<hr style="border:none;border-top:1px solid var(--border);margin:12px 0">')
    // Saltos de línea
    .replace(/\n\n/g,'<br><br>')
    .replace(/\n/g,'<br>');
}

// ── MOBILE MENU ──
function toggleMobileMenu(){
  var sb=document.querySelector('.sidebar');
  var ov=document.getElementById('sidebarOverlay');
  if(sb) sb.classList.toggle('mobile-open');
  if(ov) ov.classList.toggle('active');
}
function closeMobileMenu(){
  var sb=document.querySelector('.sidebar');
  var ov=document.getElementById('sidebarOverlay');
  if(sb) sb.classList.remove('mobile-open');
  if(ov) ov.classList.remove('active');
}
// Cerrar menú al navegar en mobile
var _origNav=window.navigate;
window.addEventListener('DOMContentLoaded',function(){
  if(window.innerWidth<=768){
    document.querySelectorAll('.nav-item').forEach(function(el){
      el.addEventListener('click',closeMobileMenu);
    });
  }
});
// Swipe para abrir/cerrar sidebar en mobile
(function(){
  var startX=0;
  document.addEventListener('touchstart',function(e){startX=e.touches[0].clientX;},{passive:true});
  document.addEventListener('touchend',function(e){
    var dx=e.changedTouches[0].clientX-startX;
    if(dx>60&&startX<30) toggleMobileMenu();
    if(dx<-60) closeMobileMenu();
  },{passive:true});
})();

// ── PANEL REDES ──
var BOT_CONFIG = {
  hora_inicio: 22, hora_fin: 8,
  precio_eval: 2000, precio_ds160: 5000,
  precio_visa: 15000, precio_cita: 8000,
  tel_asesor: '+18499189998',
  twilio_sid: '', twilio_token: '', twilio_num: ''
};

async function loadRedes(){
  // Stats
  var leads=await api('/leads');
  var hoy=new Date().toISOString().slice(0,10);
  var leadsHoy=(leads||[]).filter(function(l){return (l.created_at||'').startsWith(hoy);});
  var waHoy=leadsHoy.filter(function(l){return (l.origen||'').includes('whatsapp');}).length;
  var igHoy=leadsHoy.filter(function(l){return (l.origen||'').includes('instagram');}).length;

  if(document.getElementById('rs-wa')) document.getElementById('rs-wa').textContent=waHoy;
  if(document.getElementById('rs-ig')) document.getElementById('rs-ig').textContent=igHoy;
  if(document.getElementById('rs-leads')) document.getElementById('rs-leads').textContent=leadsHoy.length;
  if(document.getElementById('rs-email')) document.getElementById('rs-email').textContent='—';

  // Estado bot
  try{
    var h=await fetch('http://localhost:8002/health' /* no disponible desde browser */);
    var st=document.getElementById('wa-status');
    if(st) st.textContent='Activo';
  }catch{}

  loadLeadsRedes();
}

async function loadLeadsRedes(){
  var leads=await api('/leads');
  var redesLeads=(leads||[]).filter(function(l){
    return ['whatsapp','instagram','facebook','meta'].some(function(o){return (l.origen||'').includes(o);});
  });
  var el=document.getElementById('redesLeads');
  if(!el) return;
  if(!redesLeads.length){el.innerHTML='<div class="empty">Sin leads de redes aún</div>';return;}
  el.innerHTML='<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Nombre</th><th>WhatsApp</th><th>Origen</th><th>Fecha</th><th>Acción</th></tr></thead><tbody>'+
    redesLeads.map(function(l){
      var wa=(l.whatsapp||'').replace(/\D/g,'');
      return '<tr><td><b>'+(l.nombre||'')+'</b></td><td>'+(l.whatsapp||'—')+'</td><td><span class="badge b-'+(l.origen&&l.origen.includes('whatsapp')?'success':'info')+'">'+( l.origen||'directo')+'</span></td><td>'+(l.created_at||'').slice(0,10)+'</td><td><div style="display:flex;gap:4px">'+(wa?'<a href="https://wa.me/1'+wa+'" target="_blank" class="btn btn-g btn-sm">💬</a>':'')+'<button class="btn btn-p btn-sm" onclick="convertirLeadACliente(\''+l.id+'\')">👤</button></div></td></tr>';
    }).join('')+
  '</tbody></table></div>';
}

function openBotConfig(){
  var sec=document.getElementById('secBotConfig');
  if(sec){sec.style.display='block';sec.scrollIntoView({behavior:'smooth'});}
  // Cargar config guardada
  var saved=localStorage.getItem('botConfig');
  if(saved){
    var c=JSON.parse(saved);
    if(document.getElementById('bot-hora-inicio')) document.getElementById('bot-hora-inicio').value=c.hora_inicio||22;
    if(document.getElementById('bot-hora-fin')) document.getElementById('bot-hora-fin').value=c.hora_fin||8;
    if(document.getElementById('bot-precio-eval')) document.getElementById('bot-precio-eval').value=c.precio_eval||2000;
    if(document.getElementById('bot-precio-ds160')) document.getElementById('bot-precio-ds160').value=c.precio_ds160||5000;
    if(document.getElementById('bot-precio-visa')) document.getElementById('bot-precio-visa').value=c.precio_visa||15000;
    if(document.getElementById('bot-precio-cita')) document.getElementById('bot-precio-cita').value=c.precio_cita||8000;
    if(document.getElementById('bot-tel-asesor')) document.getElementById('bot-tel-asesor').value=c.tel_asesor||'+18499189998';
    if(document.getElementById('bot-twilio-num')) document.getElementById('bot-twilio-num').value=c.twilio_num||'';
  }
}

function cerrarBotConfig(){
  var sec=document.getElementById('secBotConfig');
  if(sec) sec.style.display='none';
}

async function guardarBotConfig(){
  var config={
    hora_inicio:parseInt(document.getElementById('bot-hora-inicio')?.value||22),
    hora_fin:parseInt(document.getElementById('bot-hora-fin')?.value||8),
    precio_eval:parseInt(document.getElementById('bot-precio-eval')?.value||2000),
    precio_ds160:parseInt(document.getElementById('bot-precio-ds160')?.value||5000),
    precio_visa:parseInt(document.getElementById('bot-precio-visa')?.value||15000),
    precio_cita:parseInt(document.getElementById('bot-precio-cita')?.value||8000),
    tel_asesor:document.getElementById('bot-tel-asesor')?.value||'+18499189998',
    twilio_sid:document.getElementById('bot-twilio-sid')?.value||'',
    twilio_token:document.getElementById('bot-twilio-token')?.value||'',
    twilio_num:document.getElementById('bot-twilio-num')?.value||''
  };
  localStorage.setItem('botConfig',JSON.stringify(config));
  BOT_CONFIG=config;

  // Actualizar el bot en el servidor
  try{
    await fetch('/api/bot/config',{
      method:'POST',
      headers:{'Content-Type':'application/json','x-api-key':'TengoVisa2026API'},
      body:JSON.stringify(config)
    });
  }catch{}

  toast('✅ Configuración guardada — precios y horario actualizados');
  cerrarBotConfig();
}

async function testWebhookWA(){
  try{
    var r=await fetch('/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=TengoVisaBot2026&hub.challenge=TEST123');
    var text=await r.text();
    if(text==='TEST123') toast('✅ Webhook WhatsApp OK');
    else toast('Webhook responde: '+text.slice(0,50));
  }catch(e){toast('Error: '+e.message,'error');}
}

async function testEmail(){
  toast('📤 Enviando email de prueba...');
  try{
    var r=await api('/ia/analizar',{method:'POST',body:JSON.stringify({prompt:'test',tipo:'test'})});
    toast('✅ API activa');
  }catch{toast('Error','error');}
}

function openWAConfig(){openBotConfig();}

// ── BOT REDES ──
var botRespEditando = null;

async function loadBotRedes(){
  var data = await api('/bot/respuestas');
  var respuestas = (data.respuestas || []);
  var el = document.getElementById('botRespestasList');
  if(!el) return;
  if(!respuestas.length){
    el.innerHTML='<div class="empty">Sin respuestas configuradas.<br><button class="btn btn-p btn-sm" onclick="nuevaRespuestaBot()" style="margin-top:8px">+ Agregar primera respuesta</button></div>';
    return;
  }
  el.innerHTML = respuestas.map(function(r){
    var keys = (r.palabras_clave||[]).join(', ');
    var preview = (r.respuesta||'').slice(0,120).replace(/\n/g,' ');
    return '<div class="sec" style="margin-bottom:10px"><div class="sec-h">'
      +'<div><div class="sec-t">'+r.categoria+'</div>'
      +'<div style="font-size:10px;color:var(--tv-blue);margin-top:2px">🔑 '+keys+'</div></div>'
      +'<div style="display:flex;gap:4px">'
      +'<button class="btn btn-outline btn-sm" onclick="editarRespuestaBot(\''+r.id+'\')">✏️ Editar</button>'
      +'<button class="btn btn-d btn-sm" onclick="eliminarRespuestaBot(\''+r.id+'\')">🗑</button>'
      +'</div></div>'
      +'<div class="sec-b" style="padding:10px 14px">'
      +'<div style="font-size:12px;color:var(--text-soft);white-space:pre-wrap;font-family:monospace;background:var(--bg-soft);padding:8px;border-radius:6px;max-height:120px;overflow-y:auto">'+preview+'...</div>'
      +'</div></div>';
  }).join('');
}

function nuevaRespuestaBot(){
  botRespEditando = null;
  document.getElementById('bot-resp-id').value = '';
  document.getElementById('bot-cat').value = '';
  document.getElementById('bot-keys').value = '';
  document.getElementById('bot-resp-texto').value = '';
  document.getElementById('formBotTitulo').textContent = '➕ Nueva Respuesta';
  var form = document.getElementById('formBotResp');
  if(form){form.style.display='block';form.scrollIntoView({behavior:'smooth'});}
}

async function editarRespuestaBot(id){
  var data = await api('/bot/respuestas');
  var r = (data.respuestas||[]).find(function(x){return x.id===id;});
  if(!r) return;
  botRespEditando = id;
  document.getElementById('bot-resp-id').value = id;
  document.getElementById('bot-cat').value = r.categoria||'';
  document.getElementById('bot-keys').value = (r.palabras_clave||[]).join(', ');
  document.getElementById('bot-resp-texto').value = r.respuesta||'';
  document.getElementById('formBotTitulo').textContent = '✏️ Editar: '+r.categoria;
  var form = document.getElementById('formBotResp');
  if(form){form.style.display='block';form.scrollIntoView({behavior:'smooth'});}
}

async function guardarRespuestaBot(){
  var cat = document.getElementById('bot-cat')?.value?.trim();
  var keys = document.getElementById('bot-keys')?.value?.trim();
  var resp = document.getElementById('bot-resp-texto')?.value?.trim();
  if(!cat||!keys||!resp){toast('Completa todos los campos','error');return;}
  
  var id = botRespEditando || cat.toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');
  var body = {
    id: id,
    categoria: cat,
    palabras_clave: keys.split(',').map(function(k){return k.trim().toLowerCase();}),
    respuesta: resp
  };
  
  var r = await api('/bot/respuestas/'+id, {method:'PUT', body:JSON.stringify(body)});
  if(r.ok){
    toast('✅ Respuesta guardada — activa en WhatsApp, FB e Instagram');
    cerrarFormBot();
    loadBotRedes();
    // Recargar bot
    fetch('/api/bot/config',{method:'POST',headers:{'Content-Type':'application/json','x-api-key':'TengoVisa2026API'},body:JSON.stringify({reload:true})}).catch(function(){});
  } else toast('Error: '+(r.error||''),'error');
}

async function eliminarRespuestaBot(id){
  if(!confirm('¿Eliminar esta respuesta del bot?')) return;
  var r = await api('/bot/respuestas/'+id, {method:'DELETE'});
  if(r.ok){toast('✅ Eliminada');loadBotRedes();}
  else toast('Error','error');
}

async function probarRespuestaBot(){
  var keys = document.getElementById('bot-keys')?.value||'';
  var primera = keys.split(',')[0]?.trim()||'hola';
  toast('Probando con: "'+primera+'"...');
  try{
    var r = await fetch('/api/bot/test?msg='+encodeURIComponent(primera),{headers:{'x-api-key':'TengoVisa2026API'}});
    var d = await r.json();
    if(d.respuesta) toast('Bot respondería: '+d.respuesta.slice(0,80)+'...');
    else toast('Sin respuesta para "'+primera+'"','error');
  }catch{toast('Bot no disponible','error');}
}

function cerrarFormBot(){
  var form = document.getElementById('formBotResp');
  if(form) form.style.display='none';
  botRespEditando = null;
}

// ── GOOGLE CALENDAR CITAS ──
async function loadCitasHoy(){
  var el = document.getElementById('citasHoyList');
  if(el) el.innerHTML = '<div class="empty">⏳ Sincronizando...</div>';
  try{
    var citas = await api('/calendar/citas-hoy');
    if(!el) return;
    if(!Array.isArray(citas)||!citas.length){
      el.innerHTML='<div class="empty">Sin citas hoy 📅</div>';return;
    }
    el.innerHTML = citas.map(function(c){
      return '<div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:6px;background:var(--bg-soft);margin-bottom:6px">'
        +'<div style="background:var(--tv-red);color:white;border-radius:6px;padding:4px 8px;font-size:11px;font-weight:700;white-space:nowrap">'+c.inicio.slice(11,16)+'</div>'
        +'<div style="flex:1"><div style="font-size:12px;font-weight:700">'+c.titulo+'</div>'
        +(c.email_cliente?'<div style="font-size:10px;color:var(--text-faint)">'+c.email_cliente+'</div>':'')+'</div>'
        +(c.email_cliente?'<a href="mailto:'+c.email_cliente+'" class="btn btn-outline btn-sm">📧</a>':'')
        +'</div>';
    }).join('');
  }catch(e){
    if(el) el.innerHTML='<div class="empty">Error cargando citas</div>';
  }
}

// Cargar citas al abrir dashboard
var _origLoadDash = window.loadDashboard;
window.loadDashboard = function(){
  if(_origLoadDash) _origLoadDash();
  setTimeout(loadCitasHoy, 1000);
};

// ── PANEL REDES CHAT ──
var waContactos = [];
var waContactoActivo = null;

function showRedesTab(tab){
  ['wa','ig','fb','email'].forEach(function(t){
    var panel = document.getElementById('rpanel-'+t);
    var btn = document.getElementById('rtab-'+t);
    if(panel) panel.style.display = t===tab ? 'flex' : 'none';
    if(btn){
      btn.style.borderBottomColor = t===tab ? 'var(--tv-red)' : 'transparent';
      btn.style.fontWeight = t===tab ? '700' : '400';
    }
  });
  if(tab==='wa') loadWAMessages();
}

async function loadRedes(){
  document.getElementById('rs-wa-count') && (document.getElementById('rs-wa-count').textContent='...');
  await loadWAMessages();
}

async function loadWAMessages(){
  var el = document.getElementById('waContactos');
  if(el) el.innerHTML='<div class="empty" style="padding:20px">⏳ Cargando mensajes...</div>';
  try{
    var data = await api('/redes/mensajes-wa');
    if(!data.ok){
      if(el) el.innerHTML='<div class="empty" style="padding:10px;font-size:11px">Error: '+( data.error||'')+'</div>';
      return;
    }
    waContactos = data.contactos || [];
    if(document.getElementById('rs-wa-count'))
      document.getElementById('rs-wa-count').textContent = waContactos.length;
    renderContactosWA(waContactos);
  }catch(e){
    if(el) el.innerHTML='<div class="empty" style="padding:10px;font-size:11px">Sin conexión Twilio</div>';
  }
}

function renderContactosWA(contactos){
  var el = document.getElementById('waContactos');
  if(!el) return;
  if(!contactos.length){
    el.innerHTML='<div class="empty" style="padding:20px;font-size:11px">Sin mensajes aún.<br>Cuando alguien escriba al +1 415 523 8886 aparecerá aquí.</div>';
    return;
  }
  el.innerHTML = contactos.map(function(c){
    var ultimo = (c.mensajes||[])[0]||{};
    var preview = (ultimo.body||'').slice(0,40);
    var activo = waContactoActivo === c.phone;
    return '<div onclick="abrirChatWA(\''+c.phone+'\')" style="padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border);background:'+(activo?'var(--bg-soft)':'transparent')+';display:flex;align-items:center;gap:10px">'
      +'<div style="width:38px;height:38px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;flex-shrink:0">'
      +c.phone.slice(-2)+'</div>'
      +'<div style="flex:1;min-width:0">'
      +'<div style="font-size:12px;font-weight:700">'+c.phone+'</div>'
      +'<div style="font-size:10px;color:var(--text-faint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+preview+'</div>'
      +'</div>'
      +'<div style="font-size:9px;color:var(--text-faint)">'+( (c.ultimo||'').slice(11,16)||'')+'</div>'
      +'</div>';
  }).join('');
}

function filtrarContactosWA(q){
  if(!q) return renderContactosWA(waContactos);
  var filtrados = waContactos.filter(function(c){ return c.phone.includes(q); });
  renderContactosWA(filtrados);
}

function abrirChatWA(phone){
  waContactoActivo = phone;
  var contacto = waContactos.find(function(c){return c.phone===phone;});
  if(!contacto) return;
  
  // Actualizar lista
  renderContactosWA(waContactos);
  
  // Header
  document.getElementById('waChatNombre').textContent = phone;
  document.getElementById('waChatPhone').textContent = 'WhatsApp · '+( contacto.mensajes||[]).length+' mensajes';
  document.getElementById('waBtnCrearLead').style.display = 'block';
  document.getElementById('waBtnAbrir').style.display = 'block';
  document.getElementById('waBtnAbrir').href = 'https://wa.me/'+phone.replace(/\D/g,'');
  document.getElementById('waChatInput').style.display = 'flex';
  
  // Mensajes
  var msgs = (contacto.mensajes||[]).slice().reverse();
  var el = document.getElementById('waChatMensajes');
  if(!msgs.length){el.innerHTML='<div class="empty">Sin mensajes</div>';return;}
  
  el.innerHTML = msgs.map(function(m){
    var out = m.direction === 'out';
    return '<div style="display:flex;justify-content:'+(out?'flex-end':'flex-start')+'">'
      +'<div style="max-width:70%;padding:8px 12px;border-radius:'+(out?'12px 12px 2px 12px':'12px 12px 12px 2px')+';background:'+(out?'#25D366':'var(--bg-soft)')+';color:'+(out?'white':'var(--text)')+';font-size:12px;line-height:1.5">'
      +(m.body||'')
      +'<div style="font-size:9px;opacity:0.7;margin-top:3px;text-align:right">'+(m.fecha||'').slice(11,16)+(out?' ✓✓':'')+'</div>'
      +'</div></div>';
  }).join('');
  
  // Scroll al final
  el.scrollTop = el.scrollHeight;
}

async function enviarMsgWA(){
  var msg = document.getElementById('waMsgInput')?.value?.trim();
  if(!msg || !waContactoActivo){toast('Escribe un mensaje','error');return;}
  
  var btn = document.querySelector('#waChatInput .btn-p');
  if(btn) btn.textContent='⏳';
  
  var r = await api('/redes/enviar-wa',{method:'POST',body:JSON.stringify({to:waContactoActivo,mensaje:msg})});
  
  if(r.ok){
    document.getElementById('waMsgInput').value='';
    toast('✅ Enviado');
    setTimeout(loadWAMessages, 2000);
  } else {
    toast('Error: '+(r.error||''),'error');
  }
  if(btn) btn.textContent='📤';
}

async function crearLeadDesdeWA(){
  if(!waContactoActivo) return;
  var contacto = waContactos.find(function(c){return c.phone===waContactoActivo;});
  var primerMsg = (contacto?.mensajes||[]).find(function(m){return m.direction==='in';});
  
  var r = await api('/leads',{method:'POST',body:JSON.stringify({
    nombre: 'Lead WA',
    whatsapp: waContactoActivo,
    origen: 'whatsapp_manual',
    estado: 'nuevo',
    etapa: 'captacion',
    notas: primerMsg?.body||'Lead desde Panel Redes'
  })});
  if(r.id || r.ok) toast('✅ Lead creado en CRM');
  else toast('Error','error');
}

function redactarEmail(){
  var p = document.getElementById('emailRedactorPanel');
  if(p) p.style.display = p.style.display==='none'?'block':'none';
}

async function enviarEmailCRM(){
  var para = document.getElementById('email-para')?.value?.trim();
  var asunto = document.getElementById('email-asunto')?.value?.trim();
  var body = document.getElementById('email-body')?.value?.trim();
  if(!para||!asunto||!body){toast('Completa todos los campos','error');return;}
  
  var r = await api('/enviar-email',{method:'POST',body:JSON.stringify({to:para,subject:asunto,body:body})});
  if(r.ok){
    toast('✅ Email enviado');
    document.getElementById('emailRedactorPanel').style.display='none';
    document.getElementById('email-para').value='';
    document.getElementById('email-asunto').value='';
    document.getElementById('email-body').value='';
  } else toast('Error: '+(r.error||''),'error');
}

// Auto-refresh WhatsApp cada 30 segundos cuando el panel está abierto
setInterval(function(){
  var panel = document.getElementById('rpanel-wa');
  if(panel && panel.style.display !== 'none'){
    loadWAMessages();
  }
}, 30000);

// ── DESCARGAR PDF EVALUACIÓN ──
async function descargarEvalPDF(lead_id, nombre){
  toast('📄 Generando PDF...');
  try{
    var resp = await fetch('/api/crm/evaluaciones/'+lead_id+'/pdf',{
      headers:{'x-api-key':'TengoVisa2026API'}
    });
    var blob = await resp.blob();
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'TengoVisa_Evaluacion_'+nombre+'.pdf';
    a.click();
    URL.revokeObjectURL(url);
    toast('✅ PDF descargado');
  }catch(e){toast('Error: '+e.message,'error');}
}
