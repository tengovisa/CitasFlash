import os, re, json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('/root/.env.citafast')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

rows = sb.table('cuentas_citafast').select('id,email,status,is_active').limit(5000).execute().data or []
now = datetime.now()
pat = re.compile(r'bloqueada ais hasta (.+?)(?:\.|$)', re.I)

fixed = []
for r in rows:
    st = (r.get('status') or '').strip()
    m = pat.search(st)
    if not m:
        continue

    raw = m.group(1).strip()
    dt = None
    for fmt in (
        '%d %B, %Y, %H:%M:%S AST',
        '%d %B, %Y, %H:%M:%S',
        '%d %b, %Y, %H:%M:%S AST',
        '%d %b, %Y, %H:%M:%S',
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except:
            pass

    if dt and dt <= now:
        sb.table('cuentas_citafast').update({
            'status': 'Pendiente de revalidación',
            'is_active': False,
            'updated_at': datetime.now().isoformat()
        }).eq('id', r['id']).execute()
        fixed.append({'id': r['id'], 'email': r.get('email')})

print(json.dumps({'ok': True, 'fixed': len(fixed), 'items': fixed}, ensure_ascii=False))
