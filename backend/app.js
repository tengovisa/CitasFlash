
// ── CONFIG ──
const API = 'https://citaflash.com/cita/proxy.php?path=';

// ── STATE ──
let SESSION = null;
let accounts = [];
let users = [];
let filterCurrent = 'todos';
let searchVal = '';
let addMode = 'run';
let refreshTimer = null;
let logTimer = null;
let proxyCheckTimer = null;
let notifications = [];
let selectedClientId = null;

// ── AUTH ──
async function doLogin() {
  const email = document.getElementById('l-email').value.trim();
  const pass  = document.getElementById('l-pass').value;
  if (!email || !pass) { toast('Ingresa email y contraseña', 'err'); return; }
  const btn = document.querySelector('.lf-btn');
  btn.textContent = '⏳ Ingresando...';
  try {
    const r = await fetch(API + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    if (!r.ok) throw new Error('auth_failed');
    SESSION = await r.json();
    localStorage.setItem('cf_s', JSON.stringify(SESSION));
    showApp();
  } catch {
    document.getElementById('login-error').textContent = 'Credenciales incorrectas';
    btn.textContent = 'Ingresar al panel';
  }
}

document.getElementById('l-pass').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

async function sendForgot() {
  const email = document.getElementById('forgot-email').value.trim();
  if (!email) { toast('Ingresa tu correo', 'err'); return; }
  try { await fetch(API + '/auth/forgot-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) }); } catch {}
  toast('Si el correo existe recibirás tu contraseña', 'info');
  document.getElementById('forgot-box').classList.remove('show');
}

function logout() {
  localStorage.removeItem('cf_s');
  SESSION = null;
  clearInterval(refreshTimer);
  clearInterval(logTimer);
  clearInterval(proxyCheckTimer);
  document.getElementById('app').style.display = 'none';
  document.getElementById('login-page').style.display = 'flex';
}

async function showApp() {
  document.getElementById('login-page').style.display = 'none';
  document.getElementById('app').style.display = 'block';
  document.getElementById('user-name').textContent = SESSION.nombre;
  document.getElementById('user-role').textContent = SESSION.rol === 'administrador' ? 'Administrador' : 'Gestor';
  document.getElementById('user-av').textContent = SESSION.nombre.substring(0, 2).toUpperCase();
  if (SESSION.rol !== 'administrador') {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
  }
  await loadAccounts();
  refreshTimer = setInterval(loadAccounts, 10000);
  proxyCheckTimer = setInterval(checkProxyHealth, 60000);
}

window.addEventListener('load', async () => {
  const saved = localStorage.getItem('cf_s');
  if (saved) {
    try {
      SESSION = JSON.parse(saved);
      const r = await fetch(API + '/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: SESSION.token })
      });
      if (r.ok) { showApp(); return; }
    } catch {}
    localStorage.removeItem('cf_s');
  }
});

// ── API ──
async function api(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

// ── ACCOUNTS ──
async function loadAccounts() {
  try {
    const prev = accounts.map(a => ({ id: a.id, status: a.status }));
    accounts = await api('GET', '/cuentas');
    renderTable();
    updateStats();
    updatePie();
    renderRecent();
    checkOutsideBookings(prev);
    if (selectedClientId) showClientDetail(selectedClientId);
  } catch (e) { console.error('loadAccounts:', e); }
}

function checkOutsideBookings(prev) {
  accounts.forEach(a => {
    const old = prev.find(p => p.id === a.id);
    if (!old) return;
    if (a.status === 'Cita Agendada' && old.status !== 'Cita Agendada' && a.booked_outside) {
      addNotification('⚠️ ' + a.email + ' tiene cita fuera de CitasFlash', 'outside');
    }
  });
}

function checkProxyHealth() {
  accounts.filter(a => a.is_active && a.proxies && a.last_proxy_error).forEach(a => {
    if (Date.now() - new Date(a.last_proxy_error).getTime() > 300000) {
      addNotification('🔴 Proxy muerto: ' + a.email, 'proxy');
    }
  });
}

function addNotification(msg, type) {
  notifications.unshift({ msg, type, time: new Date().toLocaleTimeString(), read: false });
  const count = notifications.filter(n => !n.read).length;
  document.getElementById('notif-count').textContent = count;
  document.getElementById('bell-dot').classList.add('show');
  document.getElementById('bell-btn').classList.add('ringing');
  setTimeout(() => document.getElementById('bell-btn').classList.remove('ringing'), 500);
  renderNotifs();
  toast(msg, 'warn');
}

function renderNotifs() {
  const list = document.getElementById('notif-list');
  if (!notifications.length) { list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted);font-size:13px">Sin notificaciones</div>'; return; }
  list.innerHTML = notifications.slice(0, 10).map(n =>
    `<div class="notif-item ${n.read ? '' : 'unread'}"><div class="nt">${n.msg}</div><div class="ns">${n.time}</div></div>`
  ).join('');
}

function toggleNotifs() {
  const p = document.getElementById('notif-panel');
  p.classList.toggle('open');
  if (p.classList.contains('open')) {
    notifications.forEach(n => n.read = true);
    document.getElementById('bell-dot').classList.remove('show');
    document.getElementById('notif-count').textContent = '0';
    renderNotifs();
  }
}
document.addEventListener('click', e => {
  if (!e.target.closest('#bell-btn') && !e.target.closest('#notif-panel')) {
    document.getElementById('notif-panel').classList.remove('open');
  }
});

function getEstado(a) {
  if (a.status === 'Cancelado') return 'cancelado';
  if (a.status === 'Cita Agendada') return 'agendado';
  if (a.is_active) return 'proceso';
  return 'pausado';
}

function updateStats() {
  const total    = accounts.length;
  const ok       = accounts.filter(a => a.status === 'Cita Agendada').length;
  const proc     = accounts.filter(a => a.is_active && a.status === 'Activo').length;
  const pause    = accounts.filter(a => !a.is_active && a.status !== 'Cita Agendada' && a.status !== 'Cancelado').length;
  const cancelled= accounts.filter(a => a.status === 'Cancelado').length;
  const err      = accounts.filter(a => a.status === 'Error').length;
  const approved = accounts.filter(a => a.visa_status === 'aprobada').length;
  const rejected = accounts.filter(a => a.visa_status === 'rechazada').length;
  const s = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
  s('st-total', total); s('st-ok', ok); s('st-proc', proc); s('st-pause', pause);
  s('st-approved', approved); s('st-rejected', rejected);
  s('nb-total', total); s('nb-ok', ok); s('nb-proc', proc); s('nb-pause', pause); s('nb-cancel', cancelled);
  s('bn-b', total); s('cons-active', proc); s('cons-total', ok); s('cons-err', err);
  s('rep-total', ok); s('rep-week', ok); s('rep-err', err);
  if (total > 0) {
    const pf = (id, v) => { const e = document.getElementById(id); if (e) e.style.width = Math.round(v / total * 100) + '%'; };
    pf('pf-ok', ok); pf('pf-proc', proc);
  }
}

function updatePie() {
  const total = accounts.length || 1;
  const ok    = accounts.filter(a => a.status === 'Cita Agendada').length;
  const proc  = accounts.filter(a => a.is_active && a.status === 'Activo').length;
  const pause = accounts.filter(a => !a.is_active && a.status !== 'Cita Agendada').length;
  const op = Math.round(ok / total * 100);
  const pp = Math.round(proc / total * 100);
  const pp2= Math.round(pause / total * 100);
  const pie = (id, da, off) => {
    const e = document.getElementById(id);
    if (e) { e.setAttribute('stroke-dasharray', da + ' ' + (100 - da)); e.setAttribute('stroke-dashoffset', off); }
  };
  pie('pie-ok', op, 25);
  pie('pie-proc', pp, 25 - op);
  pie('pie-pause', pp2, 25 - op - pp);
  const s = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
  s('pie-pct', op + '%');
  s('leg-ok', 'Agendados ' + op + '%');
  s('leg-proc', 'En proceso ' + pp + '%');
  s('leg-pause', 'Pausados ' + pp2 + '%');
}

function renderRecent() {
  const booked = accounts.filter(a => a.status === 'Cita Agendada').slice(-5).reverse();
  const el = document.getElementById('recent-list');
  if (!el) return;
  if (!booked.length) { el.innerHTML = '<div style="color:var(--muted);font-size:14px;padding:8px 0">No hay citas agendadas aún</div>'; return; }
  el.innerHTML = booked.map(a => `
    <div style="display:flex;align-items:center;gap:12px;padding:11px 13px;background:var(--bg);border-radius:9px;cursor:pointer;transition:background .15s"
      onclick="showClientDetail(${a.id})"
      onmouseover="this.style.background='#ecfdf5'" onmouseout="this.style.background='var(--bg)'">
      <div style="width:36px;height:36px;border-radius:50%;background:#ecfdf5;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">✓</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:14px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a.nombre || a.email.split('@')[0]}</div>
        <div style="font-size:12px;color:var(--muted)">${a.email} · ${a.last_appointment_date || '—'}</div>
      </div>
      <span class="badge green">✓ Agendado</span>
    </div>`).join('');
}

function showClientDetail(id) {
  selectedClientId = id;
  const a = accounts.find(x => x.id === id);
  const cd = document.getElementById('client-detail');
  if (!a || !cd) return;
  cd.classList.add('show');
  document.getElementById('cd-av').textContent = (a.nombre || a.email).substring(0, 2).toUpperCase();
  document.getElementById('cd-nombre').textContent = a.nombre || 'Sin nombre';
  document.getElementById('cd-email').textContent = a.email;
  document.getElementById('cd-badge').innerHTML = getBadge(a);
  document.getElementById('cd-grid').innerHTML = `
    <div class="cd-field"><div class="cd-label">Código</div><div class="cd-value">${genCode(a.id)}</div></div>
    <div class="cd-field"><div class="cd-label">Schedule ID</div><div class="cd-value">${a.schedule_id || '—'}</div></div>
    <div class="cd-field"><div class="cd-label">Tipo visa</div><div class="cd-value">${a.visa_type || 'B1/B2'}</div></div>
    <div class="cd-field"><div class="cd-label">Nº Pasaporte</div><div class="cd-value">${a.passport_number || '—'}</div></div>
    <div class="cd-field"><div class="cd-label">DS-160</div><div class="cd-value">${a.ds160_number || '—'}</div></div>
    <div class="cd-field"><div class="cd-label">Última cita AIS</div><div class="cd-value">${a.last_appointment_date || 'Sin cita'}</div></div>
    <div class="cd-field"><div class="cd-label">Fecha a buscar</div><div class="cd-value">${a.min_date || '—'} → ${a.max_date || '—'}</div></div>
    <div class="cd-field"><div class="cd-label">ASC/CAS</div><div class="cd-value">${a.need_asc ? 'Sí' : 'No'}</div></div>
    <div class="cd-field"><div class="cd-label">Estado visa</div><div class="cd-value">${a.visa_status || '—'}</div></div>`;
}

function getBadge(a) {
  if (a.status === 'Cancelado')        return '<span class="badge purple">✗ Cancelado</span>';
  if (a.booked_outside)                return '<span class="badge outside">⚠ Fuera de sistema</span>';
  if (a.status === 'Cita Agendada')    return '<span class="badge green">✓ Agendado</span>';
  if (a.status === 'Error')            return '<span class="badge red">⚠ Error</span>';
  if (a.is_active)                     return '<span class="badge amber">↻ En proceso</span>';
  return '<span class="badge gray">⏸ Pausado</span>';
}

function genCode(id) { return 'CF-' + String(id).padStart(3, '0'); }

function renderRow(a) {
  const cancelled = a.status === 'Cancelado';
  return `<tr class="${a.booked_outside ? 'outside-booking' : cancelled ? 'cancelled' : ''}"
    onclick="showClientDetail(${a.id})" style="cursor:pointer">
    <td><span class="code-tag">${genCode(a.id)}</span></td>
    <td>
      <div style="font-weight:600">${a.nombre || '—'}</div>
      <div style="font-size:11px;color:var(--muted)">${a.email}</div>
    </td>
    <td>${a.visa_type || 'B1/B2'}</td>
    <td style="font-size:12px">
      <div>${a.min_date || '—'}</div>
      <div style="color:var(--muted)">${a.max_date || '—'}</div>
    </td>
    <td style="text-align:center">${a.need_asc ? '<span style="color:var(--success)">✓</span>' : '—'}</td>
    <td>${getBadge(a)}</td>
    <td style="font-size:12px">${a.last_appointment_date || '<span style="color:var(--muted)">Sin cita</span>'}</td>
    <td onclick="event.stopPropagation()">
      <div class="act-btns">
        <button class="abt edit" onclick="openEdit(${a.id})" title="Editar">✎</button>
        ${cancelled
          ? `<button class="abt reactivate" onclick="reactivateAcc(${a.id})" title="Reactivar">↺</button>`
          : `<button class="abt ${a.is_active ? 'pause' : 'play'}" onclick="toggleAcc(${a.id},${a.is_active})" title="${a.is_active ? 'Pausar' : 'Activar'}">${a.is_active ? '⏸' : '▶'}</button>`
        }
        <button class="abt sync" onclick="syncAccount(${a.id},event)" title="Sincronizar con AIS" style="color:var(--info)">↻</button>
        <button class="abt cancel" onclick="cancelAcc(${a.id})" title="Cancelar">✗</button>
        <button class="abt del" onclick="deleteAcc(${a.id})" title="Eliminar">🗑</button>
        ${a.status === 'Cita Agendada' ? `<button class="abt print" onclick="printCita(${a.id})" title="Imprimir">⎙</button>` : ''}
      </div>
    </td>
  </tr>`;
}

function renderTable() {
  const filtered = accounts.filter(a => {
    const mf = filterCurrent === 'todos' || getEstado(a) === filterCurrent;
    const ms = !searchVal ||
      (a.email || '').toLowerCase().includes(searchVal.toLowerCase()) ||
      (a.nombre || '').toLowerCase().includes(searchVal.toLowerCase()) ||
      (a.schedule_id || '').includes(searchVal) ||
      genCode(a.id).toLowerCase().includes(searchVal.toLowerCase());
    return mf && ms;
  });
  const html = filtered.length ? filtered.map(renderRow).join('') :
    `<tr><td colspan="8" style="text-align:center;padding:28px;color:var(--muted)">Sin resultados</td></tr>`;
  ['main-tbody', 'clientes-tbody'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  });
  renderReports();
}

function renderReports() {
  const rs  = (document.getElementById('rep-search')   || { value: '' }).value.toLowerCase();
  const rc  = (document.getElementById('rep-codigo')   || { value: '' }).value.toLowerCase();
  const rn  = (document.getElementById('rep-nombre')   || { value: '' }).value.toLowerCase();
  const rp  = (document.getElementById('rep-pasaporte')|| { value: '' }).value.toLowerCase();
  const booked = accounts.filter(a => {
    if (a.status !== 'Cita Agendada') return false;
    if (rs && !(a.email || '').toLowerCase().includes(rs)) return false;
    if (rc && !genCode(a.id).toLowerCase().includes(rc)) return false;
    if (rn && !(a.nombre || '').toLowerCase().includes(rn)) return false;
    if (rp && !(a.passport_number || '').toLowerCase().includes(rp)) return false;
    return true;
  });
  const tbody = document.getElementById('rep-tbody');
  if (!tbody) return;
  tbody.innerHTML = booked.map(a => `
    <tr>
      <td><span class="code-tag">${genCode(a.id)}</span></td>
      <td style="font-size:12px">${a.email}</td>
      <td style="font-weight:500">${a.nombre || '—'}</td>
      <td style="font-family:monospace;font-size:12px">${a.passport_number || '—'}</td>
      <td style="font-family:monospace;font-size:12px">${a.ds160_number || '—'}</td>
      <td style="font-size:12px">${a.last_appointment_date || '—'}</td>
      <td>${(a.country || '').toUpperCase()}</td>
      <td>${a.visa_status ? `<span class="badge ${a.visa_status === 'aprobada' ? 'green' : a.visa_status === 'rechazada' ? 'red' : 'amber'}">${a.visa_status}</span>` : '—'}</td>
    </tr>`).join('') || `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--muted)">Sin citas agendadas</td></tr>`;
  const cnt = document.getElementById('rep-count');
  if (cnt) cnt.textContent = booked.length;
}

function exportCSV() {
  const b = accounts.filter(a => a.status === 'Cita Agendada');
  if (!b.length) { toast('No hay citas', 'err'); return; }
  const rows = [
    ['Código', 'Email', 'Nombre', 'Pasaporte', 'DS-160', 'Fecha cita', 'País', 'Estado visa'],
    ...b.map(a => [genCode(a.id), a.email, a.nombre || '', a.passport_number || '', a.ds160_number || '',
      a.last_appointment_date || '', (a.country || '').toUpperCase(), a.visa_status || ''])
  ];
  const a2 = document.createElement('a');
  a2.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(rows.map(r => r.join(',')).join('\n'));
  a2.download = 'citasflash_reporte.csv';
  a2.click();
  toast('CSV exportado', 'ok');
}

function filterTab(f, el) {
  filterCurrent = f;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
  el.classList.add('on');
  renderTable();
}

let srchTimer;
function handleSearch(inp) {
  clearTimeout(srchTimer);
  document.getElementById('srch-wrap').classList.add('loading');
  srchTimer = setTimeout(() => {
    searchVal = inp.value;
    renderTable();
    document.getElementById('srch-wrap').classList.remove('loading');
  }, 350);
}

async function toggleAcc(id, cur) {
  try { await api('PATCH', '/cuentas/' + id + '/toggle'); toast('Cuenta ' + (cur ? 'pausada' : 'activada'), 'ok'); loadAccounts(); }
  catch { toast('Error', 'err'); }
}
async function cancelAcc(id) {
  if (!confirm('¿Cancelar esta cuenta?')) return;
  try { await api('PUT', '/cuentas/' + id, { status: 'Cancelado', is_active: false }); toast('Cancelada', 'ok'); loadAccounts(); }
  catch { toast('Error', 'err'); }
}
async function reactivateAcc(id) {
  try { await api('PUT', '/cuentas/' + id, { status: 'Pausado', is_active: false }); toast('Reactivada', 'ok'); loadAccounts(); }
  catch { toast('Error', 'err'); }
}
async function deleteAcc(id) {
  if (!confirm('¿Eliminar esta cuenta?')) return;
  try { await api('DELETE', '/cuentas/' + id); toast('Eliminada', 'ok'); loadAccounts(); }
  catch { toast('Error', 'err'); }
}

function printCita(id) {
  const a = accounts.find(x => x.id === id);
  if (!a || !a.schedule_id) return;
  window.open('https://ais.usvisa-info.com/es-do/niv/schedule/' + a.schedule_id + '/appointment/print_instructions', '_blank');
}

// ── VALIDATE AIS ──
async function validateAIS() {
  const email = document.getElementById('v-email').value.trim();
  const pass  = document.getElementById('v-pass').value;
  if (!email || !pass) { toast('Ingresa email y contraseña AIS', 'err'); return; }
  const btn = document.getElementById('v-btn');
  btn.textContent = '⏳ Validando...';
  btn.disabled = true;
  try {
    const proxy = document.getElementById('f-proxies').value.trim();
    const body  = { email, password: pass, country: 'do' };
    if (proxy) body.proxy = proxy.split(',')[0].trim();
    const data = await api('POST', '/validate-ais', body);
    if (data.success && data.data && data.data.length > 0) {
      const f = data.data[0];
      document.getElementById('f-schedule').value = f.schedule_id || '';
      document.getElementById('f-visa').value = f.visa_type || 'B1/B2';
      const res = document.getElementById('v-result');
      res.style.display = 'block';
      res.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <span style="color:var(--success);font-size:18px">✓</span>
          <strong>Credenciales válidas</strong>
        </div>
        <div style="font-size:13px;color:var(--muted);display:grid;grid-template-columns:1fr 1fr;gap:4px">
          <div>📋 Schedule: <strong style="color:var(--text)">${f.schedule_id}</strong></div>
          <div>🛂 Visa: <strong style="color:var(--text)">${f.visa_type || 'B1/B2'}</strong></div>
          <div style="grid-column:1/-1">📅 Cita actual: <strong style="color:var(--text)">${f.cita_actual || 'Sin cita'}</strong></div>
        </div>`;
      toast('Datos obtenidos', 'ok');
    } else {
      toast('Credenciales inválidas o sin aplicación', 'err');
    }
  } catch (e) {
    toast('Error al validar: ' + e.message, 'err');
  } finally {
    btn.textContent = '⚡ Validar y obtener datos';
    btn.disabled = false;
  }
}

function selectMode(mode) {
  addMode = mode;
  document.getElementById('mode-pause').className = 'mode-btn' + (mode === 'pause' ? ' sel-pause' : '');
  document.getElementById('mode-run').className   = 'mode-btn' + (mode === 'run'   ? ' sel-run'   : '');
}

async function saveSolicitante() {
  const email    = document.getElementById('v-email').value.trim();
  const password = document.getElementById('v-pass').value;
  const schedule = document.getElementById('f-schedule').value.trim();
  const min_date = document.getElementById('f-min').value;
  const max_date = document.getElementById('f-max').value;
  const need_asc = document.getElementById('f-asc').classList.contains('on');
  const proxies  = document.getElementById('f-proxies').value.trim();
  const secondRaw= parseInt(document.getElementById('f-second').value);
  const second   = isNaN(secondRaw) ? 0 : Math.min(59, Math.max(0, secondRaw));
  const visa_type= document.getElementById('f-visa').value.trim() || 'B1/B2';

  if (!email)    { toast('Email AIS es requerido', 'err'); return; }
  if (!password) { toast('Contraseña AIS es requerida', 'err'); return; }
  if (!schedule) { toast('Schedule ID es requerido. Valida primero con AIS.', 'err'); return; }
  if (!min_date) { toast('Fecha mínima es requerida', 'err'); return; }

  const is_active = addMode === 'run';
  try {
    await api('POST', '/cuentas', {
      email, password, schedule_id: schedule, min_date,
      max_date: max_date || null, need_asc,
      proxies: proxies || null, second, visa_type,
      is_active, status: is_active ? 'Activo' : 'Pausado'
    });
    toast('Solicitante ' + (is_active ? 'agregado y ejecutando' : 'agregado en pausa'), 'ok');
    closeModal('add-modal');
    ['v-email','v-pass','f-schedule','f-min','f-max','f-proxies'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('f-visa').value = 'B1/B2';
    document.getElementById('f-second').value = '0';
    document.getElementById('f-asc').classList.remove('on');
    document.getElementById('v-result').style.display = 'none';
    loadAccounts();
  } catch (e) { toast('Error al guardar: ' + e.message, 'err'); }
}

// ── EDIT ──
function openEdit(id) {
  const a = accounts.find(x => x.id === id);
  if (!a) return;
  document.getElementById('e-id').value        = a.id;
  document.getElementById('e-email').value     = a.email || '';
  document.getElementById('e-schedule').value  = a.schedule_id || '';
  document.getElementById('e-min').value       = a.min_date || '';
  document.getElementById('e-max').value       = a.max_date || '';
  document.getElementById('e-proxies').value   = a.proxies || '';
  document.getElementById('e-second').value    = a.second || 0;
  document.getElementById('e-visa').value      = a.visa_type || 'B1/B2';
  document.getElementById('e-visa-status').value = a.visa_status || '';
  const asc = document.getElementById('e-asc');
  a.need_asc ? asc.classList.add('on') : asc.classList.remove('on');
  openModal('edit-modal');
}

async function saveEdit() {
  const id = document.getElementById('e-id').value;
  const secondRaw = parseInt(document.getElementById('e-second').value);
  const second    = isNaN(secondRaw) ? 0 : Math.min(59, Math.max(0, secondRaw));
  try {
    await api('PUT', '/cuentas/' + id, {
      email:       document.getElementById('e-email').value.trim(),
      schedule_id: document.getElementById('e-schedule').value.trim(),
      min_date:    document.getElementById('e-min').value || null,
      max_date:    document.getElementById('e-max').value || null,
      need_asc:    document.getElementById('e-asc').classList.contains('on'),
      proxies:     document.getElementById('e-proxies').value.trim() || null,
      second,
      visa_type:   document.getElementById('e-visa').value.trim() || 'B1/B2',
      visa_status: document.getElementById('e-visa-status').value || null,
    });
    toast('Actualizado', 'ok');
    closeModal('edit-modal');
    loadAccounts();
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

// ── USUARIOS ──
async function loadUsers() {
  try { users = await api('GET', '/usuarios'); renderUsers(); }
  catch (e) { console.error('loadUsers:', e); }
}

function renderUsers() {
  const tbody = document.getElementById('users-tbody');
  if (!tbody) return;
  tbody.innerHTML = users.map(u => `
    <tr>
      <td style="font-weight:600">${u.nombre}</td>
      <td style="font-size:13px">${u.email}</td>
      <td style="font-size:13px">${u.phone || '—'}</td>
      <td><span class="badge ${u.rol === 'administrador' ? 'blue' : 'cyan'}">${u.rol === 'administrador' ? 'Administrador' : 'Gestor'}</span></td>
      <td><span class="badge ${u.is_active ? 'green' : 'gray'}">${u.is_active ? 'Activo' : 'Inactivo'}</span></td>
      <td>${u.is_demo ? '<span class="badge amber">Demo</span>' : '—'}</td>
      <td style="font-size:12px;color:var(--muted)">${u.last_login ? u.last_login.substring(0, 16) : 'Nunca'}</td>
      <td>
        <div class="act-btns">
          <button class="abt ${u.is_active ? 'pause' : 'play'}" onclick="toggleUser(${u.id})" title="${u.is_active ? 'Suspender' : 'Activar'}">${u.is_active ? '⏸' : '▶'}</button>
          <button class="abt edit" onclick="resetPass(${u.id})" title="Resetear clave">🔑</button>
          <button class="abt del" onclick="deleteUser(${u.id})" title="Eliminar">🗑</button>
        </div>
      </td>
    </tr>`).join('') || '<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--muted)">Sin usuarios</td></tr>';
}

async function createUser() {
  const nombre  = document.getElementById('u-nombre').value.trim();
  const email   = document.getElementById('u-email').value.trim();
  const phone   = document.getElementById('u-phone').value.trim();
  const rol     = document.getElementById('u-rol').value;
  const is_demo = document.getElementById('u-demo').classList.contains('on');
  if (!nombre || !email) { toast('Nombre y email son requeridos', 'err'); return; }
  try {
    await api('POST', '/usuarios', { nombre, email, phone, rol, is_demo });
    toast('Usuario creado — email enviado con clave provisional', 'ok');
    closeModal('user-modal');
    ['u-nombre', 'u-email', 'u-phone'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('u-demo').classList.remove('on');
    loadUsers();
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

async function toggleUser(id) {
  try { await api('PATCH', '/usuarios/' + id + '/toggle'); toast('Estado actualizado', 'ok'); loadUsers(); }
  catch { toast('Error', 'err'); }
}
async function resetPass(id) {
  if (!confirm('¿Enviar email de restablecimiento de contraseña?')) return;
  try { await api('POST', '/usuarios/' + id + '/reset-password'); toast('Email enviado', 'ok'); }
  catch { toast('Error', 'err'); }
}
async function deleteUser(id) {
  if (!confirm('¿Eliminar este usuario?')) return;
  try { await api('DELETE', '/usuarios/' + id); toast('Usuario eliminado', 'ok'); loadUsers(); }
  catch { toast('Error', 'err'); }
}

// ── CONSOLA ──
async function checkBotStatus() {
  try {
    const d = await api('GET', '/bot/status');
    const dot = document.getElementById('sdot');
    const txt = document.getElementById('stext');
    if (d.status === 'active') { dot.className = 'sdot on'; txt.textContent = 'Proceso activo'; }
    else { dot.className = 'sdot off'; txt.textContent = 'Proceso detenido'; }
  } catch {}
}

async function botCmd(cmd) {
  try {
    await api('POST', '/bot/' + cmd);
    toast('Proceso ' + (cmd === 'start' ? 'iniciado' : cmd === 'stop' ? 'detenido' : 'reiniciado'), 'ok');
    setTimeout(checkBotStatus, 2000);
  } catch { toast('Error', 'err'); }
}

// LOG — cols: Fecha | Cuenta (email) | Mensaje
async function loadLogs() {
  try {
    const data = await api('GET', '/bot/logs');
    const lines = (data.logs || '').split('\n').filter(Boolean).slice(-120);
    document.getElementById('log-tbody').innerHTML = lines.reverse().map(line => {
      // Extraer fecha/hora completa
      const dtMatch = line.match(/(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})/);
      const fecha = dtMatch ? dtMatch[1].substring(5) : (line.match(/\d{2}:\d{2}:\d{2}/) ? line.match(/\d{2}:\d{2}:\d{2}/)[0] : '—');
      // Extraer email
      const emMatch = line.match(/\[([^\]]+@[^\]]+)\]/);
      const email = emMatch ? emMatch[1] : 'Sistema';
      // Mensaje limpio: quitar timestamp y email
      let msg = line
        .replace(/\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}[,\.]?\d*\s*/g, '')
        .replace(/\[[^\]]+@[^\]]+\]\s*/g, '')
        .replace(/vmi\d+\s+python3\[\d+\]:\s*/g, '')
        .replace(/\[CF-\d+\]\s*/g, '')
        .trim();
      if (msg.length > 80) msg = msg.substring(0, 80) + '…';
      // Clase de color
      let cls = 'lt-info';
      if (line.includes('✅') || line.includes('AGENDADA')) cls = 'lt-ok';
      else if (line.includes('❌') || line.includes('Error')) cls = 'lt-err';
      else if (line.includes('⚠️') || line.includes('Sin cuentas')) cls = 'lt-warn';
      return `<tr>
        <td class="${cls}" style="white-space:nowrap;font-size:11px">${fecha}</td>
        <td class="lt-email" title="${email}">${email}</td>
        <td class="${cls} lt-msg">${msg || '—'}</td>
      </tr>`;
    }).join('');
    if (!logTimer) logTimer = setInterval(loadLogs, 10000);
  } catch {
    document.getElementById('log-tbody').innerHTML = '<tr><td colspan="3" style="color:#f87171;padding:12px">Error al cargar logs</td></tr>';
  }
}

// ── SEGUNDOS MASIVO ──
function onSecModeChange() {
  const mode = document.getElementById('sec-mode').value;
  document.getElementById('sec-manual-wrap').style.display = mode === 'manual' ? 'block' : 'none';
  updateSecPreview();
}

function updateSecPreview() {
  const proc = accounts.filter(a => a.is_active && a.status === 'Activo');
  const mode = document.getElementById('sec-mode').value;
  let txt = 'Cuentas en proceso: ' + proc.length + '\n';
  if (mode === 'auto') {
    const ejemplos = proc.slice(0, 6).map((_, i) => Math.floor(i * (60 / Math.max(proc.length, 1))));
    txt += 'Distribución ejemplo: ' + ejemplos.join(', ') + (proc.length > 6 ? '...' : '');
  } else if (mode === 'random') {
    txt += 'Segundo aleatorio 0-59 por cuenta';
  } else {
    const v = document.getElementById('sec-value').value;
    txt += 'Segundo ' + (v || '0') + ' para todas las cuentas en proceso';
  }
  document.getElementById('sec-preview').textContent = txt;
}

async function applySeconds() {
  const proc = accounts.filter(a => a.is_active && a.status === 'Activo');
  if (!proc.length) { toast('No hay cuentas en proceso', 'err'); return; }
  const mode = document.getElementById('sec-mode').value;
  const manualVal = parseInt(document.getElementById('sec-value').value);
  if (mode === 'manual' && (isNaN(manualVal) || manualVal < 0 || manualVal > 59)) {
    toast('Ingresa un segundo válido entre 0 y 59', 'err'); return;
  }
  try {
    for (let i = 0; i < proc.length; i++) {
      let sec;
      if (mode === 'auto') sec = Math.floor(i * (60 / proc.length));
      else if (mode === 'random') sec = Math.floor(Math.random() * 60);
      else sec = manualVal;
      await api('PUT', '/cuentas/' + proc[i].id, { second: sec });
    }
    toast('Segundos actualizados en ' + proc.length + ' cuentas', 'ok');
    closeModal('seconds-modal');
    loadAccounts();
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

// ── SYNC ACCOUNT ──
async function syncAccount(id, event) {
  if (event) event.stopPropagation();
  const a = accounts.find(x => x.id === id);
  if (!a) return;
  toast('Sincronizando ' + a.email + '...', 'info');
  try {
    const proxy = a.proxies ? a.proxies.split(',')[0].trim() : undefined;
    const data = await api('POST', '/validate-ais', {
      email: a.email, password: a.password, country: a.country || 'do',
      proxy: proxy
    });
    if (data.success && data.data && data.data.length > 0) {
      const d = data.data[0];
      const updates = {};
      if (d.nombre && d.nombre !== 'Sin nombre') updates.nombre = d.nombre;
      if (d.visa_type) updates.visa_type = d.visa_type;
      if (d.passport_number) updates.passport_number = d.passport_number;
      if (d.ds160_number) updates.ds160_number = d.ds160_number;
      if (d.cita_actual && d.cita_actual !== 'Sin cita') updates.last_appointment_date = d.cita_actual;
      if (Object.keys(updates).length > 0) {
        await api('PUT', '/cuentas/' + id, updates);
        toast('✅ ' + a.email + ' sincronizado', 'ok');
        loadAccounts();
      } else {
        toast('Sin cambios para ' + a.email, 'info');
      }
    } else {
      toast('No se pudo sincronizar ' + a.email, 'err');
    }
  } catch (e) { toast('Error al sincronizar: ' + e.message, 'err'); }
}

// ── IMPORT CSV ──
window.addEventListener('load', function() { var cf = document.getElementById('csv-file'); cf && cf.addEventListener('change', function() {
  const file = this.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const lines = e.target.result.split('\n').filter(l => l.trim() && !l.startsWith('email'));
    const preview = document.getElementById('csv-preview');
    preview.style.display = 'block';
    preview.innerHTML = '<strong>' + lines.length + ' cuentas detectadas</strong><br>' +
      lines.slice(0, 3).map(l => '<span style="color:var(--muted);font-size:12px">' + l.substring(0, 60) + (l.length > 60 ? '...' : '') + '</span>').join('<br>') +
      (lines.length > 3 ? '<br><span style="color:var(--muted);font-size:12px">... y ' + (lines.length - 3) + ' más</span>' : '');
  };
  reader.readAsText(file);
});

async function importCSV() {
  const fileInput = document.getElementById('csv-file');
  if (!fileInput || !fileInput.files[0]) { toast('Selecciona un archivo CSV', 'err'); return; }
  const isActive = document.getElementById('import-run').classList.contains('on');
  const reader = new FileReader();
  reader.onload = async function(e) {
    const lines = e.target.result.split('\n').filter(l => l.trim() && !l.startsWith('email'));
    if (!lines.length) { toast('El archivo está vacío o no tiene datos válidos', 'err'); return; }
    toast('Importando ' + lines.length + ' cuentas...', 'info');
    let ok = 0, err = 0;
    for (const line of lines) {
      const parts = line.split(',').map(p => p.trim().replace(/^"|"$/g, ''));
      const [email, password, schedule_id, visa_type, min_date, max_date, need_asc_raw, second_raw, proxies] = parts;
      if (!email || !password || !schedule_id || !min_date) { err++; continue; }
      try {
        await api('POST', '/cuentas', {
          email, password, schedule_id,
          visa_type: visa_type || 'B1/B2',
          min_date, max_date: max_date || null,
          need_asc: need_asc_raw === 'true' || need_asc_raw === '1',
          second: parseInt(second_raw) || 0,
          proxies: proxies || null,
          is_active: isActive,
          status: isActive ? 'Activo' : 'Pausado'
        });
        ok++;
      } catch { err++; }
      // Pequeña pausa para no saturar la API
      await new Promise(r => setTimeout(r, 200));
    }
    toast('Importadas: ' + ok + ' ✅ | Errores: ' + err + (err > 0 ? ' ❌' : ''), ok > 0 ? 'ok' : 'err');
    closeModal('import-modal');
    fileInput.value = '';
    document.getElementById('csv-preview').style.display = 'none';
    loadAccounts();
  };
  reader.readAsText(fileInput.files[0]);
}

// ── NAV ──
const pageMap = {
  dashboard: 'page-dashboard',
  todos: 'page-clientes', agendados: 'page-clientes',
  proceso: 'page-clientes', pausados: 'page-clientes', cancelados: 'page-clientes',
  consola: 'page-consola', usuarios: 'page-usuarios', reportes: 'page-reportes'
};
const pageTitles = {
  dashboard: 'Dashboard', todos: 'Todos los clientes', agendados: 'Agendados',
  proceso: 'En proceso', pausados: 'Pausados', cancelados: 'Cancelados',
  consola: 'Consola', usuarios: 'Usuarios', reportes: 'Reportes'
};

function goPage(p, el) {
  // Ocultar todas las páginas
  Object.values(pageMap).forEach(id => {
    const e = document.getElementById(id);
    if (e) e.style.display = 'none';
  });
  // Mostrar la página destino
  const show = document.getElementById(pageMap[p]);
  if (show) show.style.display = 'block';
  // Actualizar sidebar activo
  document.querySelectorAll('.ni').forEach(n => n.classList.remove('on'));
  if (el && el.classList && el.classList.contains('ni')) el.classList.add('on');
  // Título topbar
  document.getElementById('page-title').textContent = pageTitles[p] || p;
  // Lógica por página
  if (['todos', 'agendados', 'proceso', 'pausados', 'cancelados'].includes(p)) {
    filterCurrent = p === 'todos' ? 'todos'
                  : p === 'agendados' ? 'agendado'
                  : p === 'cancelados' ? 'cancelado' : p;
    const ct = document.getElementById('clientes-title');
    if (ct) ct.textContent = pageTitles[p];
    const sw = document.getElementById('sec-btn-wrap');
    if (sw) sw.style.display = p === 'proceso' ? 'block' : 'none';
    renderTable();
  }
  if (p === 'consola') { checkBotStatus(); }
  if (p === 'usuarios') { loadUsers(); }
  if (p === 'reportes') { renderReports(); }
  closeSB();
}

function setBN(el) { document.querySelectorAll('.bn-item').forEach(n => n.classList.remove('on')); el.classList.add('on'); }
function openSB()  { document.getElementById('sidebar').classList.add('open'); document.getElementById('sb-overlay').classList.add('open'); }
function closeSB() { document.getElementById('sidebar').classList.remove('open'); document.getElementById('sb-overlay').classList.remove('open'); }
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-overlay').forEach(m => m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); }));
function toast(msg, type = 'ok') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show ' + type;
  setTimeout(() => el.className = '', 3500);
}
