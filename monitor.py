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
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        print("✅ Изпратено Telegram съобщение")
    except Exception as e:
        print("❌ Грешка при изпращане:", e)

def check_appointments():
    print(f"[{datetime.datetime.now()}] Проверка на SuperDoc...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=30000)
            time.sleep(5)  # време за зареждане на динамичния текст
            
            # Извличаме целия текст и търсим "Най-ранен час"
            body_text = page.inner_text("body")
            
            if "Най-ранен час" in body_text:
                # Намираме реда с най-ранния час
                lines = body_text.splitlines()
                for line in lines:
                    if "Най-ранен час" in line:
                        earliest = line.strip()
                        print(f"📅 {earliest}")
                        
                        # Ако е по-рано от ноември → уведоми
                        if any(m in earliest.lower() for m in ["юли", "август", "септември", "октомври"]) or "ноември" not in earliest.lower():
                            send_telegram(earliest)
                        else:
                            print("Все още ноември или по-късно")
                        break
                else:
                    print("Не намерих точния ред")
            else:
                print("Не открих 'Най-ранен час'")
                
        except Exception as e:
            error_msg = f"Грешка при проверка: {str(e)[:150]}"
            print(error_msg)
            send_telegram(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
