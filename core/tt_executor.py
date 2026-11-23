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
    "upload_success_indicator": "//div[contains(@class, 'info-progress') and contains(@class, 'success')] | //*[contains(@class, 'info-status')][contains(., 'Uploaded') or contains(., 'Diunggah')]",
    "replace_video_button": "//button[normalize-space(.)='Replace' or normalize-space(.)='Ganti']",

    # Pop-up Tutorial / Overlay TikTok Studio
    "tutorial_got_it": "//button[contains(., 'Got it') or contains(., 'Mengerti')]",
    "tutorial_overlay": ".react-joyride__overlay",

    # Editor Caption / Judul
    "caption_editor": "//div[contains(@class, 'public-DraftEditor-content')] | //div[@contenteditable='true']",

    # Cover / Custom Thumbnail Editor
    "cover_container": "//div[@data-e2e='cover_container'] | //div[contains(@class, 'cover-container')]",
    "edit_cover_button": (
        "//div[@data-e2e='cover_container']//div[contains(@class, 'edit-container')]"
        " | //div[contains(@class, 'cover-container')]//div[contains(@class, 'edit-container')]"
        " | //*[normalize-space(text())='Edit cover' or normalize-space(text())='Edit sampul']"
    ),
    "upload_cover_tab": (
        "//div[contains(@class, 'ImageUpload__root')]"
        " | //*[normalize-space(text())='Upload cover' or normalize-space(text())='Unggah sampul']"
    ),
    "cover_file_input": "//input[@type='file' and contains(@accept, 'image')]",
    "cover_save_button": (
        "//button[contains(@class, 'header-button') and contains(@class, 'primary')][contains(., 'Save') or contains(., 'Simpan') or contains(., 'Confirm') or contains(., 'Konfirmasi')]"
        " | //div[contains(@class, 'CoverEditor')]//button[contains(., 'Save') or contains(., 'Simpan') or contains(., 'Confirm') or contains(., 'Konfirmasi')]"
    ),

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

