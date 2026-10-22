import sys
import os
import time
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("core"))
from utils import setup_driver
from selenium.webdriver.common.by import By

def test_full_schedule():
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
        
        # Kita set target: Besok jam 19:30
        target_dt = datetime.now() + timedelta(days=1)
        target_dt = target_dt.replace(hour=19, minute=30, second=0)
        date_str = target_dt.strftime("%Y-%m-%d")
        hour_target = f"{target_dt.hour:02d}"
        min_target = f"{target_dt.minute:02d}"
        target_day = str(target_dt.day)
        
        print(f"\n---> MENGUJI SET JADWAL LENGKAP: {date_str} {hour_target}:{min_target} <---")
        
        # 1. Date Picker
        date_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if "-" in (i.get_attribute("value") or "")]
        d_inp = date_inputs[0]
        print(f"Date awal: '{d_inp.get_attribute('value')}'")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", d_inp)
        time.sleep(1.5)
        
        day_cells = driver.find_elements(By.XPATH, f"//span[contains(@class, 'day') and not(contains(@class, 'disabled')) and text()='{target_day}']")
        if day_cells:
            print(f"Mengklik hari {target_day}...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", day_cells[0])
            time.sleep(1)
            
        driver.find_element(By.XPATH, "//body").click()
        time.sleep(0.5)
        print(f"Date setelah klik: '{d_inp.get_attribute('value')}'")
        
        # 2. Time Picker
        time_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if ":" in (i.get_attribute("value") or "")]
        t_inp = time_inputs[0]
        print(f"Time awal: '{t_inp.get_attribute('value')}'")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", t_inp)
        time.sleep(1)
        
        # Klik jam
        h_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-left') and text()='{hour_target}']")
        if h_spans:
            print(f"Mengklik jam {hour_target}...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", h_spans[0])
            time.sleep(0.3)
            parent_h = h_spans[0].find_element(By.XPATH, "..")
            driver.execute_script("arguments[0].click();", parent_h)
            driver.execute_script("arguments[0].click();", h_spans[0])
            time.sleep(0.5)
            
        # Klik menit
        m_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-right') and text()='{min_target}']")
        if m_spans:
            print(f"Mengklik menit {min_target}...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", m_spans[0])
            time.sleep(0.3)
            parent_m = m_spans[0].find_element(By.XPATH, "..")
            driver.execute_script("arguments[0].click();", parent_m)
            driver.execute_script("arguments[0].click();", m_spans[0])
            time.sleep(0.5)
            
        driver.find_element(By.XPATH, "//body").click()
        time.sleep(1)
        
        final_date = d_inp.get_attribute("value")
        final_time = t_inp.get_attribute("value")
        print(f"\n==========================================")
        print(f"HASIL AKHIR: Tanggal='{final_date}', Jam='{final_time}'")
        print(f"TARGET     : Tanggal='{date_str}', Jam='{hour_target}:{min_target}'")
        if final_date == date_str and final_time == f"{hour_target}:{min_target}":
            print("STATUS: >>> 100% SUKSES TERSIMPAN! <<<")
        else:
            print("STATUS: >>> BELUM COCOK <<<")
        print(f"==========================================")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_full_schedule()
