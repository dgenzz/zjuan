import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ——— CONFIG ———
OUTPUT_FILE   = "polymarket_data.json"
POLL_INTERVAL = 10.0  # seconds

# ——— SETUP WEBDRIVER ———
options = Options()
options.add_experimental_option("detach", True)   # keep Chrome open after script ends
driver = webdriver.Chrome(options=options)

# ——— NAVIGATE ONCE ———
driver.get("https://polymarket.com/sports/live")
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.XPATH, "//button[.//span[contains(text(),'¢')]]"))
)
time.sleep(3)  # let React render

# ——— POLL LOOP ———
try:
    while True:
        start = time.time()
        ts    = time.strftime("%Y-%m-%d %H:%M:%S")

        # (Re)scroll to load everything
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(0.5)

        # scrape all odds-buttons
        btns = driver.find_elements(By.XPATH, "//button[.//span[contains(text(),'¢')]]")
        data = []
        for i in range(0, len(btns), 2):
            try:
                b1, b2 = btns[i], btns[i+1]
                t1 = b1.find_element(By.XPATH, ".//span[contains(@class,'c-kcELIr')]").text.upper()
                t2 = b2.find_element(By.XPATH, ".//span[contains(@class,'c-kcELIr')]").text.upper()
                c1 = float(b1.find_element(By.XPATH, ".//span[contains(text(),'¢')]")
                           .text.replace("¢",""))
                c2 = float(b2.find_element(By.XPATH, ".//span[contains(text(),'¢')]")
                           .text.replace("¢",""))
                o1, o2 = round(100/c1,2), round(100/c2,2)
                data.append({"match":i//2+1,"team1":t1,"odd1":o1,"team2":t2,"odd2":o2})
            except Exception as e:
                print(f"[{ts}] ⚠️ Skipped pair {i//2}: {e}")

        # print table to terminal
        print(f"\n[{ts}] Polymarket odds:")
        for match in data:
            print(f"  Match {match['match']}: {match['team1']} {match['odd1']}  |  {match['team2']} {match['odd2']}")

        # dump to JSON
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)

        # wait up to next cycle
        elapsed = time.time() - start
        time.sleep(max(0, POLL_INTERVAL - elapsed))

except KeyboardInterrupt:
    print("\n🛑 Monitoring stopped by user. Browser remains open.")