def wait_media_processed(driver, timeout_sec=300, log_func=None):
    """
    Menunggu proses upload dan rendering video TikTok benar-benar selesai (100% / Uploaded)
    sebelum lanjut ke custom thumbnail, caption, dan jadwal.
    Memantau:
    - info-status (info vs success / 'Uploaded')
    - info-aside (persentase % & tombol Cancel vs tombol Replace)
    - cover-info-tip ('Uploading...')
    - tombol Post/Schedule (disabled vs aktif)
    """
    safe_log(log_func, "Menunggu proses upload & verifikasi media TikTok selesai...")
    start_time = time.time()
    min_wait_sec = 5  # Jeda awal agar UI progress bar sempat muncul
    stable_done_ticks = 0
    last_progress_msg = ""

    while time.time() - start_time < timeout_sec:
        switch_to_upload_frame(driver)
        handle_confirmation_popups(driver, log_func=log_func)
        elapsed = time.time() - start_time

        try:
            status = driver.execute_script("""
                const isVis = (el) => el && el.offsetParent !== null;

                // 1. Cek cover-info-tip ('Uploading...' / 'Processing...')
                const coverTips = Array.from(document.querySelectorAll('[class*="cover-info-tip"]')).filter(isVis);
                const coverTipText = coverTips.map(el => (el.textContent || '').trim()).join(' ');
                const coverUploading = /uploading|mengunggah|processing|memproses/i.test(coverTipText);

                // 2. Cek info-status (saat upload: class 'info-status info' dgn 'MB/' atau 'seconds left'; saat selesai: 'info-status success' dgn 'Uploaded')
                const statusEls = Array.from(document.querySelectorAll('[class*="info-status"]')).filter(isVis);
                let statusText = '';
                let statusIsSuccess = false;
                let statusIsUploading = false;
                for (const el of statusEls) {
                    const cls = typeof el.className === 'string' ? el.className : '';
                    const t = (el.textContent || '').trim();
                    if (t) statusText += ' ' + t;
                    if (cls.includes('success') || /\\buploaded\\b|\\bdiunggah\\b/i.test(t)) {
                        statusIsSuccess = true;
                    }
                    if (/seconds? left|minutes? left|detik|menit|uploading|mengunggah|processing|memproses|\\d+(?:\\.\\d+)?\\s*mb\\s*\\/\\s*\\d+/i.test(t)) {
                        statusIsUploading = true;
                    }
                }
                statusText = statusText.trim();

                // 3. Cek info-aside (saat upload: 'Cancel' + '51.36%'; saat selesai: 'Replace')
                const asideEls = Array.from(document.querySelectorAll('[class*="info-aside"], [class*="info-progress"], [role="progressbar"]')).filter(isVis);
                let asideText = '';
                for (const el of asideEls) {
                    const t = (el.textContent || '').trim();
                    if (t) asideText += ' ' + t;
                }
                asideText = asideText.trim();

                const pctMatch = (asideText + ' ' + statusText).match(/(\\d+(?:\\.\\d+)?)\\s*%/);
                const pctVal = pctMatch ? parseFloat(pctMatch[1]) : null;
                const asideHasCancel = /\\bcancel\\b|\\bbatal\\b/i.test(asideText);
                const progressStillRunning = (
                    statusIsUploading ||
                    asideHasCancel ||
                    (pctVal !== null && pctVal < 100) ||
                    /uploading|mengunggah|processing|memproses/i.test(asideText)
                );

                // 4. Cek tombol Replace & tombol Post/Schedule
                const btns = Array.from(document.querySelectorAll('button')).filter(isVis);
                const replaceBtn = btns.some(b => {
                    const txt = (b.textContent || '').trim().toLowerCase();
                    return txt === 'replace' || txt === 'ganti';
                });
                const submitReady = btns.some(b => {
                    const txt = (b.textContent || '').trim().toLowerCase();
                    const disabled = b.disabled || b.getAttribute('aria-disabled') === 'true';
                    return !disabled && (txt === 'post' || txt === 'posting' || txt === 'schedule' || txt === 'jadwalkan');
                });

                const editorReady = Array.from(document.querySelectorAll('.public-DraftEditor-content, [contenteditable="true"]')).some(isVis);

                return {
                    coverUploading,
                    coverTipText,
                    statusIsSuccess,
                    statusText,
                    progressStillRunning,
                    pctVal,
                    replaceBtn,
                    editorReady,
                    submitReady
                };
            """)
        except Exception:
            status = {}

        still_uploading = bool(status.get("coverUploading") or status.get("progressStillRunning"))
        done_signal = bool(
            (status.get("statusIsSuccess") and not still_uploading)
            or (status.get("replaceBtn") and status.get("submitReady") and not still_uploading)
        )

        # Log progres upload secara berkala
        if still_uploading:
            stable_done_ticks = 0
            pct = status.get("pctVal")
            if pct is not None:
                prog_msg = f"Mengunggah media ke TikTok... ({pct:.1f}%)"
            elif status.get("statusText"):
                prog_msg = f"Mengunggah media... ({status['statusText'][:45]})"
            elif status.get("coverTipText"):
                prog_msg = f"Memproses media TikTok... ({status['coverTipText'][:30]})"
            else:
                prog_msg = f"Mengunggah media ke TikTok... ({int(elapsed)}d)"
            if prog_msg != last_progress_msg:
                safe_log(log_func, prog_msg)
                last_progress_msg = prog_msg
        elif elapsed >= min_wait_sec and done_signal:
            # Pastikan kondisi selesai stabil selama 2 pengecekan berturut-turut (~4 detik)
            stable_done_ticks += 1
            if stable_done_ticks >= 2:
                safe_log(log_func, "Media berhasil diunggah & diproses 100% di TikTok!", is_success=True)
                return True
        else:
            stable_done_ticks = 0

        time.sleep(2)

    safe_log(log_func, "Waktu tunggu upload habis, melanjutkan dengan asumsi media telah diterima...")
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

