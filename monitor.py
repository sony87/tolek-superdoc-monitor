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
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
        timeout=10
    )
    print("✅ Telegram изпратен")

def check_appointments():
    print(f"[{datetime.datetime.now()}] 🔍 Проверка на SuperDoc...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL, wait_until="networkidle", timeout=40000)
            time.sleep(8)
            
            # По-точно извличане
            body_text = page.inner_text("body")
            
            # Търсим линията с "Най-ранен час"
            if "Най-ранен час" in body_text:
                lines = [line.strip() for line in body_text.splitlines() if line.strip()]
                for i, line in enumerate(lines):
                    if "Най-ранен час" in line:
                        # Ако е празно след :, взимаме следващия ред или конкатенираме
                        full_line = line
                        if ":" in line and len(line.split(":", 1)[1].strip()) < 5 and i + 1 < len(lines):
                            full_line = line + " " + lines[i + 1]
                        
                        print(f"📅 **НАМЕРЕНО:** {full_line}")
                        send_telegram(full_line)   # Винаги изпращаме за тестване
                        return
            else:
                print("Не открих 'Най-ранен час'")
                print("Първите 400 символа:", body_text[:400])
                
        except Exception as e:
            print(f"❌ Грешка: {e}")
            send_telegram(f"Грешка: {str(e)[:150]}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
