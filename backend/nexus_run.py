import uuid,time,re
from curl_cffi import requests

CID="hl_d36aad6c"
ZONE="residential_proxy2"
PWD="yrkzbddify53"

class Nexus:
    def __init__(self):
        self.session_id="sess_"+uuid.uuid4().hex
        self.new_session()

    def new_session(self):
        self.session=requests.Session(impersonate="chrome120")
        self.session.timeout=15

        proxy=f"http://brd-customer-{CID}-zone-{ZONE}-country-us-session-{self.session_id}:{PWD}@brd.superproxy.io:33335"

        self.session.proxies={"http":proxy,"https":proxy}

        self.session.headers={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept-Language":"en-US,en;q=0.9"
        }

    def rotate(self):
        self.session_id="sess_"+uuid.uuid4().hex
        self.new_session()

    def run(self):
        while True:
            try:
                r=self.session.get(
                    "https://ais.usvisa-info.com/es-do/niv",
                    timeout=15,
                    verify=False  # 🔥 CLAVE: SOLO AQUÍ
                )

                txt=r.text.lower()

                status=r.status_code
                login="sign in" in txt
                locked="your account is locked" in txt
                csrf=bool(re.search(r'authenticity_token',r.text))

                print(f"[{time.strftime('%H:%M:%S')}] {status} login:{login} lock:{locked} csrf:{csrf}")

                # CONTROL REAL
                if status!=200 or not csrf:
                    self.rotate()

                if locked:
                    print("LOCK → SLEEP 30m")
                    time.sleep(1800)

            except Exception as e:
                print("ERR:",e)
                self.rotate()

            time.sleep(8)

bot=Nexus()
bot.run()