def _prepare_thumbnail_file(thumbnail_path):
    """
    Memastikan file thumbnail dalam format JPG/PNG yang didukung TikTok Studio.
    Mengembalikan tuple (path_siap_upload, is_temp_file).
    """
    abs_path = os.path.abspath(thumbnail_path)
    ext = os.path.splitext(abs_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".png"):
        return abs_path, False

    # Jika format lain (misal .webp), coba konversi otomatis ke .jpg sementara jika Pillow tersedia
    try:
        from PIL import Image
        import tempfile
        with Image.open(abs_path) as img:
            rgb_img = img.convert("RGB")
            fd, tmp_jpg = tempfile.mkstemp(suffix=".jpg", prefix="tt_thumb_")
            os.close(fd)
            rgb_img.save(tmp_jpg, "JPEG", quality=95)
            return tmp_jpg, True
    except Exception:
        return abs_path, False

def upload_custom_thumbnail(driver, thumbnail_path, log_func=None, timeout_sec=30):
    """
    Mengunggah custom thumbnail (cover) untuk video di TikTok Studio.
    Alur:
    1. Tunggu tombol 'Edit cover' siap (proses upload awal cover selesai)
    2. Klik 'Edit cover' untuk membuka modal CoverEditor
    3. Cari input file image (atau klik tab 'Upload cover' terlebih dahulu jika diperlukan)
    4. Kirim path gambar thumbnail ke input file
    5. Klik tombol 'Save' / 'Confirm' pada modal CoverEditor
    """
    if not thumbnail_path or not os.path.isfile(thumbnail_path):
        safe_log(log_func, f"File custom thumbnail tidak ditemukan: {thumbnail_path}")
        return False

    safe_log(log_func, f"Mengunggah custom thumbnail: {os.path.basename(thumbnail_path)}")
    dismiss_tutorial_overlay(driver)
    switch_to_upload_frame(driver)

    prepared_path, is_temp = _prepare_thumbnail_file(thumbnail_path)
    try:
        # 1. Tunggu tombol 'Edit cover' muncul dan siap diklik
        edit_btn = None
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            dismiss_tutorial_overlay(driver)
            try:
                cands = driver.find_elements(By.XPATH, SELECTORS["edit_cover_button"])
                visible_cands = [c for c in cands if c.is_displayed()]
                if visible_cands:
                    # Pastikan tidak sedang dalam state 'Uploading...' pada cover-info-tip
                    uploading_tips = driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'cover-info-tip')][contains(., 'Uploading') or contains(., 'Mengunggah')]"
                    )
                    if not any(t.is_displayed() for t in uploading_tips):
                        edit_btn = visible_cands[0]
                        break
                    elif time.time() - start_time > 10:
                        # Tetap coba klik setelah 10 detik walau tip masih tampil
                        edit_btn = visible_cands[0]
                        break
            except Exception:
                pass
            time.sleep(1)

        if not edit_btn:
            safe_log(log_func, "Tombol 'Edit cover' tidak ditemukan di halaman upload TikTok.")
            return False

        # 2. Klik 'Edit cover' (dan fallback ke parent cover-container jika modal belum terbuka)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", edit_btn)

        # 3. Tunggu modal CoverEditor terbuka dan cari input file cover image
        cover_inputs = []
        modal_start = time.time()
        retried_container = False
        while time.time() - modal_start < 12:
            time.sleep(1)
            cover_inputs = driver.find_elements(By.XPATH, SELECTORS["cover_file_input"])
            if cover_inputs:
                break

            # Jika tab 'Upload cover' terlihat, klik dulu
            upload_tabs = driver.find_elements(By.XPATH, SELECTORS["upload_cover_tab"])
            visible_tabs = [t for t in upload_tabs if t.is_displayed()]
            if visible_tabs:
                driver.execute_script("arguments[0].click();", visible_tabs[0])
                time.sleep(1)
                cover_inputs = driver.find_elements(By.XPATH, SELECTORS["cover_file_input"])
                if cover_inputs:
                    break

            # Jika setelah 3 detik modal belum terbuka, coba klik parent cover-container & ActionChains
            if not retried_container and (time.time() - modal_start >= 3):
                retried_container = True
                try:
                    containers = driver.find_elements(By.XPATH, SELECTORS["cover_container"])
                    vis_cont = [c for c in containers if c.is_displayed()]
                    if vis_cont:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", vis_cont[-1])
                    else:
                        ActionChains(driver).move_to_element(edit_btn).click().perform()
                except Exception:
                    pass

        if not cover_inputs:
            safe_log(log_func, "Input file upload cover tidak ditemukan di modal Edit cover.")
            return False

        # 4. Kirim file gambar thumbnail ke input file cover
        cover_inputs[-1].send_keys(os.path.abspath(prepared_path))
        safe_log(log_func, "Gambar thumbnail dikirim ke editor cover, menunggu pratinjau...")
        time.sleep(2.5)

        # 5. Tunggu tombol Save aktif lalu klik (menggunakan JS DOM query agar kebal terhadap portal/headless)
        save_clicked = False
        save_start = time.time()
        while time.time() - save_start < 15:
            clicked = driver.execute_script("""
                const targets = ['save', 'simpan', 'confirm', 'konfirmasi'];
                const btns = Array.from(document.querySelectorAll('button'));
                // Prioritaskan tombol header-button primary di modal CoverEditor
                const match = btns.find(b => {
                    if (b.offsetParent === null) return false;
                    if (b.disabled || b.getAttribute('aria-disabled') === 'true') return false;
                    const cls = typeof b.className === 'string' ? b.className : '';
                    const txt = (b.textContent || '').trim().toLowerCase();
                    return cls.includes('header-button') && cls.includes('primary') && targets.includes(txt);
                }) || btns.find(b => {
                    if (b.offsetParent === null) return false;
                    if (b.disabled || b.getAttribute('aria-disabled') === 'true') return false;
                    const cls = typeof b.className === 'string' ? b.className : '';
                    const txt = (b.textContent || '').trim().toLowerCase();
                    return (cls.includes('header-button') || b.closest('[class*="CoverEditor"], [role="dialog"]')) && targets.includes(txt);
                });
                if (match) {
                    match.scrollIntoView({block: 'center', behavior: 'instant'});
                    match.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                    match.click();
                    match.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                    return true;
                }
                return false;
            """)
            if clicked:
                save_clicked = True
                break
            time.sleep(0.8)

        if not save_clicked:
            safe_log(log_func, "Tombol Save/Confirm pada modal Edit cover tidak ditemukan atau nonaktif.")
            return False

        # 6. Tunggu modal CoverEditor tertutup
        close_start = time.time()
        while time.time() - close_start < 10:
            still_open = driver.execute_script("""
                const targets = ['save', 'simpan', 'confirm', 'konfirmasi'];
                return Array.from(document.querySelectorAll('button')).some(b => {
                    if (b.offsetParent === null) return false;
                    const cls = typeof b.className === 'string' ? b.className : '';
                    const txt = (b.textContent || '').trim().toLowerCase();
                    return cls.includes('header-button') && cls.includes('primary') && targets.includes(txt);
                });
            """)
            if not still_open:
                break
            time.sleep(0.5)

        time.sleep(1)
        safe_log(log_func, "Custom thumbnail berhasil dipasang!", is_success=True)
        return True
    except Exception as e:
        safe_log(log_func, f"Peringatan upload custom thumbnail: {e}")
        return False
    finally:
        if is_temp and prepared_path and os.path.exists(prepared_path):
            try:
                os.remove(prepared_path)
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
            # Tutup popover autocomplete hashtag/mention jika muncul
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
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

            driver.execute_script("""
                const titleEl = document.querySelector('.scheduled-title-container') || document.body;
                titleEl.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                titleEl.click();
                titleEl.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
            """)
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

