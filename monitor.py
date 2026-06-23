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
            time.sleep(7)   # повече време за зареждане
            
            # По-точно търсене
            body_text = page.inner_text("body")
            page_text_lower = body_text.lower()
            
            if "най-ранен час" in page_text_lower:
                # Търсим целия ред
                lines = [line.strip() for line in body_text.splitlines() if line.strip()]
                for line in lines:
                    if "Най-ранен час" in line or "най-ранен час" in line.lower():
                        print(f"📅 Намерено: {line}")
                        # Изпращаме ако е по-рано от ноември
                        if any(m in line.lower() for m in ["юли", "август", "септември", "октомври"]):
                            send_telegram(line)
                        else:
                            print("Все още ноември или по-късно")
                        return  # спираме след първото намиране
                print("Намерих 'Най-ранен час', но не можах да извлека реда")
            else:
                print("Не открих 'Най-ранен час' в текста")
                print("Първите 500 символа:", body_text[:500])
                
        except Exception as e:
            error_msg = f"Грешка: {str(e)[:200]}"
            print(error_msg)
            send_telegram(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
