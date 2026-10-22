import sys
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("core"))
from utils import setup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def test_time_selection():
    profile_path = os.path.abspath("tt_profiles/Amin")
    driver = setup_driver(profile_path, headless=False)
    
    try:
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=upload")
        time.sleep(5)
        
        # Joyride
        try:
            driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
            got_it = driver.find_elements(By.XPATH, "//button[contains(., 'Got it')]")
            if got_it: driver.execute_script("arguments[0].click();", got_it[0])
        except Exception:
            pass
            
        # Upload test video
        video_path = os.path.abspath("content/bakteri-vs-antiseptik-mikroskop/bakteri-vs-antiseptik-mikroskop.mp4")
        driver.find_element(By.XPATH, "//input[@type='file']").send_keys(video_path)
        print("[i] Menunggu Schedule...")
        
        for _ in range(60):
            time.sleep(2)
            try:
                driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
            except Exception:
                pass
            radios = driver.find_elements(By.XPATH, "//label[contains(., 'Schedule')] | //input[@type='radio'][@value='schedule']")
            if radios and any(r.is_displayed() for r in radios):
                radio = [r for r in radios if r.is_displayed()][0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", radio)
                break
                
        time.sleep(2)
        
        # Cari time input
        time_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if ":" in (i.get_attribute("value") or "")]
        if not time_inputs:
            print("[!] time input tidak ditemukan")
            return
            
        t_inp = time_inputs[0]
        initial_val = t_inp.get_attribute("value")
        print(f"[i] Initial Time Value: '{initial_val}'")
        
        # Buka dropdown timepicker
        print("[i] Membuka dropdown timepicker...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", t_inp)
        time.sleep(1)
        
        # Target: Jam 20, Menit 45
        target_hour = "20"
        target_min = "45"
        
        # Cek apakah dropdown terbuka
        dropdown = driver.find_elements(By.XPATH, "//div[contains(@class, 'tiktok-timepicker-time-picker-container')]")
        print(f"[i] Dropdown terbuka? {bool(dropdown and dropdown[0].is_displayed())}")
        
        # METODE 1: Klik langsung pada span vs div option item
        # Coba klik div option-item parent atau span
        hour_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-left') and text()='{target_hour}']")
        if hour_spans:
            h_span = hour_spans[0]
            # Coba scroll ke item dan klik
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", h_span)
            time.sleep(0.3)
            # Coba ActionChains click vs execute_script click
            print(f"[i] Mengklik jam {target_hour} via JS click...")
            # Coba klik parent div
            parent_div = h_span.find_element(By.XPATH, "..")
            driver.execute_script("arguments[0].click();", parent_div)
            # Juga klik spannya
            driver.execute_script("arguments[0].click();", h_span)
            time.sleep(0.5)
            
        min_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-right') and text()='{target_min}']")
        if min_spans:
            m_span = min_spans[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", m_span)
            time.sleep(0.3)
            parent_div = m_span.find_element(By.XPATH, "..")
            print(f"[i] Mengklik menit {target_min} via JS click...")
            driver.execute_script("arguments[0].click();", parent_div)
            driver.execute_script("arguments[0].click();", m_span)
            time.sleep(0.5)
            
        # Cek nilai time input sekarang
        current_val = t_inp.get_attribute("value")
        print(f"[?] Nilai time input setelah klik: '{current_val}' (Target: {target_hour}:{target_min})")
        
        # Coba tutup dropdown dengan klik di luar atau blur
        print("[i] Mencoba klik body / blur untuk menutup dropdown...")
        driver.execute_script("arguments[0].blur();", t_inp)
        # Coba klik container judul atau area luar
        try:
            bg = driver.find_element(By.XPATH, "//div[contains(@class, 'scheduled-title-container')]")
            driver.execute_script("arguments[0].click();", bg)
        except Exception:
            pass
        time.sleep(1)
        
        final_val = t_inp.get_attribute("value")
        print(f"[!] Nilai FINAL time input: '{final_val}'")
        
        # Apakah kelas active berubah?
        active_hours = driver.find_elements(By.XPATH, "//span[contains(@class, 'tiktok-timepicker-left') and contains(@class, 'is-active')]")
        active_mins = driver.find_elements(By.XPATH, "//span[contains(@class, 'tiktok-timepicker-right') and contains(@class, 'is-active')]")
        h_act = [h.text for h in active_hours]
        m_act = [m.text for m in active_mins]
        print(f"[i] Active items di DOM: Jam={h_act}, Menit={m_act}")
        
        # Coba juga METODE 2: ActionChains mouse click fisik jika JS click tidak memicu React synthetic event
        if final_val != f"{target_hour}:{target_min}":
            print("[!] JS click tidak mengubah nilai input. Mencoba METODE 2: ActionChains Mouse Click...")
            # Buka dropdown lagi
            driver.execute_script("arguments[0].click();", t_inp)
            time.sleep(0.5)
            if hour_spans:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hour_spans[0])
                time.sleep(0.3)
                ActionChains(driver).move_to_element(hour_spans[0]).click().perform()
                time.sleep(0.5)
            if min_spans:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", min_spans[0])
                time.sleep(0.3)
                ActionChains(driver).move_to_element(min_spans[0]).click().perform()
                time.sleep(0.5)
                
            val_after_ac = t_inp.get_attribute("value")
            print(f"[?] Nilai setelah ActionChains: '{val_after_ac}'")
            
        time.sleep(3)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_time_selection()
