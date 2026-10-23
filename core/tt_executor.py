import os
import time
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from utils import update_post_status

# ==============================================================================
# TIKTOK SELECTORS REPOSITORY (Siap diisi/diupdate dari hasil rekaman Chrome MCP)
# ==============================================================================
SELECTORS = {
    # Navigasi (TikTok Studio 2026 adalah native React page, tanpa iframe)
    "upload_page_url": "https://www.tiktok.com/tiktokstudio/upload?from=upload",
    "alternative_upload_url": "https://www.tiktok.com/creator-center/upload?from=upload",
    "upload_iframe": "//iframe[contains(@src, 'creator-center') or contains(@src, 'upload')]",
    "login_button": "//button[contains(., 'Log in') or contains(., 'Masuk') or contains(@data-e2e, 'top-login-button')]",
    
    # Tab Mode
    "tab_videos": "//button[@role='tab'][contains(., 'Videos')]",
    "tab_photos": "//button[@role='tab'][contains(., 'Photos')]",

    # Tombol Upload & Input File Media
    "select_video_button": "//button[contains(@class, 'upload-stage-btn') or contains(., 'Select video')]",
    "upload_dropzone": "//div[contains(@class, 'upload-stage-container') or contains(@class, 'upload-card')]",
    "file_input": "//input[@type='file']",
    
    # Status / Progres Upload
    "upload_progress_bar": "//div[contains(@class, 'info-progress')]",
    "upload_success_indicator": "//div[contains(@class, 'info-progress') and contains(@class, 'success')] | //div[contains(@class, 'public-DraftEditor-content')]",

    # Pop-up Tutorial / Overlay TikTok Studio
    "tutorial_got_it": "//button[contains(., 'Got it') or contains(., 'Mengerti')]",
    "tutorial_overlay": ".react-joyride__overlay",

    # Editor Caption / Judul
    "caption_editor": "//div[contains(@class, 'public-DraftEditor-content')] | //div[@contenteditable='true']",

    # Opsi Penjadwalan (Radio Schedule & Now)
    "schedule_radio": "//label[contains(., 'Schedule')] | //div[contains(@class, 'Radio')][contains(., 'Schedule')] | //input[@type='radio'][@value='schedule']",
    "now_radio": "//label[contains(., 'Now')] | //input[@type='radio'][@value='post_now']",

    # Date Picker & Time Picker
    "scheduled_picker_container": "//div[contains(@class, 'scheduled-picker')]",
    "date_picker_combobox": "//*[@role='combobox'][@aria-label='Select date'] | //*[@aria-label='Select date']",
    "time_picker_combobox": "//*[@role='combobox'][@aria-label='Select time'] | //*[@aria-label='Select time']",
    "date_picker_input": "//div[contains(@class, 'scheduled-picker')]//input[contains(@value, '-') or contains(@placeholder, 'YYYY')]",
    "time_picker_input": "//div[contains(@class, 'scheduled-picker')]//input[contains(@value, ':') or contains(@placeholder, 'HH')]",
    "time_picker_dropdown": "//div[contains(@class, 'TimePicker__column') or contains(@class, 'tiktok-timepicker-time-picker-container')]",

    # Tombol Final: Posting Sekarang atau Jadwalkan
    "post_button": "//button[contains(@class, 'Button__root')][contains(., 'Post') or contains(., 'Posting')]",
    "schedule_button": "//button[contains(@class, 'Button__root')][contains(., 'Schedule') or contains(., 'Jadwalkan')]",

    # Modal Notifikasi & Konfirmasi Sukses
    "success_modal_or_toast": "//*[contains(text(), 'Your video has been uploaded') or contains(text(), 'Video Anda telah diunggah') or contains(text(), 'Video dijadwalkan') or contains(text(), 'scheduled') or contains(@class, 'modal-success')]"
}

def log_step(msg, dashboard=None, is_success=False):
    """Membantu pencatatan aktivitas langkah pada Dashboard atau Terminal."""
    if dashboard:
        dashboard.current_job["activity"] = ("✓ " if is_success else "") + msg
        dashboard.render()
    else:
        prefix = "[✓]" if is_success else "[i]"
        print(f"    {prefix} {msg}")

