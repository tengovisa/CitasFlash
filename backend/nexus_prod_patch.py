import os,uuid,time,re,requests

# === SSL FIX REAL (PYTHON) ===
os.environ['REQUESTS_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'
os.environ['SSL_CERT_FILE']='/etc/ssl/certs/ca-certificates.crt'

CID="hl_d36aad6c"
ZONE="residential_proxy2"
PWD="yrkzbddify53"

class NexusSafe:
    def __init__(self):
        self.session_id="sess_"+uuid.uuid4().hex
        self.session=requests.Session()
        self.session.headers={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept-Language":"en-US,en;q=0.9"
        }
        self.set_proxy()

    def set_proxy(self):
        proxy=f"http://brd-customer-{CID}-zone-{ZONE}-country-us-session-{self.session_id}:{PWD}@brd.superproxy.io:33335"
        self.session.proxies={"http":proxy,"https":proxy}

    def rotate(self):
        self.session_id="sess_"+uuid.uuid4().hex
        self.set_proxy()

    def check(self):
        try:
            r=self.session.get("https://ais.usvisa-info.com/es-do/niv",timeout=15)
            txt=r.text.lower()

            status=r.status_code
            login="sign in" in txt
            locked="your account is locked" in txt
            csrf=bool(re.search(r'authenticity_token',r.text))

            print(f"[{time.strftime('%H:%M:%S')}] STATUS:{status} LOGIN:{login} LOCK:{locked} CSRF:{csrf}")

            # VALIDACIÓN REAL
            if status!=200 or not csrf:
                self.rotate()

            if locked:
                print("ACCOUNT LOCKED → SLEEP 30m")
                time.sleep(1800)

        except Exception as e:
            print("ERROR:",e)
            self.rotate()

bot=NexusSafe()

# === LOOP 24/7 ===
while True:
    bot.check()
    time.sleep(8)
