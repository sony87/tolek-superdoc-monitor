import os
import time
import datetime
import requests
from playwright.sync_api import sync_playwright

URL = "https://superdoc.bg/lekar/transportna-oblastna-lekarska-ekspertna-komisia-tolek"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LAST_SUMMARY_FILE = "last_summary.txt"

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram не е конфигуриран")
        return
    text = f"🔔 **ТОЛЕК София**\n\n{message}\n\n🔗 [Отвори SuperDoc]({URL})"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
        timeout=10
    )
    print("✅ Telegram изпратен")

def should_send_daily_summary():
    try:
        if os.path.exists(LAST_SUMMARY_FILE):
            with open(LAST_SUMMARY_FILE, "r") as f:
                last = f.read().strip()
            if last == datetime.date.today().isoformat():
                return False
        with open(LAST_SUMMARY_FILE, "w") as f:
            f.write(datetime.date.today().isoformat())
        return True
    except:
        return True

def check_appointments():
    print(f"[{datetime.datetime.now()}] 🔍 Проверка...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            time.sleep(10)
            
            body_text = page.inner_text("body")
            
            # === Агресивно търсене ===
            earliest = "Не открит"
            
            if "Най-ранен час" in body_text:
                # Търсим точния ред
                for line in body_text.splitlines():
                    if "Най-ранен час" in line:
                        earliest = line.strip()
                        print(f"✅ НАМЕРЕНО: {earliest}")
                        break
            
            print(f"📋 Пълен текст на реда: {earliest}")
            
            # Логика
            lower = earliest.lower()
            if any(x in lower for x in ["юли", "август", "септември", "октомври"]):
                send_telegram(earliest)
                print("🎉 По-ранен час!")
            elif "ноември" in lower or "декември" in lower:
                if should_send_daily_summary():
                    send_telegram(f"📊 Дневен summary:\n{earliest}")
                    print("📊 Daily summary")
                else:
                    print("📊 Summary вече пратен")
            else:
                send_telegram(earliest)
                
        except Exception as e:
            print(f"❌ Грешка: {e}")
            send_telegram(f"Грешка: {str(e)[:100]}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
