#!/usr/bin/env python3
"""
Test Webshare Residential contra AIS
Corre: python3 test_webshare.py
"""
import requests
import concurrent.futures
import time

# ── CONFIG ──────────────────────────────────────
AIS_URL   = "https://ais.usvisa-info.com/en-do/niv"
TIMEOUT   = 12
PASS_CODE = [200, 403]   # 403 = llegó a AIS pero bloqueó la cuenta, NO el proxy
FAIL_CODE = [407, 000]   # 407 = proxy auth fail

PROXIES_RAW = [
    "axihbvupresidential-us-1:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-2:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-3:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-4:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-5:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-6:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-7:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-8:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-9:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-10:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-11:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-12:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-13:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-14:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-15:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-16:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-17:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-18:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-19:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-20:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-21:ng8m7kbc1met@p.webshare.io:80",
    "axihbvupresidential-us-22:ng8m7kbc1met@p.webshare.io:80",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── LÓGICA ──────────────────────────────────────
def test_proxy(raw):
    proxy_url = f"http://{raw}"
    proxies   = {"http": proxy_url, "https": proxy_url}
    label     = raw.split("@")[0].split(":")[0]  # ej: axihbvupresidential-us-3
    try:
        r = requests.get(AIS_URL, proxies=proxies, headers=HEADERS, timeout=TIMEOUT)
        code = r.status_code
        # Detectar bloqueo real de AIS (Cloudflare/captcha)
        blocked = "cloudflare" in r.text.lower() or "blocked" in r.text.lower() or "captcha" in r.text.lower()
        if code == 200 and not blocked:
            return (label, "✅ PASS", code, "AIS respondió OK")
        elif code == 200 and blocked:
            return (label, "⚠️  BLOCKED", code, "Cloudflare/captcha detectado")
        elif code == 403:
            return (label, "🔴 403", code, "AIS bloqueó — proxy llegó pero AIS rechaza")
        elif code == 407:
            return (label, "❌ PROXY FAIL", code, "Auth proxy fallida")
        else:
            return (label, f"⚠️  HTTP {code}", code, "Respuesta inesperada")
    except requests.exceptions.ProxyError as e:
        return (label, "❌ PROXY ERROR", 0, str(e)[:60])
    except requests.exceptions.ConnectTimeout:
        return (label, "⏱️  TIMEOUT", 0, f">{TIMEOUT}s sin respuesta")
    except Exception as e:
        return (label, "❌ ERROR", 0, str(e)[:60])

# ── MAIN ────────────────────────────────────────
def main():
    print("=" * 60)
    print("  TEST WEBSHARE RESIDENTIAL → AIS")
    print(f"  Target: {AIS_URL}")
    print(f"  Proxies: {len(PROXIES_RAW)} | Timeout: {TIMEOUT}s")
    print("=" * 60)

    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futuros = {ex.submit(test_proxy, p): p for p in PROXIES_RAW}
        for fut in concurrent.futures.as_completed(futuros):
            r = fut.result()
            resultados.append(r)
            label, status, code, msg = r
            print(f"  {status:<18} {label:<35} {msg}")

    # Resumen
    print("\n" + "=" * 60)
    ok    = [r for r in resultados if "PASS" in r[1]]
    f403  = [r for r in resultados if "403" in r[1]]
    block = [r for r in resultados if "BLOCKED" in r[1]]
    fail  = [r for r in resultados if "ERROR" in r[1] or "FAIL" in r[1] or "TIMEOUT" in r[1]]

    print(f"  ✅ PASS (llegan a AIS OK):    {len(ok)}")
    print(f"  🔴 403 (AIS los ve pero bloquea): {len(f403)}")
    print(f"  ⚠️  BLOCKED (Cloudflare):      {len(block)}")
    print(f"  ❌ FAIL/TIMEOUT (proxy muerto): {len(fail)}")
    print("=" * 60)

    if ok:
        print("\n  🟢 PROXIES QUE PASAN — usar en Nexus:")
        for r in ok:
            print(f"     {r[0]}:ng8m7kbc1met@p.webshare.io:80")
    if f403:
        print("\n  ⚠️  PROXIES CON 403 — AIS los detecta, Webshare SIGUE BLOQUEADO")
    if fail:
        print("\n  💀 PROXIES MUERTOS:")
        for r in fail:
            print(f"     {r[0]} → {r[3]}")

    print("\n  DIAGNÓSTICO:")
    if len(ok) > 0:
        print("  → Webshare residential SÍ pasa. Prueba con una cuenta real en Nexus.")
    elif len(f403) > len(fail):
        print("  → Los proxies llegan a AIS pero AIS da 403. Sigue bloqueado.")
        print("  → Recomendación: quedarse con IPRoyal residencial.")
    else:
        print("  → Proxies muertos o bloqueados. Webshare no funciona aquí.")

if __name__ == "__main__":
    main()
