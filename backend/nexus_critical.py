import time,re,uuid
from curl_cffi import requests

CID="hl_d36aad6c"
ZONE="residential_proxy2"
PWD="yrkzbddify53"

EMAIL="TU_EMAIL"
PASSWORD="TU_PASSWORD"

class N:
    def __init__(self):
        self.sid="sess_"+uuid.uuid4().hex
        self.new()

    def new(self):
        self.s=requests.Session(impersonate="chrome120")
        proxy=f"http://brd-customer-{CID}-zone-{ZONE}-country-us-session-{self.sid}:{PWD}@brd.superproxy.io:33335"
        self.s.proxies={"http":proxy,"https":proxy}
        self.s.headers={
            "User-Agent":"Mozilla/5.0",
            "Accept-Language":"en-US,en;q=0.9"
        }

    def rotate(self):
        print("ROTATE IP")
        self.sid="sess_"+uuid.uuid4().hex
        self.new()

    def login(self):
        try:
            r1=self.s.get("https://ais.usvisa-info.com/es-do/niv/users/sign_in",verify=False)
            m=re.search(r'authenticity_token.*value="(.*?)"',r1.text)

            if not m:
                print("NO CSRF")
                return False

            data={
                "user[email]":EMAIL,
                "user[password]":PASSWORD,
                "policy_confirmed":"1",
                "commit":"Sign In",
                "authenticity_token":m.group(1)
            }

            r2=self.s.post("https://ais.usvisa-info.com/es-do/niv/users/sign_in",data=data,verify=False)

            ok="sign out" in r2.text.lower() or "schedule" in r2.text.lower()
            print("LOGIN:", "OK" if ok else "FAIL")

            if not ok:
                self.rotate()

            return ok

        except Exception as e:
            print("LOGIN ERROR:",e)
            self.rotate()
            return False

    def run(self):
        if not self.login():
            return

        while True:
            try:
                r=self.s.get("https://ais.usvisa-info.com/es-do/niv",verify=False)
                txt=r.text.lower()

                print(time.strftime("%H:%M:%S"), "STATUS:", r.status_code)

                if "your account is locked" in txt:
                    print("LOCK → SLEEP 30m")
                    time.sleep(1800)

                elif r.status_code==403:
                    print("403 → ROTATE")
                    self.rotate()

                elif r.status_code==429:
                    print("429 → WAIT")
                    time.sleep(120)

                elif r.status_code==401 or "sign in" in txt:
                    print("SESSION LOST → RELOGIN")
                    self.login()

                else:
                    print("OK")

            except Exception as e:
                print("ERR:",e)
                self.rotate()
                time.sleep(10)

            time.sleep(8)

N().run()
