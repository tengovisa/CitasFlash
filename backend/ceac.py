import requests, time, re
from bs4 import BeautifulSoup

CEAC_URL = "https://ceac.state.gov/CEACStatTracker/Status.aspx?App=NIV"
CAPTCHA_KEY = "63b6b5526264e00990fcd823d9b42e09"

def solve_captcha(site_key, url):
    r = requests.post("https://2captcha.com/in.php", data={
        "key": CAPTCHA_KEY, "method": "userrecaptcha",
        "googlekey": site_key, "pageurl": url, "json": 1
    }).json()
    if r.get("status") != 1: raise Exception(f"2captcha error: {r}")
    captcha_id = r["request"]
    for _ in range(30):
        time.sleep(5)
        res = requests.get(f"https://2captcha.com/res.php?action=get&key={CAPTCHA_KEY}&id={captcha_id}&json=1").json()
        if res.get("status") == 1: return res["request"]
        if res.get("request") == "ERROR_CAPTCHA_UNSOLVABLE": raise Exception("Captcha unsolvable")
    raise Exception("Timeout captcha")

def check_ceac(case_number, surname, passport):
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
    r = s.get(CEAC_URL, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Obtener viewstate
    viewstate = soup.find("input", {"id": "__VIEWSTATE"})["value"]
    viewstategenerator = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})["value"]
    eventvalidation = soup.find("input", {"id": "__EVENTVALIDATION"})["value"]
    
    # Resolver captcha
    site_key_tag = soup.find("div", {"class": "g-recaptcha"})
    site_key = site_key_tag["data-sitekey"] if site_key_tag else "6LfMbN8SAAAAAHBcR-oXhGqB2XQVJjETG7G4YG2R"
    token = solve_captcha(site_key, CEAC_URL)
    
    # Submit form
    r2 = s.post(CEAC_URL, data={
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$drpDEMO_AppType": "NIV",
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$drpDEMO_Location": "DOP",
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$tbxDEMO_AppID": case_number,
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$tbxDEMO_Surname": surname,
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$tbxDEMO_PassportID": passport,
        "g-recaptcha-response": token,
        "ctl00$SiteContentPlaceholder$ucApplicationStatusView$btnDEMO_Submit": "Submit"
    }, timeout=20)
    
    soup2 = BeautifulSoup(r2.text, "html.parser")
    status_div = soup2.find("div", {"id": "ctl00_SiteContentPlaceholder_ucApplicationStatusView_pnlStatusInfo"})
    if status_div:
        return {"success": True, "status": status_div.get_text().strip()[:300]}
    return {"success": False, "error": "No se encontró resultado"}

if __name__ == "__main__":
    # Test
    result = check_ceac("AA0020AKAX", "GARCIA", "AB123456")
    print(result)
