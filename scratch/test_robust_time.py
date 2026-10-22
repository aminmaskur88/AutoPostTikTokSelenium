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

def select_time(driver, t_inp, hour_str, min_str):
    # Format 2 digit
    hour_target = f"{int(hour_str):02d}"
    # Pastikan menit kelipatan 5
    m_val = (int(min_str) // 5) * 5
    min_target = f"{m_val:02d}"
    
    print(f"\n---> MENCOBA SET WAKTU KE: {hour_target}:{min_target} <---")
    
    # 1. Buka dropdown timepicker jika belum terbuka
    dropdowns = driver.find_elements(By.XPATH, "//div[contains(@class, 'tiktok-timepicker-time-picker-container')]")
    if not dropdowns or not dropdowns[0].is_displayed():
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", t_inp)
        time.sleep(0.8)
        
    # 2. Cari Jam
    # Gunakan JavaScript untuk mencari span dengan textContent yang tepat, scroll ke tengah kontainer, dan trigger mousedown + click
    res_hour = driver.execute_script("""
        const target = arguments[0];
        const spans = Array.from(document.querySelectorAll('.tiktok-timepicker-left'));
        const span = spans.find(s => s.textContent.trim() === target);
        if (span) {
            span.scrollIntoView({block: 'center', behavior: 'instant'});
            const parent = span.closest('.tiktok-timepicker-option-item') || span;
            parent.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
            parent.click();
            parent.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
            return true;
        }
        return false;
    """, hour_target)
    print(f"Hasil klik jam {hour_target}: {res_hour}")
    time.sleep(0.5)

    # 3. Cari Menit
    res_min = driver.execute_script("""
        const target = arguments[0];
        const spans = Array.from(document.querySelectorAll('.tiktok-timepicker-right'));
        const span = spans.find(s => s.textContent.trim() === target);
        if (span) {
            span.scrollIntoView({block: 'center', behavior: 'instant'});
            const parent = span.closest('.tiktok-timepicker-option-item') || span;
            parent.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
            parent.click();
            parent.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
            return true;
        }
        return false;
    """, min_target)
    print(f"Hasil klik menit {min_target}: {res_min}")
    time.sleep(0.5)

    # 4. Tutup dropdown dengan klik background atau blur
    driver.execute_script("""
        const bg = document.querySelector('.scheduled-title-container') || document.body;
        bg.click();
    """)
    time.sleep(0.8)
    
    actual_val = t_inp.get_attribute("value")
    expected_val = f"{hour_target}:{min_target}"
    success = (actual_val == expected_val)
    print(f"HASIL: Expected '{expected_val}', Actual: '{actual_val}' -> {'SUKSES [OK]' if success else 'GAGAL [X]'}")
    return success

def run_tests():
    profile_path = os.path.abspath("tt_profiles/Amin")
    driver = setup_driver(profile_path, headless=False)
    try:
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=upload")
        time.sleep(5)
        
        # Joyride
        try:
            driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
        except Exception:
            pass
            
        # Upload
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
        time_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if ":" in (i.get_attribute("value") or "")]
        t_inp = time_inputs[0]
        
        test_cases = [
            ("19", "30"),
            ("08", "15"),
            ("23", "55"),
            ("00", "00"),
            ("12", "45")
        ]
        
        results = []
        for h, m in test_cases:
            res = select_time(driver, t_inp, h, m)
            results.append((f"{h}:{m}", res))
            time.sleep(1)
            
        print("\n=== REKAP TEST TIME PICKER ===")
        all_passed = True
        for t_str, ok in results:
            print(f"  {t_str}: {'BERHASIL' if ok else 'GAGAL'}")
            if not ok: all_passed = False
            
        print(f"\nSTATUS AKHIR: {'SEMUA TEST LOLOS!' if all_passed else 'ADA TEST YANG GAGAL'}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