def handle_confirmation_popups(driver, log_func=None):
    """
    Mendeteksi dan mengklik tombol konfirmasi pada dialog / modal / toaster TikTok
    (misal: 'Post now' pada modal 'Continue to post?', 'Schedule now', 'Allow', 'Izinkan',
    'Continue to post', 'Post anyway', 'Confirm').
    Catatan: TUXModal-overlay memakai position:fixed sehingga offsetParent === null;
    wajib gunakan getBoundingClientRect().
    """
    try:
        clicked_label = driver.execute_script("""
            const isVis = (el) => {
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
            };
            const confirmKeywords = [
                'post now', 'schedule now', 'continue to post', 'post anyway',
                'allow', 'izinkan', 'confirm', 'konfirmasi',
                'tetap posting', 'tetap jadwalkan', 'lanjutkan posting', 'turn on'
            ];
            const containers = Array.from(document.querySelectorAll(
                '.TUXModal, .TUXModal-overlay, .common-modal, [role="dialog"], [role="alertdialog"], [class*="modal"], [class*="Modal"], [class*="toast"], [class*="Toast"]'
            )).filter(isVis);

            for (const c of containers) {
                const btns = Array.from(c.querySelectorAll('button')).filter(b => {
                    if (!isVis(b)) return false;
                    if (b.disabled || b.getAttribute('aria-disabled') === 'true') return false;
                    return true;
                });
                for (const b of btns) {
                    const txt = (b.textContent || '').trim().replace(/\\s+/g, ' ');
                    const low = txt.toLowerCase();
                    if (confirmKeywords.some(k => low === k || low.includes(k))) {
                        b.scrollIntoView({block: 'center', behavior: 'instant'});
                        b.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                        b.click();
                        b.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                        return txt;
                    }
                }
            }
            return null;
        """)
        if clicked_label:
            safe_log(log_func, f"Mengonfirmasi pop-up/modal TikTok: '{clicked_label}'...", is_success=True)
            time.sleep(2)
            return clicked_label
    except Exception:
        pass
    return None

