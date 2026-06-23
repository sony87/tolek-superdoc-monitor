import os
import time
import datetime
import requests
from playwright.sync_api import sync_playwright

URL = "https://superdoc.bg/lekar/transportna-oblastna-lekarska-ekspertna-komisia-tolek"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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

def check_appointments():
    print(f"[{datetime.datetime.now()}] 🔍 Проверка на SuperDoc...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=40000)
            time.sleep(8)  # повече време за JS
            
            # По-ефективно търсене
            body_text = page.inner_text("body")
            
            # Търсим точно фразата
            if "Най-ранен час" in body_text:
                lines = body_text.splitlines()
                for line in lines:
                    if "Най-ранен час" in line:
                        earliest_line = line.strip()
                        print(f"📅 Намерено: {earliest_line}")
                        
                        # Изпращаме само ако е по-рано от ноември
                        lower_line = earliest_line.lower()
                        if any(m in lower_line for m in ["юли", "август", "септември", "октомври"]):
                            send_telegram(earliest_line)
                        else:
                            print("Все още ноември или по-късно")
                        return
                print("Намерих 'Най-ранен час', но не можах да извлека реда")
            else:
                print("Не открих 'Най-ранен час'")
                print("Първите 300 символа от страницата:", body_text[:300])
                
        except Exception as e:
            error_msg = f"Грешка: {str(e)[:200]}"
            print(error_msg)
            send_telegram(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
