# 🎥 TikTok Automation Suite (Termux/Android Edition)

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.9.1-green.svg?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Termux](https://img.shields.io/badge/Environment-Termux-orange.svg?logo=android&logoColor=white)](https://termux.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sebuah koleksi skrip otomasi profesional untuk **TikTok Web** yang dirancang khusus untuk berjalan di lingkungan **Android (Termux)** menggunakan **X11 Forwarding/VNC Server**. Proyek ini memungkinkan Anda melakukan manajemen konten TikTok secara otomatis dengan teknik yang sulit terdeteksi (anti-bot).

---

## ✨ Fitur Utama

- 🛡️ **Advanced Anti-Bot:** Menghilangkan jejak `navigator.webdriver` dan menggunakan `User-Agent` yang konsisten.
- 🍪 **Persistent Session:** Sesi login (cookies, cache, localStorage) tersimpan aman di direktori profil.
- 📦 **Bulk Uploader (Video Only):** Mengunggah video `.mp4` secara berurutan. Otomatis melewati folder yang berisi foto.
- 🧩 **Manual Captcha Solver:** Skrip otomatis mendeteksi Captcha, menjeda proses, dan menunggu Anda menyelesaikannya lewat VNC sebelum melanjutkan.
- ⌨️ **Human-like Interaction:**
  - **Smart Warmup:** Simulasi tonton video dengan navigasi menu samping (For You, Explore, dll) dan tombol `Arrow Down` agar menyerupai perilaku manusia.
  - Pengetikan teks menggunakan metode fisik (`Ctrl+V`) untuk stabilitas editor React.
- 🛠️ **Smart Logic:** Menangani popup hak cipta, konfirmasi "Post now", dan verifikasi status upload.
- ⏳ **Visual Countdown:** Hitung mundur interaktif yang terlihat bergerak di terminal saat jeda antar postingan.
- 🔍 **Ultimate XPath Helper:** Skrip fleksibel untuk mengidentifikasi elemen web baru dengan fitur auto-HTTPS dan deteksi klik tingkat lanjut.

---

## 🛠️ Persiapan Lingkungan (Termux)

### 1. Update & Install Dependencies Sistem
```bash
pkg update && pkg upgrade
pkg install x11-repo
pkg install chromium chromedriver tigervnc fluxbox
```

### 2. Konfigurasi VNC Server
```bash
vncserver -localhost :1 -geometry 1280x720
export DISPLAY=:1
```
*Hubungkan **VNC Viewer** HP ke `127.0.0.1:5901`.*

### 3. Instalasi Skrip
```bash
git clone https://github.com/aminmaskur88/AutoPostTikTokSelenium.git
cd AutoPostTikTokSelenium
pip install -r requirements.txt
```

---

## 📂 Struktur Proyek & Panduan File

| File | Deskripsi |
| :--- | :--- |
| `tiktok_login.py` | 🔑 **Login Manager:** Jalankan pertama kali untuk menyimpan sesi login manual. |
| `tiktok_uploader.py` | 🚀 **Bulk Engine:** Skrip utama untuk proses upload masal otomatis. |
| `get_xpath.py` | 🎯 **Element Finder:** Alat pembantu mengambil XPath elemen dengan klik-langsung. |
| `Post/` | 📁 **Content Storage:** Folder konten (Video `.mp4` + JSON Meta). |

---

## 📋 Alur Kerja (Workflow)

### 1. Inisialisasi Sesi Login
```bash
export DISPLAY=:1
python tiktok_login.py
```
*Login manual di VNC, lalu tutup terminal (`Ctrl+C`) setelah masuk beranda.*

### 2. Eksekusi Upload Masal
```bash
export DISPLAY=:1
python tiktok_uploader.py
```
- Skrip akan langsung mulai melakukan **Warmup** (Pemanasan).
- Jika muncul **Captcha**, selesaikan di VNC. Skrip akan lanjut otomatis.
- Folder yang hanya berisi foto akan di-skip dengan peringatan.
- Setelah upload berhasil, hitung mundur visual akan berjalan di terminal.

---

## 💡 Troubleshooting & Tips
- **Captcha:** Jika skrip mendeteksi Captcha, segera buka VNC Viewer. Skrip akan menunggu Anda menyelesaikan puzzle tersebut.
- **Hanya Video:** Pastikan konten Anda berformat `.mp4`. Skrip ini sengaja melewati foto karena keterbatasan dukungan pada lingkungan tertentu.
- **Anti-Spam:** Gunakan jeda minimal **10-20 menit** antar postingan untuk menjaga kesehatan akun.

---

## 🤝 Kontribusi & Kredit
Dikembangkan dan disempurnakan dengan bantuan kecerdasan buatan:
- **Gemini AI (Google)** - Logika otomasi, optimasi XPath, fitur Captcha, dan pembaruan sistem ini.

---
**License:** [MIT](LICENSE) | **Author:** Amin Maskur
