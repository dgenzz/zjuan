import ssl, json, time
ssl._create_default_https_context = ssl._create_unverified_context

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === SETUP ===
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")  # avoid tiny viewport issues
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")

driver = uc.Chrome(options=options)

# === NAVIGATE & CAPTCHA ===
driver.get("https://stake.com/sports/baseball")
WebDriverWait(driver, 180).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.outcome-content"))
)
print("✅ Stake page loaded — writing to stake_data.json every 10s\n")

# === POLL LOOP & FILE DUMP ===
try:
    while True:
        start = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        outcomes = driver.find_elements(By.CSS_SELECTOR, "div.outcome-content")
        data = []  # will hold dicts for JSON

        if len(outcomes) < 2:
            print(f"[{timestamp}] ⚠️ No odds found")
        else:
            for i in range(0, len(outcomes), 2):
                try:
                    o1, o2 = outcomes[i], outcomes[i+1]
                    team1 = o1.find_element(By.CSS_SELECTOR, "[data-test='outcome-button-name']").text.strip()
                    odd1  = float(o1.find_element(By.CSS_SELECTOR, "div[data-test='fixture-odds'] span").text.strip())
                    team2 = o2.find_element(By.CSS_SELECTOR, "[data-test='outcome-button-name']").text.strip()
                    odd2  = float(o2.find_element(By.CSS_SELECTOR, "div[data-test='fixture-odds'] span").text.strip())
                    data.append({
                        "timestamp": timestamp,
                        "team1": team1,
                        "odd1": odd1,
                        "team2": team2,
                        "odd2": odd2
                    })
                    print(f"[{timestamp}] 📊 {team1}: {odd1} | {team2}: {odd2}")
                except Exception as e:
                    print(f"[{timestamp}] ⚠️ Skipped a pair: {e}")

        # write out stake_data.json
        with open("stake_data.json", "w") as f:
            json.dump(data, f, indent=2)

        # wait next cycle
        elapsed = time.time() - start
        time.sleep(max(0, 10 - elapsed))

except KeyboardInterrupt:
    print("\n🛑 Stopped by user. Browser stays open for manual inspection.")
