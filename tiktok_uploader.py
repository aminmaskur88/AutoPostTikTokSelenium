import os
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.action_chains import ActionChains

# Path biner Termux
CHROME_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"
PROFILE_PATH = os.path.join(os.getcwd(), "tiktok_profile")

def human_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def check_for_captcha(driver):
    """
    Mendeteksi apakah ada popup Captcha yang muncul.
    Jika ada, skrip akan berhenti sementara dan menunggu user menyelesaikannya secara manual di VNC.
    """
    captcha_xpaths = [
        "//*[contains(@id, 'captcha')]",
        "//*[contains(@class, 'captcha')]",
        "//div[@id='secsdk-captcha-drag-wrapper']"
    ]
    
    for xpath in captcha_xpaths:
        try:
            # Cari dengan cepat, tidak perlu eksplisit wait lama
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    print("\n" + "!"*50)
                    print("⚠️ CAPTCHA TERDETEKSI!")
                    print("⚠️ Silakan buka VNC dan selesaikan Captcha secara manual.")
                    print("⚠️ Skrip sedang menunggu (Auto-resume jika captcha hilang)...")
                    print("!"*50 + "\n")
                    
                    # Tunggu sampai elemen captcha tersebut hilang dari layar
                    WebDriverWait(driver, 600).until_not(EC.visibility_of(el))
                    
                    print("[+] Captcha berhasil diselesaikan. Melanjutkan proses...")
                    time.sleep(2)
                    return True # Captcha ditemukan dan diselesaikan
        except:
            continue
    return False

def setup_driver(headless=False):
    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH
    
    # Konfigurasi Headless (Hemat RAM & Tanpa VNC)
    if headless:
        print("[*] Berjalan dalam mode HEADLESS (Hemat RAM)...")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--mute-audio") # Hemat CPU (tanpa suara)
    
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def simulate_warmup(driver):
    print("Memulai simulasi pemanasan (interaksi).")
    try:
        driver.get("https://www.tiktok.com/foryou")
        human_delay(5, 8)
        
        # Daftar XPath tombol menu samping (For You, Following, Explore, Live, dll.) dari hasil get_xpath
        menu_xpaths = [
            "/html/body/div/div[2]/main/aside/div/div[2]/button",
            "/html/body/div/div[2]/main/aside/div/div[2]/button/div/div/svg",
            "/html/body/div/div[2]/main/aside/div/div/button/div/div/svg",
            "/html/body/div/div[2]/main/aside/div[2]/section/div/div[2]/div/button/div/div/svg"
        ]
        
        # Pilih 2-3 menu acak untuk diklik sebagai pemanasan
        num_clicks = random.randint(2, 3)
        for _ in range(num_clicks):
            xpath_to_click = random.choice(menu_xpaths)
            try:
                # Tunggu elemen muncul (menggunakan presence karena target berupa SVG sering dianggap tidak clickable oleh Selenium)
                btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath_to_click)))
                print(f"[*] Warmup: Menemukan dan mengklik menu samping...")
                driver.execute_script("arguments[0].click();", btn) # Gunakan JS click agar lebih andal
                human_delay(3, 7)
                
                # Pindah ke video selanjutnya dengan tombol Panah Bawah (Standar TikTok Web)
                print("[*] Warmup: Menekan tombol Panah Bawah untuk melihat video berikutnya...")
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
                human_delay(2, 5)
            except Exception as e:
                print(f"[-] Warmup: Tombol menu tidak ditemukan, mengalihkan ke tonton video (Panah Bawah)...")
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
                human_delay(3, 7)
                
    except Exception as e:
        print(f"[!] Gagal warmup: {e}, lanjut ke upload...")