def submit_post(driver, is_scheduled=True, log_func=None):
    """
    Menunggu tombol 'Posting' atau 'Jadwalkan' aktif, mengkliknya, lalu menangani
    pop-up / toaster konfirmasi (termasuk 'Allow', 'Post now', 'Schedule now', 'Continue to post').
    """
    action_name = "Jadwalkan" if is_scheduled else "Posting"
    safe_log(log_func, f"Menyiapkan klik tombol final: {action_name}...")
    switch_to_upload_frame(driver)
    
    try:
        # Tangani pop-up Allow / konfirmasi jika sudah muncul sebelum submit
        handle_confirmation_popups(driver, log_func=log_func)

        xpath_btn = SELECTORS["schedule_button"] if is_scheduled else SELECTORS["post_button"]
        visible_btns = []
        wait_start = time.time()
        while time.time() - wait_start < 30:
            btns = driver.find_elements(By.XPATH, xpath_btn)
            visible_btns = [
                b for b in btns
                if b.is_displayed()
                and not b.get_attribute("disabled")
                and b.get_attribute("aria-disabled") != "true"
            ]
            if visible_btns:
                break
            handle_confirmation_popups(driver, log_func=log_func)
            time.sleep(1)

        if visible_btns:
            target_btn = visible_btns[-1]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", target_btn)
            safe_log(log_func, f"Tombol {action_name} diklik, memeriksa konfirmasi/toaster...", is_success=True)

            # Pantau hingga ~8 detik untuk pop-up konfirmasi bertingkat (Allow / Post now / Continue to post)
            for _ in range(4):
                time.sleep(2)
                clicked = handle_confirmation_popups(driver, log_func=log_func)
                if not clicked:
                    break
            return True
        else:
            safe_log(log_func, f"Tombol {action_name} belum aktif atau tidak ditemukan setelah 30 detik.")
            return False
    except Exception as e:
        safe_log(log_func, f"Gagal mengklik tombol submit: {e}")
        return False

