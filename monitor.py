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
            time.sleep(8)
            
            body_text = page.inner_text("body")
            
            # По-умно търсене
            if "Най-ранен час" in body_text:
                # Търсим целия ред, който съдържа "Най-ранен час"
                lines = body_text.splitlines()
                for line in lines:
                    if "Най-ранен час" in line:
                        # Почистваме и взимаме целия текст
                        earliest_line = line.strip()
                        # Ако е само "Най-ранен час:", търсим в следващите няколко реда
                        if earliest_line.endswith("Най-ранен час:") or earliest_line.endswith("Най-ранен час"):
                            # Проверяваме следващите редове
                            idx = lines.index(line)
                            for i in range(idx, min(idx+5, len(lines))):
                                if any(x in lines[i] for x in ["ноември", "октомври", "септември", "август", "юли"]):
                                    earliest_line = lines[i].strip()
                                    break
                        
                        print(f"📅 Намерено: {earliest_line}")
                        
                        lower = earliest_line.lower()
                        if any(m in lower for m in ["юли", "август", "септември", "октомври"]):
                            send_telegram(earliest_line)
                        else:
                            print("Все още ноември или по-късно")
                        return
                
                print("Намерих 'Най-ранен час', но не можах да извлека пълния текст")
            else:
                print("Не открих 'Най-ранен час'")
                
        except Exception as e:
            error_msg = f"Грешка: {str(e)[:200]}"
            print(error_msg)
            send_telegram(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_appointments()
