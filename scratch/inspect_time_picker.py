import sys
import os
import time
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("core"))
from utils import setup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def main():
    profile_path = os.path.abspath("tt_profiles/Amin")
    print(f"[i] Menggunakan profil: {profile_path}")
    driver = setup_driver(profile_path, headless=False)
    
    try:
        url = "https://www.tiktok.com/tiktokstudio/upload?from=upload"
        print(f"[i] Membuka URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Check login
        if "login" in driver.current_url.lower():
            print("[!] Profil belum login!")
            return
            
        # Tutup joyride jika ada
        try:
            got_it_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Got it') or contains(., 'Mengerti')]")
            for b in got_it_btns:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
            driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
        except Exception:
            pass
            
        # Upload video
        video_path = os.path.abspath("content/bakteri-vs-antiseptik-mikroskop/bakteri-vs-antiseptik-mikroskop.mp4")
        print(f"[i] Mengunggah file test: {video_path}")
        file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        if not file_inputs:
            print("[!] Input file tidak ditemukan!")
            return
            
        file_inputs[0].send_keys(video_path)
        print("[i] File dikirim. Menunggu elemen Schedule muncul...")
        
        # Tunggu sampai Schedule radio muncul
        found_schedule = False
        for _ in range(60):
            time.sleep(2)
            # Dismiss joyride
            try:
                driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
                got_it_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Got it') or contains(., 'Mengerti')]")
                for b in got_it_btns:
                    if b.is_displayed():
                        driver.execute_script("arguments[0].click();", b)
            except Exception:
                pass
                
            radios = driver.find_elements(By.XPATH, "//label[contains(., 'Schedule')] | //input[@type='radio'][@value='schedule']")
            if radios and any(r.is_displayed() for r in radios):
                found_schedule = True
                break
                
        if not found_schedule:
            print("[!] Opsi Schedule tidak muncul dalam 120 detik!")
            return
            
        print("[OK] Opsi Schedule ditemukan! Mengklik Schedule radio...")
        radio = [r for r in radios if r.is_displayed()][0]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", radio)
        time.sleep(2)
        
        # Cari semua input di area penjadwalan
        inputs = driver.find_elements(By.XPATH, "//input")
        print("\n=== DAFTAR SEMUA INPUT DI HALAMAN ===")
        for idx, inp in enumerate(inputs):
            try:
                val = inp.get_attribute("value")
                ph = inp.get_attribute("placeholder")
                cls = inp.get_attribute("class")
                typ = inp.get_attribute("type")
                disp = inp.is_displayed()
                print(f"[{idx}] type={typ}, val='{val}', placeholder='{ph}', displayed={disp}, class='{cls}'")
            except Exception:
                pass
                
        # Cari container date/time picker
        containers = driver.find_elements(By.XPATH, "//*[contains(@class, 'picker') or contains(@class, 'schedule') or contains(@class, 'Schedule')]")
        print(f"\n=== FOUND CONTAINERS ({len(containers)}) ===")
        for c in containers[:10]:
            try:
                print(f"Tag: {c.tag_name}, Class: {c.get_attribute('class')}")
            except Exception:
                pass
                
        # Cari input yang ada jam (misal ":")
        time_inputs = [i for i in inputs if ":" in (i.get_attribute("value") or "")]
        if not time_inputs:
            # Cari input di dalam scheduled picker container
            time_inputs = driver.find_elements(By.XPATH, "//div[contains(@class, 'scheduled-picker')]//input")
            
        print(f"\n[i] Kandidat time input: {len(time_inputs)}")
        for t_inp in time_inputs:
            print(f"  -> val='{t_inp.get_attribute('value')}', class='{t_inp.get_attribute('class')}', outerHTML:\n{t_inp.get_attribute('outerHTML')}")

        if time_inputs:
            target_t_inp = time_inputs[-1] # biasanya input kedua adalah jam
            if len(time_inputs) > 1 and ":" in (time_inputs[1].get_attribute("value") or ""):
                target_t_inp = time_inputs[1]
                
            print(f"\n[i] Mengklik time input: val='{target_t_inp.get_attribute('value')}'")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", target_t_inp)
            time.sleep(2)
            
            # Sekarang cari dropdown / popover yang muncul di body
            print("\n=== MEMINDAI ELEMEN SETELAH TIME INPUT DIKLIK ===")
            # Cari elemen baru yang muncul
            dropdowns = driver.find_elements(By.XPATH, "//*[contains(@class, 'timepicker') or contains(@class, 'time-picker') or contains(@class, 'dropdown') or contains(@class, 'popover') or contains(@class, 'menu') or contains(@role, 'listbox') or contains(@class, 'picker-container')]")
            print(f"Ditemukan {len(dropdowns)} elemen potensial dropdown:")
            for d in dropdowns:
                try:
                    if d.is_displayed():
                        print(f"--- VISIBLE DROPDOWN ELEMENT: tag={d.tag_name}, class={d.get_attribute('class')} ---")
                        html = d.get_attribute("outerHTML")
                        print(html[:500] + "..." if len(html) > 500 else html)
                        with open("scratch/timepicker_dropdown.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print("[OK] Dropdown HTML disimpan ke scratch/timepicker_dropdown.html")
                except Exception:
                    pass

            # Cek apakah span left/right ada di DOM
            hours = driver.find_elements(By.XPATH, "//*[contains(@class, 'timepicker-left') or contains(@class, 'left')]")
            print(f"Elemen hour/left ditemukan: {len(hours)}")
            for h in hours[:5]:
                print(f"  tag={h.tag_name}, class={h.get_attribute('class')}, text='{h.text}'")

            mins = driver.find_elements(By.XPATH, "//*[contains(@class, 'timepicker-right') or contains(@class, 'right')]")
            print(f"Elemen min/right ditemukan: {len(mins)}")
            for m in mins[:5]:
                print(f"  tag={m.tag_name}, class={m.get_attribute('class')}, text='{m.text}'")

            # Mari dump seluruh modal / scheduled-picker container outerHTML
            sched_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'scheduled-picker')]")
            if sched_containers:
                with open("scratch/scheduled_picker_container.html", "w", encoding="utf-8") as f:
                    f.write(sched_containers[0].get_attribute("outerHTML"))
                print("[OK] scheduled_picker_container.html tersimpan.")

        print("\n[i] Selesai pemeriksaan DOM. Menunggu 5 detik lalu keluar (TIDAK MEMPOSTING).")
        time.sleep(5)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
