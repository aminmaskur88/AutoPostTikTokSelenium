# 🎵 AutoPostTT - TikTok Scheduled Auto-Poster

Sistem otomatisasi unggah dan penjadwalan konten TikTok berbasis Selenium Stealth, terinspirasi dari arsitektur teruji `fb_uploader_scheduled.py`.

---

## 🌟 Fitur Utama (Versi Base)
1. **Interactive CLI & Menu Keyboard**: Navigasi menggunakan tombol panah keyboard `[↑/↓]`, angka, dan styling warna ANSI.
2. **Web Pratinjau & Editor Interaktif**: Local server web bawaan (SortableJS) untuk melihat thumbnail video/foto, edit caption & hashtags langsung, ubah urutan postingan, lalu tombol eksekusi upload.
3. **Live ASCII Terminal Dashboard**: Tampilan status real-time saat upload berjalan (progress bar, status upload, caption, scheduling, dan aktivitas).
4. **Sistem Profil Terisolasi (`tt_profiles/`)**: Sesi login TikTok disimpan secara permanen di profil Chrome terpisah sehingga tidak perlu login berulang kali.
5. **Proteksi Penjadwalan Khusus TikTok**:
   - Membatasi jadwal maksimal **10 hari** ke depan (kebijakan TikTok Studio).
   - Menyesuaikan pembulatan menit ke kelipatan 5 menit.
6. **Arsitektur Eksekutor Modular (`tt_executor.py`)**:
   - Fungsi interaksi DOM dipisahkan dalam kamus selektor `SELECTORS` terpusat, siap diperbarui dari hasil inspeksi / perekaman via **Chrome DevTools MCP**.

---

## 📁 Struktur Direktori

```text
AutoPostTT/
├── core/
│   ├── __init__.py
│   ├── utils.py                   # Setup Selenium Chrome Stealth & Profile Manager
│   ├── tt_login.py                # Helper praktis login profil TikTok
│   ├── tt_executor.py             # Modular DOM executor & SELECTORS repository
│   └── tt_uploader_scheduled.py   # Script utama (CLI, Web Preview, Scheduler Engine)
├── tt_profiles/                   # Direktori User Data profil Chrome (auto-generated)
├── draft_posts_tt.json            # Penyimpanan draf lokal
└── README.md
```

---

## 🚀 Panduan Penggunaan

### 1. Login Pertama Kali (Menyiapkan Profil)
Jalankan helper login untuk menyimpan sesi akun TikTok Anda:
```powershell
python "C:\Users\aminm\AutoPostTT\core\tt_login.py"
```
- Pilih **Tambah Profil Baru** (misal: `AkunUtama`).
- Browser Chrome akan terbuka menuju `https://www.tiktok.com/login`.
- Masuk ke akun TikTok Anda.
- Setelah berhasil login, kembali ke terminal dan tekan **[ENTER]**. Sesi akan tersimpan permanen di `tt_profiles/AkunUtama/`.

### 2. Menjalankan Auto-Poster Interaktif
```powershell
python "C:\Users\aminm\AutoPostTT\core\tt_uploader_scheduled.py"
```
Menu interaktif akan memandu Anda:
1. Memilih profil TikTok yang sudah login.
2. Memasukkan path folder berisi video/foto.
3. Memilih strategi penjadwalan (interval jam, hari, manual, atau post now).
4. Memilih mode pratinjau Web (bisa drag-and-drop urutan dan edit caption).
5. Eksekusi upload dengan Live Dashboard terminal.

### 3. Menjalankan via Argumen CLI (Non-Interaktif)
```powershell
python "C:\Users\aminm\AutoPostTT\core\tt_uploader_scheduled.py" --profile AkunUtama --path "D:\KontenTikTok" --mode 1 --interval 60 --start "2026-10-22 10:00"
```

---

## 🛠️ Perekaman & Penyempurnaan Selektor via Chrome MCP

Kamus selektor di [`core/tt_executor.py`](file:///C:/Users/aminm/AutoPostTT/core/tt_executor.py) dirancang modular:
```python
SELECTORS = {
    "upload_page_url": "https://www.tiktok.com/creator-center/upload?from=upload",
    "file_input": "//input[@type='file']",
    "caption_editor": "//div[@contenteditable='true']",
    "schedule_switch": "...",
    "date_picker_input": "...",
    "time_picker_input": "...",
    "schedule_button": "..."
}
```
Ketika melakukan inspeksi menggunakan Chrome DevTools MCP, selektor yang ditemukan di TikTok Studio cukup dimasukkan ke dalam dictionary `SELECTORS` tersebut tanpa perlu mengubah logika otomasi lainnya.
