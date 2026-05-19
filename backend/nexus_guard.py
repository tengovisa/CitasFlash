#!/usr/bin/env python3
"""
Nexus Guard — verifica integridad de nexus.py
Si detecta cambio inesperado → restaura backup estable
"""
import os, hashlib, subprocess
from datetime import datetime

NEXUS   = '/root/nexus.py'
BACKUP  = '/root/backup/'
HASH_F  = '/root/backup/.nexus_hash'

def get_hash(path):
    return hashlib.md5(open(path,'rb').read()).hexdigest()

def save_hash():
    h = get_hash(NEXUS)
    open(HASH_F,'w').write(h)
    print(f'Hash guardado: {h[:12]}...')

def verify():
    if not os.path.exists(HASH_F):
        save_hash()
        return True
    
    saved = open(HASH_F).read().strip()
    current = get_hash(NEXUS)
    
    if saved != current:
        # Verificar sintaxis
        r = subprocess.run(['python3','-c',f'import ast; ast.parse(open("{NEXUS}").read())'],
                          capture_output=True, text=True)
        if r.returncode != 0:
            print(f'⚠️  nexus.py tiene error de sintaxis — restaurando backup')
            backups = sorted([f for f in os.listdir(BACKUP) if f.startswith('nexus_') and f.endswith('.py')], reverse=True)
            if backups:
                src = os.path.join(BACKUP, backups[0])
                os.system(f'cp {src} {NEXUS}')
                print(f'✅ Restaurado: {backups[0]}')
                subprocess.run(['systemctl','restart','nexus'])
                return False
        else:
            # Cambio válido — actualizar hash
            save_hash()
            print(f'Hash actualizado: {current[:12]}...')
    return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'save':
        save_hash()
    else:
        verify()
