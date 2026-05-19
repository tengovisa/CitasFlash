import requests, uuid, time

CID="hl_d36aad6c"
ZONE="residential_proxy2"
PWD="yrkzbddify53"

def build():
    sid="sess_"+uuid.uuid4().hex
    u=f"brd-customer-{CID}-zone-{ZONE}-session-{sid}"
    p=f"http://{u}:{PWD}@brd.superproxy.io:33335"
    return {"http":p,"https":p}

s=requests.Session()
t=time.time()

try:
    r=s.get("https://ais.usvisa-info.com/es-do/niv",proxies=build(),timeout=15)
    print("STATUS:",r.status_code)
    print("LATENCY:",round(time.time()-t,2))
    print("LOGIN_PAGE:", "sign in" in r.text.lower())
    print("LOCKED:", "your account is locked" in r.text.lower())
except Exception as e:
    print("ERROR:",e)
