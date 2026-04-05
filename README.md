# 🎥 TikTok Automation Suite (Cross-Platform)

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.9.1-green.svg?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Windows%20%7C%20Mac%20%7C%20Linux-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sebuah koleksi skrip otomasi profesional untuk **TikTok Web** yang dirancang untuk berjalan di berbagai platform: **Android (Termux)** menggunakan X11 Forwarding/VNC, maupun **PC Desktop (Windows/Mac/Linux)** secara langsung. Proyek ini memungkinkan Anda melakukan manajemen konten TikTok secara otomatis dengan teknik yang sulit terdeteksi (anti-bot).

---

## ✨ Fitur Utama

- 🌐 **Cross-Platform:** Otomatis mendeteksi environment (Termux vs PC Desktop) dan menyesuaikan konfigurasi ChromeDriver secara cerdas.
- 🛡️ **Advanced Anti-Bot:** Menghilangkan jejak `navigator.webdriver` dan menggunakan `User-Agent` yang konsisten.
- 🍪 **Persistent Session:** Sesi login (cookies, cache, localStorage) tersimpan aman di direktori profil, menghindari login berulang.
- 📦 **Bulk Uploader (Video Only):** Mengunggah video `.mp4` secara berurutan. Otomatis melewati folder yang berisi foto.
- 🧩 **Manual Captcha Solver:** Skrip otomatis mendeteksi Captcha, menjeda proses, dan menunggu Anda menyelesaikannya (via VNC atau langsung di layar PC) sebelum melanjutkan.
- ⌨️ **Human-like Interaction:**
  - **Smart Warmup:** Simulasi tonton video dengan navigasi menu samping (For You, Explore, dll) dan tombol `Arrow Down` agar menyerupai perilaku manusia.
  - Pengetikan teks menggunakan metode fisik (`Ctrl+V`) untuk stabilitas editor React.
- 🛠️ **Smart Logic:** Menangani popup hak cipta, konfirmasi "Post now", dan verifikasi status upload.
- ⏳ **Visual Countdown:** Hitung mundur interaktif yang terlihat bergerak di terminal saat jeda antar postingan.
- 🔍 **Ultimate XPath Helper:** Skrip pembantu untuk mengambil XPath elemen apa pun secara klik-langsung.

---

## 🛠️ Persiapan Lingkungan

### Opsi A: Pengguna Termux (Android)
Jika Anda menggunakan HP Android:
1. **Update & Install Dependencies:**
   ```bash
   pkg update && pkg upgrade
   pkg install x11-repo
   pkg install chromium chromedriver tigervnc fluxbox
   ```
2. **Nyalakan VNC Server:**
   ```bash
   vncserver -localhost :1 -geometry 1280x720
   export DISPLAY=:1
   ```
   *(Hubungkan VNC Viewer di HP ke `127.0.0.1:5901`)*

### Opsi B: Pengguna PC Desktop (Windows / Mac / Linux)
Jika Anda menggunakan PC biasa, prosesnya jauh lebih sederhana karena tidak butuh VNC:
1. Pastikan Anda sudah menginstal **Google Chrome** di komputer Anda.
2. Pastikan **Python 3** sudah terinstal.
3. Buka terminal/Command Prompt/PowerShell di PC Anda.

---

## 🚀 Instalasi Skrip (Semua Platform)

Kloning repositori ini dan instal library Python yang dibutuhkan:

```bash
git clone https://github.com/aminmaskur88/AutoPostTikTokSelenium.git
cd AutoPostTikTokSelenium
pip install -r requirements.txt
```

---

## 📂 Struktur Proyek & Format Metadata

### Menyiapkan Folder Konten
Setiap video yang akan diupload harus diletakkan dalam **sub-folder** tersendiri di dalam folder `Post/`.

**Contoh Struktur Direktori:**
```text
Post/
└── ai-tomat-pintar/
    ├── ai-tomat-pintar.mp4
    └── post_meta.json
```

### Struktur `post_meta.json` (WAJIB)
Setiap folder **wajib** memiliki file `post_meta.json` yang berisi detail postingan. Jangan hilangkan format ini:

```json
{
  "post_title": "AI Cerdas Sortir Tomat Modern",
  "summary": "Teknologi AI ini memindai tomat dalam hitungan detik untuk mendeteksi kematangan dan kerusakan secara otomatis.",
  "hashtags": [
    "#AISortirTomat",
    "#PertanianModern",
    "#TeknologiAI"
  ],
  "cta": "Teknologi apa lagi yang bisa bantu petani Indonesia?",
  "image_count": 1,
  "generated_at": "2026-03-20 08:56:18"
}
```

---

## 📋 Alur Kerja (Workflow)

### 1. Inisialisasi Sesi Login (Jalankan Sekali)
Menyimpan sesi profil (cookie) Anda.
- **Di Termux:** `export DISPLAY=:1 && python tiktok_login.py` (Lalu login via VNC).
- **Di PC:** `python tiktok_login.py` (Browser akan terbuka, silakan login).

*Tutup terminal (`Ctrl+C`) setelah Anda berhasil masuk ke beranda/profil.*

### 2. Eksekusi Upload Masal
Menjalankan mesin uploader otomatis.
- **Di Termux:** `export DISPLAY=:1 && python tiktok_uploader.py`
- **Di PC:** `python tiktok_uploader.py`

**Cara Kerja Mesin:**
- Skrip akan langsung mulai melakukan **Warmup** (Pemanasan menonton video).
- Jika muncul **Captcha**, skrip akan menjeda otomatis. Selesaikan puzzle captcha-nya, dan skrip akan lanjut dengan sendirinya.
- Folder yang hanya berisi foto akan di-skip.
- Setelah upload sukses, **Visual Countdown** (Hitung mundur) akan berjalan di terminal sebelum melanjutkan ke video berikutnya.

---

## 💡 Troubleshooting & Tips
- **Captcha:** Jangan panik jika muncul tulisan merah "CAPTCHA TERDETEKSI!" di terminal. Cukup buka browser/VNC Anda dan geser kepingan puzzle-nya.
- **Hanya Video (.mp4):** Pastikan media Anda berformat video. Uploader saat ini dikonfigurasi untuk melewati gambar/foto.
- **Jeda Aman (Anti-Spam):** Untuk menjaga skor kesehatan akun TikTok Anda, sangat disarankan menggunakan jeda minimal **10 - 20 menit** antar postingan.

---

## 🤝 Kontribusi & Kredit
Dikembangkan dan disempurnakan dengan bantuan kecerdasan buatan:
- **Gemini AI (Google)** - Logika otomasi, optimasi XPath lintas-platform, fitur Auto-Captcha pause, dan dokumentasi ini.

---
**License:** [MIT](LICENSE) | **Author:** Amin Maskur