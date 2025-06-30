# arb.py
import time, json, signal, sys, requests
from pathlib import Path

# 🛠️ Configurations
POLY_JSON     = Path("polymarket_data.json")
STAKE_JSON    = Path("stake_data.json")
POLL_INTERVAL = 300 # seconds

BOT_TOKEN = "7582124200:AAHvDNnzUD_c9n4weSiAD7ufUnTCc7HilH8"  # 🔴 Replace with your bot token
CHAT_ID   = "7220951663"             # 🔴 Replace with your chat id

team_map = {
    "BAL":"Baltimore Orioles","BOS":"Boston Red Sox","CHC":"Chicago Cubs",
    "CWS":"Chicago White Sox","CLE":"Cleveland Guardians","DET":"Detroit Tigers",
    "HOU":"Houston Astros","KC":"Kansas City Royals","LAA":"Los Angeles Angels",
    "LAD":"Los Angeles Dodgers","MIA":"Miami Marlins","MIL":"Milwaukee Brewers",
    "MIN":"Minnesota Twins","NYY":"New York Yankees","NYM":"New York Mets",
    "OAK":"Oakland Athletics","PHI":"Philadelphia Phillies","PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres","SF":"San Francisco Giants","SEA":"Seattle Mariners",
    "STL":"St. Louis Cardinals","TB":"Tampa Bay Rays","TEX":"Texas Rangers",
    "TOR":"Toronto Blue Jays","WSH":"Washington Nationals","COL":"Colorado Rockies",
    "ATL":"Atlanta Braves"
}

def arb_roi(a, b):
    implied = 1/a + 1/b
    return (1 - implied) / implied * 100

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        r = requests.post(url, data=data)
        print(f"📨 Telegram status: {r.status_code}, response: {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def main_loop():
    print("🚀 arb.py started. Polling every 10s...")

    while True:
        poly  = load_json(POLY_JSON)
        stake = load_json(STAKE_JSON)
        if not poly or not stake:
            time.sleep(1)
            continue

        stake_map = { (e["team1"],e["team2"]):(e["odd1"],e["odd2"]) for e in stake }

        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{ts}] Arbitrage scan:")

        msg = f"📊 ROI Scan at {ts}:\n"
        best_game = None
        best_roi = -float('inf')

        for m in poly:
            c1, c2 = m["team1"], m["team2"]
            full1 = team_map.get(c1)
            full2 = team_map.get(c2)
            if not full1 or not full2:
                continue

            p1, p2 = m["odd1"], m["odd2"]
            key = (full1, full2)
            rev = False
            if key not in stake_map:
                key = (full2, full1)
                rev = True
            if key not in stake_map:
                continue

            s1, s2 = stake_map[key]
            if rev:
                s1, s2 = s2, s1

            r1 = arb_roi(p1, s2)
            r2 = arb_roi(p2, s1)

            line = f"{full1} vs {full2} → legs: [{r1:.2f}%, {r2:.2f}%]\n"
            print(" • " + line.strip())
            msg += line

            # Check best ROI
            if r1 > best_roi:
                best_roi = r1
                best_game = f"{full1} vs {full2} (leg1) ROI: {r1:.2f}%"
            if r2 > best_roi:
                best_roi = r2
                best_game = f"{full1} vs {full2} (leg2) ROI: {r2:.2f}%"

        if best_game:
            msg += f"\n🎯 Best ROI: {best_game}"

        # Send Telegram message with all ROIs + best ROI every 10 seconds
        send_telegram(msg.strip())

        time.sleep(POLL_INTERVAL)

def handle_exit(sig, frame):
    print("\n🛑 Exiting arb.py.")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    main_loop()