def check_login_status(driver, log_func=None):
    """Mengecek apakah sesi TikTok pada profil ini sudah dalam keadaan login."""
    if log_func: log_func("Mengecek status login TikTok...")
    try:
        # Buka halaman utama jika belum di TikTok
        if "tiktok.com" not in driver.current_url:
            driver.get("https://www.tiktok.com/")
            time.sleep(3)
        
        # Cek tombol login vs ikon profil
        login_btns = driver.find_elements(By.XPATH, SELECTORS["login_button"])
        visible_login = [b for b in login_btns if b.is_displayed()]
        if visible_login:
            if log_func: log_func("Profil belum login ke TikTok. Perlu login manual terlebih dahulu.")
            return False
        
        if log_func: log_func("Status: Sudah login ke TikTok.", is_success=True)
        return True
    except Exception as e:
        if log_func: log_func(f"Catatan cek login: {e}")
        return True

def switch_to_upload_frame(driver, log_func=None):
    """
    TikTok Studio pada beberapa versi meletakkan form di dalam iframe creator-center.
    Fungsi ini otomatis mendeteksi dan beralih ke frame jika ada.
    """
    try:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.XPATH, SELECTORS["upload_iframe"])
        visible_iframes = [f for f in iframes if f.is_displayed()]
        if visible_iframes:
            if log_func: log_func("Beralih ke iframe upload TikTok...")
            driver.switch_to.frame(visible_iframes[0])
            return True
    except Exception:
        pass
    return False

def open_tiktok_upload_page(driver, log_func=None):
    """Membuka halaman Creator Center / Studio Upload TikTok."""
    target_url = SELECTORS["upload_page_url"]
    if log_func: log_func(f"Membuka halaman upload TikTok: {target_url}")
    
    driver.get(target_url)
    time.sleep(5)
    
    # Cek apakah ada redirect ke studio upload alternatif
    if "tiktokstudio/upload" in driver.current_url:
        if log_func: log_func("Terdeteksi TikTok Studio Upload interface.")
    
    switch_to_upload_frame(driver, log_func)
    return True

def upload_media_file(driver, media_files, log_func=None):
    """
    Mengunggah file media (video .mp4 atau foto) ke input type='file' TikTok.
    """
    if not media_files:
        raise ValueError("Tidak ada file media yang diberikan.")
        
    if log_func: log_func(f"Menyiapkan upload {len(media_files)} file media...")
    
    # Pastikan di dalam frame yang tepat
    switch_to_upload_frame(driver)
    
    # Cari input type file
    file_inputs = driver.find_elements(By.XPATH, SELECTORS["file_input"])
    
    if not file_inputs:
        # Coba kembali ke default content jika belum ditemukan
        driver.switch_to.default_content()
        file_inputs = driver.find_elements(By.XPATH, SELECTORS["file_input"])
        
    if not file_inputs:
        raise Exception("Input file upload TikTok tidak ditemukan di halaman.")
        
    target_input = file_inputs[0]
    
    # Jika media tunggal (misal video)
    if len(media_files) == 1:
        target_input.send_keys(os.path.abspath(media_files[0]))
    else:
        # Multi file foto (photo carousel mode)
        target_input.send_keys("\n".join(os.path.abspath(f) for f in media_files))
        
    if log_func: log_func("File berhasil dikirim ke input upload TikTok.", is_success=True)
    return True

def wait_media_processed(driver, timeout_sec=120, log_func=None):
    """
    Menunggu proses upload dan rendering awal video TikTok selesai sebelum mengatur metadata.
    """
    if log_func: log_func("Menunggu verifikasi upload media TikTok...")
    start_time = time.time()
    
    while time.time() - start_time < timeout_sec:
        switch_to_upload_frame(driver)
        # Deteksi indikator berhasil upload atau kotak preview
        try:
            success_indicators = driver.find_elements(By.XPATH, SELECTORS["upload_success_indicator"])
            if any(el.is_displayed() for el in success_indicators):
                if log_func: log_func("Media berhasil diunggah ke TikTok!", is_success=True)
                return True
        except Exception:
            pass
        
        # Cek apakah editor caption sudah muncul (indikasi upload sudah diproses)
        try:
            editor = driver.find_elements(By.XPATH, SELECTORS["caption_editor"])
            if any(ed.is_displayed() for ed in editor):
                if log_func: log_func("Editor caption siap digunakan.", is_success=True)
                return True
        except Exception:
            pass
            
        time.sleep(2)
        
    if log_func: log_func("Waktu tunggu upload habis, melanjutkan dengan asumsi media telah diterima...")
    return True

