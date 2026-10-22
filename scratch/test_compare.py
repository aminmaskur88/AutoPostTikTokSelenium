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

def main():
    profile_path = os.path.abspath("tt_profiles/Amin")
    driver = setup_driver(profile_path, headless=False)
    try:
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=upload")
        time.sleep(5)
        
        # Upload
        video_path = os.path.abspath("content/bakteri-vs-antiseptik-mikroskop/bakteri-vs-antiseptik-mikroskop.mp4")
        driver.find_element(By.XPATH, "//input[@type='file']").send_keys(video_path)
        print("[i] Menunggu Schedule...")
        
        for _ in range(60):
            time.sleep(2)
            radios = driver.find_elements(By.XPATH, "//label[contains(., 'Schedule')] | //input[@type='radio'][@value='schedule']")
            if radios and any(r.is_displayed() for r in radios):
                radio = [r for r in radios if r.is_displayed()][0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", radio)
                break
                
        time.sleep(2)
        time_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if ":" in (i.get_attribute("value") or "")]
        t_inp = time_inputs[0]
        print(f"Time input saat ini: {t_inp.get_attribute('value')}")
        
        # Buka dropdown
        print("Membuka dropdown dengan klik t_inp...")
        driver.execute_script("arguments[0].click();", t_inp)
        time.sleep(1)
        
        # Cek class dropdown
        dd = driver.find_element(By.XPATH, "//div[contains(@class, 'tiktok-timepicker-time-picker-container')]")
        print(f"Class dropdown saat terbuka: '{dd.get_attribute('class')}'")
        
        # Target: 19:30
        target_h = "19"
        target_m = "30"
        
        # Cari elemen span 19
        spans_19 = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-left') and text()='{target_h}']")
        print(f"Spans untuk jam {target_h} ditemukan: {len(spans_19)}")
        if spans_19:
            s = spans_19[0]
            print(f"Sebelum klik jam, is_displayed={s.is_displayed()}")
            parent = s.find_element(By.XPATH, "..")
            print(f"Parent tag={parent.tag_name}, class={parent.get_attribute('class')}")
            
            # Coba scroll dan klik
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", s)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", parent)
            driver.execute_script("arguments[0].click();", s)
            time.sleep(0.5)
            print(f"Nilai input setelah klik jam {target_h}: {t_inp.get_attribute('value')}")
            
        # Cari elemen span 30
        spans_30 = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-right') and text()='{target_m}']")
        print(f"Spans untuk menit {target_m} ditemukan: {len(spans_30)}")
        if spans_30:
            s_m = spans_30[0]
            parent_m = s_m.find_element(By.XPATH, "..")
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", s_m)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", parent_m)
            driver.execute_script("arguments[0].click();", s_m)
            time.sleep(0.5)
            print(f"Nilai input setelah klik menit {target_m}: {t_inp.get_attribute('value')}")
            
        # Tutup dropdown
        print("Menutup dropdown...")
        driver.execute_script("arguments[0].blur();", t_inp)
        # klik di luar
        driver.find_element(By.XPATH, "//body").click()
        time.sleep(1)
        print(f"NILAI FINAL INPUT: {t_inp.get_attribute('value')}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
