import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Deteksi Environment (Termux Android atau PC Desktop)
IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
if IS_TERMUX:
    CHROME_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
    CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"
else:
    CHROME_PATH = None
    CHROMEDRIVER_PATH = None

# Direktori untuk menyimpan profil (cookies, session, dll)
PROFILE_PATH = os.path.join(os.getcwd(), "tiktok_profile")

def cleanup_profile(profile_path):
    """Menghapus folder cache dan file tidak penting agar ukuran profil tetap kecil."""
    if not os.path.exists(profile_path):
        return

    # Daftar folder yang aman untuk dihapus (hanya cache/temp, bukan session)
    folders_to_remove = [
        "Default/Cache",
        "Default/Code Cache",
        "Default/GPUCache",
        "Default/Service Worker/CacheStorage",
        "Default/Service Worker/ScriptCache",
        "Default/DawnWebGPUCache",
        "Default/DawnGraphiteCache",
        "Default/IndexedDB", # TikTok bisa pakai ini banyak, hapus jika ingin benar-benar bersih
        "component_crx_cache",
        "TranslateKit",
        "WasmTtsEngine",
        "OnDeviceHeadSuggestModel",
        "OptimizationHints",
        "GraphiteDawnCache",
        "GrShaderCache",
        "BrowserMetrics-spare.pma"
    ]

    print(f"[*] Melakukan pembersihan profil di: {profile_path}...")
    for folder in folders_to_remove:
        full_path = os.path.join(profile_path, folder)
        if os.path.exists(full_path):
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
            except Exception as e:
                print(f"[-] Gagal menghapus {folder}: {e}")
    print("[+] Pembersihan selesai.")

def setup_driver():
    chrome_options = Options()
    if CHROME_PATH:
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
    
    # Optimasi ukuran profil (Disable features yang tidak perlu)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-features=Translate,OptimizationHints")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    # Ubah User-Agent agar tidak terdeteksi bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    if IS_TERMUX and CHROMEDRIVER_PATH:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        # Biarkan Selenium di PC mengunduh/mencari driver otomatis
        driver = webdriver.Chrome(options=chrome_options)
    
    # Script untuk menghilangkan deteksi selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def main():
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
        print(f"Membuat folder profil di: {PROFILE_PATH}")

    # Bersihkan sebelum buka
    cleanup_profile(PROFILE_PATH)

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
        # Bersihkan setelah tutup
        cleanup_profile(PROFILE_PATH)

if __name__ == "__main__":
    main()
