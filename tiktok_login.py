import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Path biner yang ditemukan di Termux
CHROME_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"

# Direktori untuk menyimpan profil (cookies, session, dll)
PROFILE_PATH = os.path.join(os.getcwd(), "tiktok_profile")

def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH
    
    # Gunakan direktori profil untuk menyimpan sesi login
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # Argumen tambahan agar berjalan lebih lancar di Termux/Linux
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Ubah User-Agent agar tidak terdeteksi bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Script untuk menghilangkan deteksi selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def main():
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
        print(f"Membuat folder profil di: {PROFILE_PATH}")

    print("Membuka TikTok... Silakan login secara MANUAL.")
    print("Setelah login berhasil, biarkan halaman terbuka sebentar.")
    print("Tekan Ctrl+C di terminal ini jika sudah selesai untuk menutup browser.")
    
    driver = setup_driver()
    try:
        driver.get("https://www.tiktok.com/login")
        
        # Biarkan browser tetap terbuka agar user bisa login manual
        while True:
            time.sleep(1)
            # Anda bisa memantau URL, jika sudah masuk ke feed, berarti login sukses
            if "tiktok.com/foryou" in driver.current_url or "tiktok.com/@" in driver.current_url:
                print("\n[!] Terdeteksi sudah masuk ke halaman utama/profil.")
                print("[!] Sesi login Anda tersimpan di folder 'tiktok_profile'.")
                
    except KeyboardInterrupt:
        print("\nMenutup browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
