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
        # Cari date input (yang ada tanda '-')
        date_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if "-" in (i.get_attribute("value") or "")]
        if not date_inputs:
            print("[!] Date input tidak ditemukan")
            return
            
        d_inp = date_inputs[0]
        print(f"Date input awal: '{d_inp.get_attribute('value')}'")
        
        print("Membuka date picker...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", d_inp)
        time.sleep(1.5)
        
        # Dump date picker modal/calendar
        cal_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'calendar') or contains(@class, 'Calendar') or contains(@class, 'day') or contains(@class, 'Day')]")
        print(f"Ditemukan {len(cal_elements)} elemen kalender")
        
        # Coba pilih hari esok (misal tanggal 22)
        target_day = "22"
        day_cells = driver.find_elements(By.XPATH, f"//span[contains(@class, 'day') and not(contains(@class, 'disabled')) and text()='{target_day}']")
        print(f"Day cells untuk tanggal {target_day}: {len(day_cells)}")
        if day_cells:
            d_cell = day_cells[0]
            print(f"Mengklik tanggal {target_day}...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", d_cell)
            time.sleep(1)
            
        # Tutup / cek nilai
        driver.find_element(By.XPATH, "//body").click()
        time.sleep(1)
        print(f"NILAI FINAL DATE INPUT: '{d_inp.get_attribute('value')}'")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
