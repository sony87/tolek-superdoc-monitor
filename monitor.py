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
    text = f"🔔 **ТОЛЕК София - Намерен по-ранен час!**\n\n{message}\n\n🔗 [Отвори SuperDoc]({URL})"
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        print("✅ Telegram изпратен")
    except Exception as e:
        print("❌ Грешка Telegram:", e)

def should_send_daily_summary():
    try:
        if os.path.exists(LAST_SUMMARY_FILE):
            with open(LAST_SUMMARY_FILE, "r") as f:
                last_date = f.read().strip()
            if last_date == datetime.date.today().isoformat():
                return False
        with open(LAST_SUMMARY_FILE, "w") as f:
            f.write(datetime.date.today().isoformat())
        return True
    except:
        return True

def check_appointments():
    print(f"[{datetime.datetime.now()}] 🔍 Проверка на SuperDoc...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=40000)
            time.sleep(8)
            
            body_text = page.inner_text("body")
            
            earliest_line = "Не открит"
            
            # По-точно търсене според актуалната структура на страницата
            if "Най-ранен час" in body_text:
                lines = body_text.splitlines()
                for line in lines:
                    if "Най-ранен час" in line:
                        earliest_line = line.strip()
                        print(f"📅 Намерено: {earliest_line}")
                        break
            
            print(f"📋 Пълен ред: {earliest_line}")
            
            # === Умна логика ===
            lower = earliest_line.lower()
            
            if any(m in lower for m in ["юли", "август", "септември", "октомври"]):
                print("🎉 ПО-РАНЕН ЧАС НАМЕРЕН!")
                send_telegram(earliest_line)
            elif "ноември" in lower or "декември" in lower:
                if should_send_daily_summary():
                    send_telegram(f"📊 Дневен summary:\n{earliest_line}\n(Все още няма по-ранни дати)")
                    print("📊 Изпратен daily summary")
                else:
                    print("📊 Summary вече пратен днес")
            else:
                send_telegram(earliest_line)
                
        except Exception as e:
            error_msg = f"Грешка: {str(e)[:150]}"
            print(error_msg)
            send_telegram(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
