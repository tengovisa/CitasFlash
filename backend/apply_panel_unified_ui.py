from pathlib import Path

p = Path('/var/www/nexus/index.html')
s = p.read_text(encoding='utf-8')

css = r"""
<style id="dfc-unified-premium-ui">
:root{
  --ok:#10B981; --bad:#EF4444; --dead:#991B1B; --warn:#F59E0B; --retry:#7C3AED; --info:#6B7280;
  --blue:#2563EB; --green:#22C55E; --orange:#EA580C; --red:#DC2626; --purple:#8B5CF6;
}
.state-chip,.prio-chip{
  display:inline-flex;align-items:center;gap:7px;padding:6px 12px;border-radius:999px;
  font-size:11px;font-weight:800;border:1px solid transparent;line-height:1;white-space:nowrap
}
.state-chip::before,.prio-chip::before{
  content:'';width:8px;height:8px;border-radius:999px;display:inline-block
}
.sc-ok{color:#fff;border-color:var(--ok);background:rgba(16,185,129,.20)} .sc-ok::before{background:var(--ok)}
.sc-bad{color:#fff;border-color:var(--bad);background:rgba(239,68,68,.20)} .sc-bad::before{background:var(--bad)}
.sc-dead{color:#fff;border-color:var(--dead);background:rgba(153,27,27,.20)} .sc-dead::before{background:var(--dead)}
.sc-warn{color:#fff;border-color:var(--warn);background:rgba(245,158,11,.20)} .sc-warn::before{background:var(--warn)}
.sc-retry{color:#fff;border-color:var(--retry);background:rgba(124,58,237,.20)} .sc-retry::before{background:var(--retry)}
.sc-info{color:#fff;border-color:var(--info);background:rgba(107,114,128,.20)} .sc-info::before{background:var(--info)}

.icon-actions{display:flex;align-items:center;gap:8px;flex-wrap:nowrap}
.icon-btn{
  width:32px;height:32px;border-radius:999px;border:1px solid rgba(0,0,0,.08);background:#fff;
  display:inline-flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(15,23,42,.10);transition:all .18s ease;color:#334155;cursor:pointer;padding:0
}
.icon-btn:hover{transform:translateY(-1px) scale(1.03);box-shadow:0 10px 24px rgba(15,23,42,.14)}
.icon-btn svg{width:16px;height:16px;stroke-width:2}
.ib-run{border-color:rgba(34,197,94,.25);color:#166534;background:rgba(34,197,94,.12)}
.ib-stop{border-color:rgba(234,88,12,.25);color:#9A3412;background:rgba(234,88,12,.12)}
.ib-check{border-color:rgba(34,197,94,.25);color:#166534;background:rgba(34,197,94,.12)}
.ib-edit{border-color:rgba(37,99,235,.25);color:#1D4ED8;background:rgba(37,99,235,.12)}
.ib-log{border-color:rgba(107,114,128,.25);color:#475569;background:rgba(107,114,128,.10)}
.ib-rotate{border-color:rgba(139,92,246,.25);color:#7C3AED;background:rgba(139,92,246,.12)}
.ib-delete{border-color:rgba(220,38,38,.25);color:#DC2626;background:rgba(220,38,38,.12)}

#cuentas-tbody td:last-child{min-width:220px}
#proxies-tbody td:last-child{min-width:180px}
#usuarios-tbody td:last-child{min-width:110px}
</style>
"""

