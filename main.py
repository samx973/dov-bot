import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# تحميل بيانات الدخول والبيئة
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# إرسال إشعار تيليجرام
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("📬 تم إرسال إشعار تيليجرام.")
        else:
            print("❌ فشل إرسال الإشعار:", response.text)
    except Exception as e:
        print("⚠️ حصل خطأ أثناء إرسال الإشعار:", e)

# تسجيل الدخول
def login(driver):
    try:
        driver.get("https://prenotami.esteri.it")
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(2)
        driver.find_element(By.ID, "login-email").send_keys(USERNAME)
        driver.find_element(By.ID, "login-password").send_keys(PASSWORD)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(5)
        print("✅ تم تسجيل الدخول بنجاح")
        return True
    except Exception as e:
        print("❌ فشل في تسجيل الدخول:", e)
        return False

# إعداد المتصفح بدون واجهة
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# بدء المتصفح
driver = webdriver.Chrome(options=chrome_options)

# إشعار أول ما البوت يشتغل
send_telegram_alert("✅ البوت اشتغل وهو بيراقب خدمة DOV - الساعة: " + time.strftime("%H:%M:%S"))

# تسجيل الدخول أول مرة
if not login(driver):
    driver.quit()
    exit()

# الذهاب إلى صفحة الخدمة
try:
    driver.get("https://prenotami.esteri.it/Services")
    time.sleep(3)
    book_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "BOOK")]')
    if not book_buttons:
        print("❌ لم يتم العثور على زر BOOK.")
        driver.quit()
        exit()
    book_buttons[-1].click()
    time.sleep(3)
except Exception as e:
    print("❌ حصل خطأ أثناء فتح صفحة الخدمة:", e)
    driver.quit()
    exit()

# حلقة الفحص كل 3 دقائق
while True:
    try:
        driver.refresh()
        time.sleep(3)

        # فحص إذا تم تسجيل الخروج
        if "login" in driver.page_source.lower():
            print("🔄 تم تسجيل الخروج - نحاول تسجيل الدخول مرة أخرى...")
            if login(driver):
                driver.get("https://prenotami.esteri.it/Services")
                time.sleep(3)
                book_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "BOOK")]')
                if book_buttons:
                    book_buttons[-1].click()
                    time.sleep(3)
                else:
                    print("❌ لم يتم العثور على زر BOOK بعد إعادة تسجيل الدخول.")
                    time.sleep(180)
                    continue
            else:
                print("❌ فشل إعادة تسجيل الدخول. سيتم المحاولة مجددًا بعد 3 دقائق.")
                time.sleep(180)
                continue

        # فحص وجود مواعيد
        page_text = driver.page_source.lower()
        if (
            "fully booked" in page_text
            or "currently booked" in page_text
            or "nessun appuntamento disponibile" in page_text
            or "all appointments for this service" in page_text
        ):
            print("🔴 مفيش مواعيد - الساعة:", time.strftime("%H:%M:%S"))
        else:
            print("🟢 فيه مواعيد! - الساعة:", time.strftime("%H:%M:%S"))
            send_telegram_alert("🟢 فيه مواعيد دلوقتي في خدمة DOV! إلحق قبل ما تروح 😱")

        time.sleep(180)  # كل 3 دقائق

    except Exception as e:
        error_msg = f"❌ حصل خطأ مفاجئ في البوت:\n{str(e)}\nسيتم إعادة المحاولة بعد 5 دقائق."
        print(error_msg)
        send_telegram_alert(error_msg)
        time.sleep(300)  # انتظر 5 دقايق وأكمل