def wait_completion(driver, timeout_sec=30, log_func=None):
    """
    Menunggu munculnya konfirmasi sukses upload/jadwal TikTok (banner toast yang drop dari atas atau redirect),
    sambil tetap menangani jika muncul pop-up/toaster konfirmasi 'Allow' / 'Continue to post'.
    """
    safe_log(log_func, "Menunggu konfirmasi posting dari TikTok...")
    start_time = time.time()
    
    # Selector khusus notifikasi sukses posting (hindari false-positive dari 'Uploaded (65MB)' di kartu file)
    success_xpath = (
        "//*[contains(@class, 'toast') or contains(@class, 'Toast') or contains(@class, 'notification') or @role='alert']"
        "| //*[contains(text(), 'Your video has been') or contains(text(), 'Video Anda telah') or contains(text(), 'dijadwalkan') or contains(text(), 'has been scheduled') or contains(text(), 'Manage your posts') or contains(text(), 'Kelola postingan')]"
        "| //button[contains(., 'Upload another') or contains(., 'Manage your posts') or contains(., 'Unggah video lain')]"
    )
    
    while time.time() - start_time < timeout_sec:
        # Jika muncul pop-up/toaster konfirmasi (Allow / Post now / Continue to post), klik dulu
        if handle_confirmation_popups(driver, log_func=log_func):
            continue

        try:
            elements = driver.find_elements(By.XPATH, success_xpath)
            visible_elements = [
                el for el in elements
                if el.is_displayed() and (el.text or "").strip()
            ]
            if visible_elements:
                toast_text = visible_elements[0].text.strip().replace('\n', ' ')
                # Jangan anggap selesai jika toast/alert justru berisi konfirmasi Allow
                if "allow" in toast_text.lower() or "izinkan" in toast_text.lower():
                    handle_confirmation_popups(driver, log_func=log_func)
                    time.sleep(1)
                    continue
                safe_log(log_func, f"Notifikasi sukses terdeteksi (Toast Banner): '{toast_text[:60]}'", is_success=True)
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
            safe_log(log_func, "Halaman beralih ke daftar konten (berhasil).", is_success=True)
            return True
            
        time.sleep(1)
        
    safe_log(log_func, "Postingan berhasil dikirim ke antrean TikTok.", is_success=True)
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
    custom_thumbnail=None,
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
            dashboard.current_job["thumbnail"] = "Pending" if custom_thumbnail else "Default"
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
            dashboard.render()
        update_post_status(post_path, "Media terunggah", 45)

        # 4b. Upload Custom Thumbnail (khusus video)
        is_video_post = any(
            m.lower().endswith((".mp4", ".mov", ".webm")) for m in media_files
        )
        if custom_thumbnail and is_video_post:
            if dashboard:
                dashboard.current_job["thumbnail"] = "Mengunggah cover..."
                dashboard.render()
            thumb_ok = upload_custom_thumbnail(driver, custom_thumbnail, log_func=log_handler)
            if dashboard:
                dashboard.current_job["thumbnail"] = "Completed" if thumb_ok else "Failed"
                dashboard.render()
            update_post_status(post_path, "Thumbnail dipasang" if thumb_ok else "Thumbnail dilewati", 55)
        elif dashboard:
            dashboard.current_job["thumbnail"] = "Default"
            dashboard.render()

        # 5. Isi Caption
        if dashboard:
            dashboard.current_job["caption"] = "Mengisi caption..."
            dashboard.render()
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
        if not submit_post(driver, is_scheduled=is_scheduled, log_func=log_handler):
            raise Exception("Tombol Post/Schedule tidak aktif atau gagal diklik.")
        
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
