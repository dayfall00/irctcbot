import os
import requests
from datetime import datetime

# =========================================================
# TELEGRAM CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")

# =========================================================
# TRAIN DETAILS
# =========================================================

TRAIN_NUMBER = "22500"
TRAIN_NAME   = "Vande Bharat"
FROM         = "BSB"
TO           = "JSME"
DATE         = "27-05-2026"
CLASSES      = ["CC", "EC"]

STATUS_FILE  = "last_status.txt"

# =========================================================
# API
# =========================================================

API_URL = "https://cttrainsapi.confirmtkt.com/api/v1/availability/fetchAvailability"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept":          "*/*",
    "Accept-Language": "en-US,en;q=0.7",
    "Content-Type":    "application/json",
    "Origin":          "https://www.confirmtkt.com",
    "Referer":         "https://www.confirmtkt.com/",
    # ── Auth headers ──────────────────────────────────────
    "ApiKey":          "ct-mweb!2$",
    "ClientId":        "ct-mweb",
    "CT-Token":        "",
    "CT-Userkey":      "",
    "DeviceId":        "7c11e5ef-5e8e-4a07-a2e4-003ff19b61f5",
}

PARAMS_BASE = {
    "trainNo":                TRAIN_NUMBER,
    "quota":                  "GN",
    "sourceStationCode":      FROM,
    "destinationStationCode": TO,
    "dateOfJourney":          DATE,
    "enableTG":               "true",
    "tGPlan":                 "CTG-A42",
    "showTGPrediction":       "false",
    "tgColor":                "DEFAULT",
    "showPredictionGlobal":   "true",
    "showNewMealOptions":     "true",
    "showNewAlternates":      "true",
    "showNewAltText":         "true",
}

# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=15)
        print("Telegram:", r.status_code)
    except Exception as e:
        print("Telegram Error:", e)

# =========================================================
# STATUS FILE
# =========================================================

def load_last_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write(status)

# =========================================================
# FETCH ONE CLASS
# =========================================================

def fetch_class(travel_class):
    params = {**PARAMS_BASE, "travelClass": travel_class}

    try:
        response = requests.post(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )
        print(f"[{travel_class}] HTTP {response.status_code}")

        if response.status_code != 200:
            print(f"[{travel_class}] Response: {response.text[:200]}")
            return None

        data        = response.json()
        avl_day_list = data.get("data", {}).get("avlDayList", [])

        if not avl_day_list:
            return f"{travel_class} → No data"

        # Find our specific travel date
        # API returns "27-5-2026" (no zero-pad), we store "27-05-2026"
        target_day = None
        for day in avl_day_list:
            raw    = day.get("availablityDate", "")
            parts  = raw.split("-")
            normed = f"{int(parts[0]):02d}-{int(parts[1]):02d}-{parts[2]}" if len(parts) == 3 else raw
            if normed == DATE:
                target_day = day
                break

        if not target_day:
            target_day = avl_day_list[0]   # fallback to first

        display = target_day.get("availabilityDisplayName", "Unknown")  # "AVL 37"
        predict = target_day.get("prediction", "")                       # "Available"

        return f"{travel_class} → {display} ({predict})"

    except Exception as e:
        print(f"[{travel_class}] Error: {e}")
        return None

# =========================================================
# MAIN
# =========================================================

print("\n====================================")
print("TRAIN BOT STARTED (API MODE)")
print("====================================\n")

results = []
for cls in CLASSES:
    result = fetch_class(cls)
    if result:
        results.append(result)

if results:
    current_time   = datetime.now().strftime("%d %b %Y | %I:%M %p")
    current_status = (
        f"🚆 {TRAIN_NUMBER} {TRAIN_NAME}\n"
        f"{FROM} → {TO} | {DATE}\n\n"
        + "\n".join(results)
        + f"\n\n🕒 {current_time}"
    )

    print("\nCURRENT STATUS:\n")
    print(current_status)

    last_status = load_last_status()

    if current_status != last_status:
        send_telegram(current_status)
        save_status(current_status)
        print("\nNew update sent!")
    else:
        print("\nNo changes detected.")

else:
    print("\nNo availability data found.")

print("\nFinished.\n")