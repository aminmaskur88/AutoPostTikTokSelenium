# 🎥 TikTok Automation Suite (Termux/Android Edition)

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.9.1-green.svg?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Termux](https://img.shields.io/badge/Environment-Termux-orange.svg?logo=android&logoColor=white)](https://termux.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sebuah koleksi skrip otomasi profesional untuk **TikTok Web** yang dirancang khusus untuk berjalan di lingkungan **Android (Termux)** menggunakan **X11 Forwarding/VNC Server**. Proyek ini memungkinkan Anda melakukan manajemen konten TikTok secara otomatis dengan teknik yang sulit terdeteksi (anti-bot).

---

## ✨ Fitur Utama

- 🛡️ **Advanced Anti-Bot:** Menghilangkan jejak `navigator.webdriver` dan menggunakan `User-Agent` yang konsisten.
- 🍪 **Persistent Session:** Sesi login (cookies, cache, localStorage) tersimpan aman di direktori profil, menghindari login berulang.
- 📦 **Bulk Uploader (Folder-Based):** Mengunggah puluhan video secara berurutan hanya dengan satu perintah.
- ⌨️ **Human-like Interaction:**
  - Simulasi gerakan mouse (`ActionChains`).
  - Pengetikan teks menggunakan metode fisik (`Ctrl+V`) untuk stabilitas editor React.
  - Skenario "Pemanasan" (menonton video sebelum memposting).
- 🛠️ **Smart Logic:** Otomatis menangani popup hak cipta ("Content may be..."), konfirmasi "Post now", dan verifikasi status upload.
- 🔍 **Ultimate XPath Helper:** Skrip fleksibel untuk mengidentifikasi elemen web baru secara dinamis.

---

## 🛠️ Persiapan Lingkungan (Termux)

### 1. Update & Install Dependencies Sistem
Jalankan perintah ini untuk memastikan semua library GUI dan Browser terpasang:
```bash
pkg update && pkg upgrade
pkg install x11-repo
pkg install chromium chromedriver tigervnc fluxbox
```

### 2. Konfigurasi VNC Server
Agar browser dapat tampil secara visual di Android:
```bash
# Buat password VNC
vncpasswd

# Mulai server VNC (Resolusi HD)
vncserver -localhost :1 -geometry 1280x720

# Di Terminal baru, atur environment display:
export DISPLAY=:1
```
*Gunakan aplikasi **VNC Viewer** di Play Store untuk menghubungkan ke `127.0.0.1:5901`.*

### 3. Instalasi Skrip
```bash
git clone https://github.com/username/TikTok-Selenium-Uploader.git
cd TikTok-Selenium-Uploader
pip install -r requirements.txt
```

---

## 📂 Struktur Proyek & Panduan File

| File | Deskripsi |
| :--- | :--- |
| `tiktok_login.py` | 🔑 **Login Manager:** Jalankan pertama kali untuk menyimpan sesi login manual Anda. |
| `tiktok_uploader.py` | 🚀 **Bulk Engine:** Skrip utama untuk proses upload masal otomatis dari folder `Post/`. |
| `tiktok_post.py` | 🧪 **Single Tester:** Digunakan untuk menguji fungsionalitas upload pada satu file spesifik. |
| `get_xpath.py` | 🎯 **Element Finder:** Alat pembantu untuk mengambil XPath elemen web apa pun secara klik-langsung. |
| `Post/` | 📁 **Content Storage:** Direktori tempat menyimpan folder konten (Video + JSON Meta). |
| `tiktok_profile/` | 👤 **User Profile:** Folder otomatis berisi data sesi Chromium Anda. |

---

## 📋 Alur Kerja (Workflow) Profesional

### 1. Inisialisasi Sesi Login
Jalankan skrip ini, buka VNC, dan login ke TikTok secara manual di Chromium:
```bash
export DISPLAY=:1
python tiktok_login.py
```
*Setelah masuk ke Beranda/Profil, Anda dapat menutup terminal (`Ctrl+C`). Sesi Anda sekarang tersimpan.*

### 2. Menyiapkan Folder Konten
Setiap konten harus diletakkan dalam sub-folder di dalam `Post/`. Contoh:
```text
Post/
└── ai-tomat-pintar/
    ├── ai-tomat-pintar.mp4
    └── post_meta.json
```

**Contoh Struktur `post_meta.json`:**
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

### 3. Eksekusi Upload Masal
Jalankan engine uploader dan ikuti instruksi interaktifnya:
```bash
export DISPLAY=:1
python tiktok_uploader.py
```
*Anda akan diminta memasukkan nama folder target dan jeda antar postingan (dalam MENIT).*

---

## 💡 Troubleshooting & Tips
- **Stale Element / Interactable Error:** Pastikan koneksi internet stabil. Skrip sudah dilengkapi dengan pencarian ulang elemen otomatis jika terjadi re-render UI.
- **Empty Caption:** Jika `Ctrl+V` menghasilkan teks kosong, pastikan browser Chromium mengizinkan akses clipboard (skrip akan menginjeksi tombol "Copy" otomatis untuk memicu izin ini).
- **Anti-Spam:** Sangat disarankan untuk menggunakan jeda minimal **10-20 menit** antar postingan jika mengunggah lebih dari 5 video sehari.

---

## 🤝 Kontribusi & Kredit
Proyek ini dikembangkan untuk tujuan edukasi dan otomasi manajemen konten kreatif.

### 🤖 Special Thanks
Dikembangkan dan disempurnakan dengan bantuan kecerdasan buatan:
- **Gemini AI (Google)** - Menangani logika otomasi Selenium, optimasi XPath, dan dokumentasi profesional ini.

---
**License:** [MIT](LICENSE) | **Author:** Amin Maskur