js = r"""
<script id="dfc-unified-premium-ui-script">
(function(){
  const esc = s => String(s ?? '').replace(/'/g,"\\'");
  const icon = {
    run:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><polygon points="5,3 13,8 5,13"/></svg>',
    stop:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><rect x="4" y="4" width="8" height="8" rx="1.2"/></svg>',
    check:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><path d="M3 8h10"/><path d="M8 3v10"/><circle cx="8" cy="8" r="5"/></svg>',
    edit:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><path d="M11 2l3 3-9 9H2v-3L11 2z"/></svg>',
    log:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><rect x="3" y="2.5" width="10" height="11" rx="1.5"/><path d="M5.5 5.5h5M5.5 8h5M5.5 10.5h3.5"/></svg>',
    rotate:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><path d="M2 8a6 6 0 106-6"/><path d="M2 4v4h4"/></svg>',
    del:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><path d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5"/><rect x="3" y="4" width="10" height="10" rx="1"/></svg>'
  };
  const btn = (cls,title,onclick,svg)=>`<button class="icon-btn ${cls}" title="${title}" onclick="${onclick}">${svg}</button>`;

  function pillClass(text){
    const t = String(text || '').toLowerCase();
    if(/buscando|activo|en proceso|ready|ok|agendad|encendid|running/.test(t)) return 'sc-ok';
    if(/bloquead|bloqueada ais|error|invalid|denied|fall/.test(t)) return 'sc-bad';
    if(/muerto|dead|eliminad|banned/.test(t)) return 'sc-dead';
    if(/detenid|pausad|sleep|dormid|pendiente|cooldown|warning|inactiv/.test(t)) return 'sc-warn';
    if(/brauueda|reintent|retry/.test(t)) return 'sc-retry';
    return 'sc-info';
  }
  function chip(text, klass){ return `<span class="${klass} ${pillClass(text)}">${text || '—'}</span>`; }

  async function testAISCuenta(id){
    try{
      const d = await api('GET','/cuentas');
      const cuentas = d.cuentas || d || [];
      const c = cuentas.find(x => Number(x.id) === Number(id));
      if(!c){ toast('Cuenta no encontrada','err'); return; }
      const r = await api('POST','/validate-ais',{email:c.email,password:c.password,country:c.country || 'do'});
      alert(JSON.stringify(r,null,2));
      toast('Validación AIS ejecutada','ok');
    }catch(e){ toast('Error AIS: ' + e.message,'err'); }
  }

  async function viewCuentaLog(id,email){
    try{
      const d = await api('GET','/logs/tail-json');
      const items = (d.items || []).filter(x => String(x.message || '').includes('[' + email + ']')).slice(-18);
      if(!items.length){ alert('Sin logs recientes para ' + email); return; }
      alert(items.map(x => `${x.ts} [${x.thread}] ${x.message}`).join('\n'));
    }catch(e){ toast('Error log: ' + e.message,'err'); }
  }

  async function testProxyById(id){
    try{
      const d = await api('GET','/proxies');
      const arr = d.proxies || d || [];
      const px = arr.find(x => Number(x.id) === Number(id));
      alert(JSON.stringify(px || {id,message:'No encontrado'}, null, 2));
      toast('Check proxy #' + id, 'ok');
    }catch(e){ toast('Error proxy: ' + e.message,'err'); }
  }

  async function copyProxyText(txt){
    try{ await navigator.clipboard.writeText(txt); toast('Copiado','ok'); }
    catch(e){ toast('No se pudo copiar','err'); }
  }

  window.editUser = window.editUser || function(id){ toast('Editar usuario #' + id, 'warn'); };

  function upgradeCuentas(){
    const tb = document.getElementById('cuentas-tbody');
    if(!tb) return;
    [...tb.querySelectorAll('tr')].forEach(tr=>{
      const tds = tr.querySelectorAll('td');
      if(tds.length < 10) return;

      const actionsTd = tds[9];
      const html = actionsTd.innerHTML || '';
      const m = html.match(/editCuenta\((\d+)\)|toggleCuenta\((\d+),|deleteCuenta\((\d+)\)/);
      const id = m ? Number(m[1] || m[2] || m[3]) : null;
      if(!id) return;

      const email = (tds[1]?.innerText || '').trim();
      const prioridad = (tds[6]?.innerText || '').trim();
      const estado = (tds[7]?.innerText || '').trim();

      tds[6].innerHTML = chip(prioridad || 'normal', 'prio-chip');
      tds[7].innerHTML = chip(estado || 'Sin estado', 'state-chip');

      const running = /buscando|activo|en proceso|ready|running/.test(String(estado).toLowerCase());

      actionsTd.innerHTML = `<div class="icon-actions">
        ${btn(running?'ib-stop':'ib-run', running?'Detener/Pausar':'Correr/Iniciar', `toggleCuenta(${id},${!running})`, running?icon.stop:icon.run)}
        ${btn('ib-check','Validar AIS', `testAISCuenta(${id})`, icon.check)}
        ${btn('ib-edit','Editar cuenta', `editCuenta(${id})`, icon.edit)}
        ${btn('ib-log','Ver log', `viewCuentaLog(${id},'${esc(email)}')`, icon.log)}
        ${btn('ib-delete','Eliminar cuenta', `deleteCuenta(${id})`, icon.del)}
      </div>`;
    });
  }

  function upgradeProxies(){
    const tb = document.getElementById('proxies-tbody');
    if(!tb) return;
    [...tb.querySelectorAll('tr')].forEach(tr=>{
      const tds = tr.querySelectorAll('td');
      if(tds.length < 8) return;

      const actionsTd = tds[7];
      const html = actionsTd.innerHTML || '';
      const m = html.match(/proxies\/(\d+)\/reset|proxies\/(\d+)|api\('DELETE','\/proxies\/(\d+)/);
      const id = m ? Number(m[1] || m[2] || m[3]) : null;
      if(!id) return;

      const host = (tds[1]?.innerText || '').trim();
      const estado = (tds[6]?.innerText || '').trim();
      tds[6].innerHTML = chip(estado || 'Sin estado', 'state-chip');

      actionsTd.innerHTML = `<div class="icon-actions">
        ${btn('ib-rotate','Rotar / Check Proxy', `testProxyById(${id})`, icon.rotate)}
        ${btn('ib-check','Reset cooldown', `api('PATCH','/proxies/${id}/reset').then(()=>{toast('Reset OK','ok');loadProxies();})`, icon.check)}
        ${btn('ib-log','Copiar host', `copyProxyText('${esc(host)}')`, icon.log)}
        ${btn('ib-delete','Eliminar proxy', `api('DELETE','/proxies/${id}').then(()=>{toast('Eliminado','ok');loadProxies();})`, icon.del)}
      </div>`;
    });
  }

  function upgradeUsuarios(){
    const tb = document.getElementById('usuarios-tbody');
    if(!tb) return;
    [...tb.querySelectorAll('tr')].forEach(tr=>{
      const tds = tr.querySelectorAll('td');
      if(tds.length < 6) return;
      const actionsTd = tds[5];
      const html = actionsTd.innerHTML || '';
      const m = html.match(/toggleUser\((\d+),|deleteUser\((\d+)\)/);
      const id = m ? Number(m[1] || m[2]) : null;
      if(!id) return;
      actionsTd.innerHTML = `<div class="icon-actions">
        ${btn('ib-edit','Editar usuario', `editUser(${id})`, icon.edit)}
        ${btn('ib-delete','Eliminar usuario', `deleteUser(${id})`, icon.del)}
      </div>`;
    });
  }

  function fixBadTexts(){
    document.body.innerHTML = document.body.innerHTML
      .replace(/Editar cuenta #223 —al editar un usuario/g,'Editar usuario #223')
      .replace(/Editar cuenta #121/g,'Editar cuenta #121');
  }

  const oldLoadCuentas = window.loadCuentas;
  if(typeof oldLoadCuentas === 'function'){
    window.loadCuentas = async function(){
      const r = await oldLoadCuentas.apply(this, arguments);
      setTimeout(upgradeCuentas, 120);
      return r;
    }
  }

  const oldLoadProxies = window.loadProxies;
  if(typeof oldLoadProxies === 'function'){
    window.loadProxies = async function(){
      const r = await oldLoadProxies.apply(this, arguments);
      setTimeout(upgradeProxies, 120);
      return r;
    }
  }

  const oldLoadUsuarios = window.loadUsuarios;
  if(typeof oldLoadUsuarios === 'function'){
    window.loadUsuarios = async function(){
      const r = await oldLoadUsuarios.apply(this, arguments);
      setTimeout(upgradeUsuarios, 120);
      return r;
    }
  }

  window.testAISCuenta = testAISCuenta;
  window.viewCuentaLog = viewCuentaLog;
  window.testProxyById = testProxyById;
  window.copyProxyText = copyProxyText;

  document.addEventListener('DOMContentLoaded', ()=>{
    setTimeout(()=>{ upgradeCuentas(); upgradeProxies(); upgradeUsuarios(); fixBadTexts(); }, 700);
  });
})();
</script>
"""

if 'id="dfc-unified-premium-ui"' not in s:
    s=s.replace('</head>', css+'\n</head>')
if 'id="dfc-unified-premium-ui-script"' not in s:
    s=s.replace('</body>', js+'\n</body>')

p.write_text(s, encoding='utf-8')
print('OK: panel unificado premium aplicado en /var/www/nexus/index.html')