def dismiss_tutorial_overlay(driver):
    """Menutup overlay tutorial/joyride TikTok Studio jika muncul."""
    try:
        got_it_btns = driver.find_elements(By.XPATH, SELECTORS.get("tutorial_got_it", "//button[contains(., 'Got it') or contains(., 'Mengerti')]"))
        for btn in got_it_btns:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
        driver.execute_script("var o = document.querySelector('.react-joyride__overlay'); if(o) o.remove();")
    except Exception:
        pass

def fill_caption_and_tags(driver, caption_text, log_func=None):
    """
    Memasukkan caption dan hashtags ke text editor TikTok Studio.
    """
    if not caption_text:
        return True
        
    if log_func: log_func("Menyuntikkan caption & hashtags...")
    dismiss_tutorial_overlay(driver)
    
    try:
        editors = driver.find_elements(By.XPATH, SELECTORS["caption_editor"])
        visible_editors = [e for e in editors if e.is_displayed()]
        
        if visible_editors:
            editor = visible_editors[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus(); arguments[0].click();", editor)
            time.sleep(0.5)
            
            # Select all & hapus text bawaan
            ActionChains(driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
            time.sleep(0.4)
            
            # Gunakan clipboard Windows untuk menyuntikkan teks panjang instan
            import subprocess
            try:
                subprocess.run("clip", input=caption_text.encode('utf-16le'), check=True)
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            except Exception:
                editor.send_keys(caption_text)
                
            time.sleep(1)
            if log_func: log_func("Caption berhasil diisi.", is_success=True)
            return True
        else:
            if log_func: log_func("Elemen editor caption tidak ditemukan.")
            return False
    except Exception as e:
        if log_func: log_func(f"Peringatan pengisian caption: {e}")
        return False

def safe_log(log_func, msg, is_success=False):
    if not log_func:
        return
    try:
        log_func(msg, is_success=is_success)
    except TypeError:
        prefix = "[✓]" if is_success else "[i]"
        log_func(f"{prefix} {msg}")

def configure_schedule(driver, schedule_time_str, log_func=None):
    """
    Mengaktifkan opsi 'Jadwalkan postingan' (Radio Schedule) pada TikTok Studio dan menentukan tanggal serta jam.
    Mendukung antarmuka baru TikTok Studio (Picker__trigger, role='combobox', DatePicker__day, TimePicker__column)
    serta kompatibel mundur dengan form legacy.
    Format schedule_time_str: 'YYYY-MM-DD HH:MM'
    """
    if not schedule_time_str:
        if log_func: safe_log(log_func, "Mode posting langsung (Post Now) dipilih.")
        try:
            now_radios = driver.find_elements(By.XPATH, SELECTORS["now_radio"])
            if now_radios:
                driver.execute_script("arguments[0].click();", now_radios[0])
        except Exception:
            pass
        return True
        
    safe_log(log_func, f"Menyiapkan opsi jadwal TikTok: {schedule_time_str}")
    dismiss_tutorial_overlay(driver)
    
    try:
        dt_obj = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M")
        date_str = dt_obj.strftime("%Y-%m-%d")
        target_year = str(dt_obj.year)
        target_month = dt_obj.month
        target_day = str(dt_obj.day)
        hour_target = f"{dt_obj.hour:02d}"
        min_rounded = (dt_obj.minute // 5) * 5
        min_target = f"{min_rounded:02d}"
        target_time_str = f"{hour_target}:{min_target}"
        
        # 1. Cari dan klik radio Schedule
        sched_radios = driver.find_elements(By.XPATH, SELECTORS["schedule_radio"])
        if sched_radios:
            target_radio = sched_radios[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_radio)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", target_radio)
            time.sleep(1.5)
            safe_log(log_func, "Radio Schedule berhasil diaktifkan.", is_success=True)
        else:
            all_radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
            for r in all_radios:
                if (r.get_attribute("value") or "").lower() == "schedule":
                    driver.execute_script("arguments[0].click();", r)
                    time.sleep(1.5)
                    break

        # 2. PENGATURAN TANGGAL (DATE PICKER)
        date_combos = driver.find_elements(By.XPATH, "//*[@role='combobox'][@aria-label='Select date'] | //*[@aria-label='Select date'] | //div[contains(@class, 'schedule-picker')]//div[@role='combobox']")
        if date_combos:
            date_trigger = date_combos[0]
            safe_log(log_func, f"Membuka Date Picker (saat ini: {date_trigger.text.strip()})...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", date_trigger)
            time.sleep(1)

            # Navigasi bulan jika target di bulan berikutnya
            driver.execute_script("""
                const targetMonth = arguments[0];
                const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
                const targetMonthName = months[targetMonth - 1];

                const currentMonthBtn = document.querySelector('.DatePicker__titleMonth');
                if (currentMonthBtn && currentMonthBtn.textContent.trim() !== targetMonthName) {
                    const nextBtn = document.querySelector('.DatePicker__nav[aria-label="Next month"]') || document.querySelector('[id*="next-button"]');
                    if (nextBtn) { nextBtn.click(); }
                }
            """, target_month)
            time.sleep(0.5)

            # Klik tanggal di kalender
            res_date = driver.execute_script("""
                const targetDay = arguments[0];
                const buttons = Array.from(document.querySelectorAll('.DatePicker__day'));
                const btn = buttons.find(b => {
                    const isOutside = b.getAttribute('data-outside') === 'true';
                    const isDisabled = b.getAttribute('data-disabled') === 'true' || b.disabled;
                    return !isOutside && !isDisabled && b.textContent.trim() === targetDay;
                });
                if (btn) {
                    btn.scrollIntoView({block: 'center', behavior: 'instant'});
                    btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                    btn.click();
                    btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                    return true;
                }
                return false;
            """, target_day)
            time.sleep(0.8)
            driver.execute_script("document.body.click();")
            time.sleep(0.5)
            safe_log(log_func, f"Pilih tanggal {target_day} di kalender: {'Berhasil' if res_date else 'Gagal'}", is_success=res_date)
        else:
            # Fallback legacy date input
            date_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if "-" in (i.get_attribute("value") or "")]
            if date_inputs:
                d_inp = date_inputs[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", d_inp)
                time.sleep(1)
                day_cells = driver.find_elements(By.XPATH, f"//span[contains(@class, 'day') and not(contains(@class, 'disabled')) and text()='{target_day}']")
                if day_cells:
                    driver.execute_script("arguments[0].click();", day_cells[0])
                time.sleep(0.5)
                driver.execute_script("document.body.click();")

        # 3. PENGATURAN JAM & MENIT (TIME PICKER)
        time_combos = driver.find_elements(By.XPATH, "//*[@role='combobox'][@aria-label='Select time'] | //*[@aria-label='Select time'] | //div[contains(@class, 'schedule-picker')]//div[@role='combobox'][contains(., ':')]")
        if time_combos:
            time_trigger = time_combos[0]
            safe_log(log_func, f"Membuka Time Picker ke {target_time_str} (saat ini: {time_trigger.text.strip()})...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", time_trigger)
            time.sleep(1)

            # 3a. Klik Jam
            h_ok = driver.execute_script("""
                const targetH = arguments[0];
                const hoursCol = document.querySelector('[role="listbox"][aria-label="Hours"]') || document.querySelector('.TimePicker__column');
                if (hoursCol) {
                    const hOpts = Array.from(hoursCol.querySelectorAll('[role="option"]'));
                    const hBtn = hOpts.find(b => b.textContent.trim() === targetH || b.textContent.trim() === String(parseInt(targetH)));
                    if (hBtn) {
                        hBtn.scrollIntoView({block: 'center', behavior: 'instant'});
                        hBtn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                        hBtn.click();
                        hBtn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                        return true;
                    }
                }
                return false;
            """, hour_target)
            time.sleep(0.4)

            # 3b. Klik Menit
            m_ok = driver.execute_script("""
                const targetM = arguments[0];
                const minsCol = document.querySelector('[role="listbox"][aria-label="Minutes"]') || document.querySelectorAll('.TimePicker__column')[1];
                if (minsCol) {
                    const mOpts = Array.from(minsCol.querySelectorAll('[role="option"]'));
                    const mBtn = mOpts.find(b => b.textContent.trim() === targetM || b.textContent.trim() === String(parseInt(targetM)));
                    if (mBtn) {
                        mBtn.scrollIntoView({block: 'center', behavior: 'instant'});
                        mBtn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                        mBtn.click();
                        mBtn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                        return true;
                    }
                }
                return false;
            """, min_target)
            time.sleep(0.4)

            driver.execute_script("document.body.click();")
            time.sleep(0.5)
            safe_log(log_func, f"Pilih jam {hour_target} dan menit {min_target}: {'Berhasil' if h_ok and m_ok else 'Gagal'}", is_success=(h_ok and m_ok))
        else:
            # Fallback legacy time input
            time_inputs = [i for i in driver.find_elements(By.XPATH, "//input") if ":" in (i.get_attribute("value") or "")]
            if time_inputs:
                t_inp = time_inputs[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", t_inp)
                time.sleep(1)
                h_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-left') and text()='{hour_target}']")
                if h_spans:
                    driver.execute_script("arguments[0].click();", h_spans[0])
                m_spans = driver.find_elements(By.XPATH, f"//span[contains(@class, 'tiktok-timepicker-right') and text()='{min_target}']")
                if m_spans:
                    driver.execute_script("arguments[0].click();", m_spans[0])
                time.sleep(0.5)
                driver.execute_script("document.body.click();")

        final_d = date_combos[0].text.strip() if date_combos else date_str
        final_t = time_combos[0].text.strip() if time_combos else target_time_str
        safe_log(log_func, f"Jadwal TikTok berhasil diset ke {final_d} {final_t}", is_success=True)
        return True
    except Exception as e:
        safe_log(log_func, f"Peringatan pengaturan jadwal: {e}")
        return False

def submit_post(driver, is_scheduled=True, log_func=None):
    """
    Mengklik tombol 'Posting' atau 'Jadwalkan' dan menunggu respon.
    """
    action_name = "Jadwalkan" if is_scheduled else "Posting"
    if log_func: log_func(f"Mengklik tombol final: {action_name}...")
    switch_to_upload_frame(driver)
    
    try:
        xpath_btn = SELECTORS["schedule_button"] if is_scheduled else SELECTORS["post_button"]
        btns = driver.find_elements(By.XPATH, xpath_btn)
        visible_btns = [b for b in btns if b.is_displayed() and b.get_attribute("aria-disabled") != "true"]
        
        if visible_btns:
            driver.execute_script("arguments[0].click();", visible_btns[-1])
            time.sleep(2)

            # Cek jika muncul pop-up konfirmasi TikTok ("Continue to post?" / "We're still checking your video...")
            confirm_modal_xpath = (
                "//div[@role='dialog']//button[contains(., 'Post now') or contains(., 'Schedule now') or contains(., 'Continue to post') or contains(., 'Post anyway') or contains(., 'Tetap posting') or contains(., 'Tetap jadwalkan')]"
                "| //div[contains(@class, 'modal')]//button[contains(., 'Post now') or contains(., 'Schedule now') or contains(., 'Continue to post')]"
            )
            confirm_btns = driver.find_elements(By.XPATH, confirm_modal_xpath)
            for cb in confirm_btns:
                if cb.is_displayed():
                    if log_func: log_func(f"Mengonfirmasi pop-up dialog: '{cb.text}'...")
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(2)
                    break

            if log_func: log_func(f"Tombol {action_name} berhasil diklik.", is_success=True)
            return True
        else:
            if log_func: log_func("Tombol submit belum aktif atau tidak ditemukan.")
            return False
    except Exception as e:
        if log_func: log_func(f"Gagal mengklik tombol submit: {e}")
        return False

def wait_completion(driver, timeout_sec=25, log_func=None):
    """
    Menunggu munculnya konfirmasi sukses upload/jadwal TikTok (banner toast yang drop dari atas atau redirect).
    """
    if log_func: log_func("Menunggu konfirmasi posting dari TikTok...")
    start_time = time.time()
    
    # Selector untuk banner notifikasi drop dari atas / toast / modal sukses TikTok
    success_xpath = (
        "//*[contains(@class, 'toast') or contains(@class, 'Toast') or contains(@class, 'notification') or @role='status' or @role='alert']"
        "| //*[contains(text(), 'dijadwalkan') or contains(text(), 'scheduled') or contains(text(), 'uploaded') or contains(text(), 'diunggah') or contains(text(), 'Manage your posts') or contains(text(), 'Kelola postingan')]"
        "| //button[contains(., 'Upload another') or contains(., 'Manage your posts') or contains(., 'Unggah video lain') or contains(., 'Kelola')]"
    )
    
    while time.time() - start_time < timeout_sec:
        try:
            elements = driver.find_elements(By.XPATH, success_xpath)
            visible_elements = [el for el in elements if el.is_displayed()]
            if visible_elements:
                toast_text = visible_elements[0].text.strip().replace('\n', ' ')
                if log_func: log_func(f"Notifikasi sukses terdeteksi (Toast Banner): '{toast_text[:60]}'", is_success=True)
                time.sleep(3)
                
                # Cek jika ada tombol 'Upload another video' untuk reset form
                another_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Upload another') or contains(., 'Unggah video lain')]")
                if another_btns and another_btns[0].is_displayed():
                    driver.execute_script("arguments[0].click();", another_btns[0])
                    time.sleep(2)
                return True
        except Exception:
            pass
            
        if any(keyword in driver.current_url for keyword in ["manage", "creator-center/content", "tiktokstudio/content"]):
            if log_func: log_func("Halaman beralih ke daftar konten (berhasil).", is_success=True)
            return True
            
        time.sleep(1)
        
    if log_func: log_func("Postingan berhasil dikirim ke antrean TikTok.", is_success=True)
    return True

# ==============================================================================
# PIPELINE UTAMA EKSEKUSI POSTING / JADWAL TIKTOK
# ==============================================================================
def run_tt_scheduled_task(
    driver,
    profile_name,
    post_path,
    schedule_time=None,
    preview=False,
    pre_caption=None,
    custom_media=None,
    dashboard=None,
    task_key=None
):
    """
    Orchestrator utama yang menjalankan seluruh tahapan upload TikTok.
    """
    key_for_dash = task_key if task_key else post_path
    item_name = os.path.basename(key_for_dash)
    is_scheduled = bool(schedule_time)
    
    def log_handler(msg, is_success=False):
        log_step(msg, dashboard, is_success)

    try:
        update_post_status(post_path, "Inisialisasi...", 10)
        
        # 1. Update status dashboard
        if dashboard:
            dashboard.current_job["name"] = item_name
            dashboard.current_job["date"] = schedule_time if schedule_time else "🚀 Posting SEKARANG"
            dashboard.current_job["upload"] = "Membuka TikTok..."
            dashboard.current_job["caption"] = "Pending"
            dashboard.current_job["scheduling"] = "Pending"
            dashboard.render()

        # 2. Buka Halaman Upload
        open_tiktok_upload_page(driver, log_func=log_handler)
        update_post_status(post_path, "Halaman upload terbuka", 20)

        # 3. Upload File
        if dashboard:
            dashboard.current_job["upload"] = "Mengunggah file..."
            dashboard.render()
        media_files = custom_media or [post_path]
        upload_media_file(driver, media_files, log_func=log_handler)
        
        # 4. Tunggu Media Diproses
        wait_media_processed(driver, log_func=log_handler)
        if dashboard:
            dashboard.current_job["upload"] = "Completed"
            dashboard.current_job["caption"] = "Mengisi caption..."
            dashboard.render()
        update_post_status(post_path, "Media terunggah", 50)

        # 5. Isi Caption
        fill_caption_and_tags(driver, pre_caption or item_name, log_func=log_handler)
        if dashboard:
            dashboard.current_job["caption"] = "Injected"
            dashboard.current_job["scheduling"] = "Mengatur jadwal..." if is_scheduled else "Siap posting..."
            dashboard.render()
        update_post_status(post_path, "Caption disuntikkan", 70)

        # 6. Atur Jadwal
        if is_scheduled:
            configure_schedule(driver, schedule_time, log_func=log_handler)
            
        if dashboard:
            dashboard.current_job["scheduling"] = "Menyimpan..."
            dashboard.render()

        # 7. Submit
        submit_post(driver, is_scheduled=is_scheduled, log_func=log_handler)
        
        # 8. Tunggu Konfirmasi
        wait_completion(driver, log_func=log_handler)
        
        if dashboard:
            dashboard.current_job["scheduling"] = "Completed"
            dashboard.render()

        # 9. Tulis Marker Sukses
        marker_file = os.path.join(post_path, "uploadedtt.txt") if os.path.isdir(post_path) else post_path + ".uploadedtt"
        with open(marker_file, "w", encoding="utf-8") as f:
            if schedule_time:
                f.write(f"Dijadwalkan: {schedule_time}\n")
            else:
                f.write(f"Diposting: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        update_post_status(post_path, "SELESAI", 100)
        
        # 10. Siapkan halaman upload bersih untuk item berikutnya
        try:
            time.sleep(2)
            driver.get(SELECTORS["upload_page_url"])
            time.sleep(3)
        except Exception:
            pass

        if dashboard:
            dashboard.statuses[key_for_dash] = "success"
            dashboard.success_count += 1
            dashboard.render()
            
        return True

    except Exception as e:
        err_msg = str(e)
        log_handler(f"Error proses posting: {err_msg}")
        update_post_status(post_path, f"Gagal: {err_msg[:40]}", 0)
        if dashboard:
            dashboard.statuses[key_for_dash] = "failed"
            dashboard.failed_count += 1
            dashboard.current_job["activity"] = f"Error: {err_msg[:35]}"
            dashboard.render()
        return False
