import os
import time
import datetime
import requests
from playwright.sync_api import sync_playwright

URL = "https://superdoc.bg/lekar/transportna-oblastna-lekarska-ekspertna-komisia-tolek"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LAST_EARLIEST = "16 ноември"  # ще се обновява

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram не е конфигуриран")
        return
    text = f"🔔 **ТОЛЕК - РАНЕН ЧАС!**\n\n{message}\n\n🔗 {URL}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )

def check_appointments():
    global LAST_EARLIEST
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="networkidle", timeout=30000)
            time.sleep(6)  # изчакване за JS

            # Търсим текста с най-ранния час
            text = page.inner_text("body")
            if "Най-ранен час:" in text:
                line = [line for line in text.splitlines() if "Най-ранен час:" in line][0]
                print(f"[{datetime.datetime.now()}] {line}")

                if "ноември" not in line or any(month in line for month in ["юли", "август", "септември", "октомври"]):
                    if line != LAST_EARLIEST:
                        send_telegram(line)
                        LAST_EARLIEST = line
                else:
                    print("Все още ноември или по-късно")
            else:
                print("Не намерих 'Най-ранен час:'")
        except Exception as e:
            print("Грешка:", e)
            send_telegram(f"⚠️ Грешка при проверка: {str(e)[:200]}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