def upload_post(folder_path, use_headless=False):
    status_file = os.path.join(folder_path, "uploaded.status")
    if os.path.exists(status_file):
        print(f"Skipping: Postingan di {folder_path} sudah pernah diupload.")
        return False

    meta_file = os.path.join(folder_path, "post_meta.json")
    if not os.path.exists(meta_file):
        print(f"Error: {meta_file} tidak ditemukan.")
        return False

    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    video_file = None
    has_photo = False
    for f in os.listdir(folder_path):
        full_path = os.path.abspath(os.path.join(folder_path, f))
        if f.lower().endswith(".mp4"):
            video_file = full_path
            break
        elif f.lower().endswith((".jpg", ".png", ".jpeg")):
            has_photo = True
    
    if not video_file:
        if has_photo:
            print(f"[!] SKIP: Folder '{os.path.basename(folder_path)}' berisi foto. Ini foto gak bisa di upload. Lanjut ke folder berikutnya...")
        else:
            print(f"Error: Tidak ada file video (.mp4) ditemukan di folder {folder_path}. Skip...")
        return False

    # Bangun caption dan bersihkan karakter \r agar tidak error di Linux/Termux
    caption_raw = f"{meta['post_title']}\n\n{meta['summary']}\n\n{' '.join(meta['hashtags'])}\n\n{meta['cta']}"
    caption = caption_raw.replace("\r", "")
    
    if len(caption) > 2200:
        caption = caption[:2195] + "..."

    driver = setup_driver(headless=use_headless)
    wait = WebDriverWait(driver, 60)

    try:
        # 1. Warmup (Pemanasan agar tidak terdeteksi bot)
        simulate_warmup(driver)
        
        # 2. Halaman Upload
        print(f"Menuju halaman upload untuk: {meta['post_title']}")
        driver.get("https://www.tiktok.com/creator-center/upload")
        human_delay(8, 12)
        
        # Cek Captcha saat masuk halaman
        check_for_captcha(driver)

        # 3. Upload Media
        print("Mengunggah media...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        if video_file:
            file_input.send_keys(video_file)
        else:
            file_input.send_keys("\n".join(media_files))
        
        print("Media sedang diunggah. Menunggu proses preview (25 detik).")
        time.sleep(25) 
        
        # Cek Captcha setelah upload media
        check_for_captcha(driver)

        # 4. Cari Kotak Caption (RELIABLE METHOD)
        print("Mencari kotak caption...")
        time.sleep(5) # Jeda ekstra agar UI stabil setelah upload
        
        # Cari satu kali saja yang paling akurat
        caption_xpath = "//div[contains(@class, 'caption-editor')]//div[@role='textbox'] | //div[@role='textbox'] | //div[@contenteditable='true']"
        caption_box = wait.until(EC.presence_of_element_located((By.XPATH, caption_xpath)))

        # Pastikan elemen terlihat
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", caption_box)
        time.sleep(2)

        print(f"Menyalin caption ke clipboard via simulasi tombol fisik...")
        # Teknik Paling Handal: Injeksi tombol Copy dan KLIK secara fisik
        driver.execute_script("""
            var text = arguments[0];
            var btn = document.createElement("button");
            btn.id = "manual-copy-btn";
            btn.innerText = "COPY CAPTION";
            btn.style.position = "fixed";
            btn.style.top = "0";
            btn.style.left = "0";
            btn.style.zIndex = "9999";
            btn.onclick = function() {
                var textArea = document.createElement("textarea");
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                console.log('COPY_SUCCESS');
            };
            document.body.appendChild(btn);
        """, caption)
        
        # Klik tombol yang baru dibuat secara fisik lewat Selenium (agar dianggap user action)
        try:
            copy_btn = driver.find_element(By.ID, "manual-copy-btn")
            copy_btn.click()
            print("[+] Tombol Copy diklik, teks seharusnya sudah di clipboard.")
            time.sleep(1)
            # Hapus tombol setelah dipakai agar tidak mengganggu UI
            driver.execute_script("document.getElementById('manual-copy-btn').remove();")
        except Exception as e:
            print(f"[!] Gagal klik tombol copy manual: {e}")

        print("Mengarahkan mouse dan klik manual ke kotak caption...")
        target = driver.find_element(By.XPATH, caption_xpath)
        actions = ActionChains(driver)
        actions.move_to_element(target).click().perform()
        time.sleep(1)

        print("Membersihkan dan menempelkan caption (Ctrl+A -> Backspace -> Ctrl+V)...")
        # 1. Bersihkan (Ctrl+A -> Backspace)
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)
        actions.send_keys(Keys.BACKSPACE).perform()
        time.sleep(1)

        # 2. Tempel (Ctrl+V)
        print("Menekan Ctrl + V...")
        actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
        time.sleep(2)
        
        # 3. Klik area netral untuk memicu penyimpanan (PENTING)
        print("Klik area netral untuk memicu save (blur)...")
        try:
            # Gunakan elemen judul sebagai area aman
            neutral = driver.find_element(By.XPATH, "//div[contains(text(), 'Upload video')] | //h1")
            actions.move_to_element(neutral).click().perform()
        except:
            driver.execute_script("document.body.click();")
        
        human_delay(2, 4)
        
        # Verifikasi akhir
        actual_text = driver.execute_script("return arguments[0].innerText;", target)
        print(f"Verifikasi: Jumlah karakter di kotak sekarang = {len(actual_text)}")
        human_delay(3, 5)

        # Cek Captcha sebelum posting
        check_for_captcha(driver)

        # 5. Tombol Post
        print("Mengecek tombol Post...")
        # Scroll perlahan ke bawah
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
        time.sleep(2)

        # Daftar kandidat XPath untuk tombol Post
        post_candidates = [
            "/html/body/div/div/div/div[2]/div[2]/div/div/div/div[6]/div/button", # Induk dari temuan user
            "//button[contains(., 'Post')]",
            "//div[contains(@class, 'button')]//button[contains(., 'Post')]",
            "//button[@type='button' and contains(., 'Post')]"
        ]
        
        post_button = None
        for xpath in post_candidates:
            try:
                print(f"Mencoba mencari tombol Post dengan XPath: {xpath}")
                btn = driver.find_element(By.XPATH, xpath)
                if btn.is_displayed():
                    post_button = btn
                    break
            except:
                continue

        if not post_button:
            print("[!] Tombol Post tidak ditemukan dengan XPath otomatis.")
            print("[*] SILAKAN KLIK TOMBOL 'POST' MANUAL DI VNC SEKARANG!")
        else:
            try:
                # Scroll ke tombol
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_button)
                time.sleep(2)

                # Tunggu aktif jika masih disabled
                try:
                    print("[*] Menunggu tombol aktif (max 30 detik)...")
                    WebDriverWait(driver, 30).until(lambda d: post_button.get_attribute("disabled") is None)
                except:
                    print("[!] Tombol tetap nonaktif, mencoba klik saja...")

                print("[+] Mengeklik tombol Post...")
                # Coba klik langsung, jika gagal gunakan JavaScript pada pusat elemen
                for attempt in range(3):
                    try:
                        post_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", post_button)
                    
                    human_delay(3, 5)

                    # Cek peringatan konten/hak cipta
                    try:
                        warning_xpath = "//*[contains(text(), 'Content may be')] | //*[contains(text(), 'copyright')]"
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, warning_xpath)))
                        print("[!] Peringatan 'Content may be' muncul. Menutup...")
                        
                        # Tutup popup
                        close_xpaths = ["//button[contains(@class, 'close')]", "//div[contains(@class, 'close')]", "//div[contains(@role, 'dialog')]//svg/.."]
                        closed = False
                        for cx in close_xpaths:
                            try:
                                btn = driver.find_element(By.XPATH, cx)
                                if btn.is_displayed():
                                    btn.click()
                                    closed = True
                                    break
                            except: continue
                        
                        if not closed:
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        
                        human_delay(2, 4)
                        continue # Ulangi klik post
                    except:
                        break # Tidak ada peringatan, lanjut

                print("[+] Klik berhasil dikirim.")
                
                # Konfirmasi popup "Post now" jika muncul
                try:
                    print("[*] Menunggu popup konfirmasi 'Post now'...")
                    post_now_xpath = "//button[contains(., 'Post now')] | //button[contains(., 'Post Now')]"
                    post_now_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, post_now_xpath)))
                    post_now_btn.click()
                    print("[+] Tombol 'Post now' diklik. Postingan terkirim!")
                except:
                    print("[*] Popup 'Post now' tidak muncul, mungkin sudah terposting otomatis.")
            except Exception as e:
                print(f"[!] Error saat klik tombol: {e}")
        
        print("Menunggu konfirmasi sukses (20 detik).")
        time.sleep(15)
        
        # Tandai sukses
        with open(status_file, "w") as f:
            f.write(f"Uploaded on: {time.ctime()}")
        print(f"BERHASIL: {meta['post_title']} telah diupload.")
        return True

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TIKTOK AUTO UPLOADER")
    print("="*50)
    
    # Menanyakan opsi Headless
    headless_input = input("Jalankan tanpa tampilan (Hemat RAM & Tanpa VNC)? (y/n): ").strip().lower()
    is_headless = True if headless_input == 'y' else False

    # Menanyakan folder media ke user
    user_input = input("Masukkan nama folder media (tekan Enter untuk default 'Post'): ").strip()
    base_post_dir = user_input if user_input else "Post"

    # Menanyakan jeda waktu antar postingan (DALAM MENIT)
    delay_input = input("Masukkan jeda antar postingan dalam MENIT (tekan Enter untuk acak 2-5 menit): ").strip()
    custom_delay_seconds = int(delay_input) * 60 if delay_input.isdigit() else None
    
    if not os.path.exists(base_post_dir):
        print(f"Error: Folder '{base_post_dir}' tidak ditemukan.")
    else:
        post_folders = [f for f in os.listdir(base_post_dir) if os.path.isdir(os.path.join(base_post_dir, f))]
        if not post_folders:
            print(f"Tidak ada folder postingan.")
        else:
            for i, folder in enumerate(post_folders):
                folder_path = os.path.join(base_post_dir, folder)
                print(f"\nPROSES: {folder}")
                success = upload_post(folder_path, use_headless=is_headless)
                
                # Jeda antar postingan hanya jika berhasil dan bukan folder terakhir
                if success and i < len(post_folders) - 1:
                    delay = custom_delay_seconds if custom_delay_seconds is not None else random.randint(120, 300)
                    print(f"\nMenunggu {delay / 60:.1f} menit sebelum proses berikutnya...")
                    for remaining in range(int(delay), 0, -1):
                        mins, secs = divmod(remaining, 60)
                        print(f"\r⏳ Hitung mundur: {mins:02d}:{secs:02d} detik tersisa... ", end="", flush=True)
                        time.sleep(1)
                    print("\n")
            print("\nSEMUA PROSES SELESAI.")