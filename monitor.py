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
            page.goto(URL, wait_until="networkidle", timeout=60000)
            time.sleep(10)   # повече време
            
            body_text = page.inner_text("body")
            
            # По-агресивно търсене
            earliest_line = "Не открит"
            
            if "Най-ранен час" in body_text:
                lines = [line.strip() for line in body_text.splitlines() if line.strip()]
                for i, line in enumerate(lines):
                    if "Най-ранен час" in line:
                        earliest_line = line
                        # Ако датата е на следващия ред
                        if i + 1 < len(lines) and any(x in lines[i+1] for x in ["ноември", "октомври", "септември"]):
                            earliest_line += " " + lines[i+1]
                        print(f"📅 **НАМЕРЕНО:** {earliest_line}")
                        break
            
            # Логика
            lower = earliest_line.lower()
            
            if any(m in lower for m in ["юли", "август", "септември", "октомври"]):
                send_telegram(earliest_line)
                print("🎉 По-ранен час!")
            elif "ноември" in lower or "декември" in lower:
                if should_send_daily_summary():
                    send_telegram(f"📊 Дневен summary:\n{earliest_line}")
                    print("📊 Daily summary изпратен")
                else:
                    print("📊 Summary вече пратен днес")
            else:
                send_telegram(earliest_line)
                
        except Exception as e:
            print(f"❌ Грешка: {e}")
            send_telegram(f"Грешка: {str(e)[:100]}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
