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
Jika Anda menggunakan PC biasa, prosesnya jauh lebih sederhana karena tidak butuh VNC. Ikuti langkah instalasi berikut secara berurutan:

1. **Instal Google Chrome:** Pastikan Anda sudah menginstal browser [Google Chrome](https://www.google.com/chrome/) versi terbaru.
2. **Instal Python 3:** 
   - **Cara Manual (Direkomendasikan):** Unduh dari [python.org/downloads](https://www.python.org/downloads/). **SANGAT PENTING:** Saat menjalankan installer, wajib mencentang kotak **✅ "Add Python to PATH"** di bagian bawah sebelum klik "Install Now".
   - **Cara Cepat (CMD Windows 10/11):** Buka Command Prompt, ketik: `winget install Python.Python.3.12` (Setelah selesai, tutup dan buka kembali CMD).
3. **Instal Git:**
   - **Cara Manual:** Unduh dari [git-scm.com](https://git-scm.com/download/win). Ikuti instruksi "Next" hingga selesai.
   - **Cara Cepat (CMD Windows 10/11):** Buka Command Prompt, ketik: `winget install --id Git.Git -e --source winget` (Setelah selesai, tutup dan buka kembali CMD).
4. **Verifikasi:** Buka Command Prompt (CMD) baru, ketik `python --version` dan `git --version`. Jika muncul angka versi, Anda siap lanjut ke tahap berikutnya.

---

## 🚀 Instalasi Skrip (Semua Platform)

Setelah Python dan Git terpasang, jalankan perintah ini di terminal/CMD Anda:

```bash
# 1. Clone repositori ini
git clone https://github.com/aminmaskur88/AutoPostTikTokSelenium.git SeleniumPostTiktok
cd SeleniumPostTiktok

# 2. Instal library yang dibutuhkan
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

## 📋 Alur Kerja (Workflow) & Cara Penggunaan

### 1. Inisialisasi Sesi Login (Jalankan Sekali Saja)
Langkah ini wajib dilakukan pertama kali di perangkat baru untuk menyimpan sesi/cookie Anda.

**Di Termux (Android):**
1. Buka aplikasi Termux.
2. Jalankan perintah satu baris ini untuk memulai VNC dan skrip login:
   ```bash
   vncserver -localhost :1; cd ~/SeleniumPostTiktok && DISPLAY=:1 python tiktok_login.py
   ```
3. Buka aplikasi **VNC Viewer** di HP Anda, sambungkan ke `127.0.0.1:5901`.
4. Anda akan melihat browser Chrome terbuka. Silakan login ke TikTok secara manual.
5. Setelah berhasil masuk ke Beranda, kembali ke Termux dan tekan `Ctrl + C` untuk menutup skrip. Profil Anda kini tersimpan!

**Di PC (Windows/Mac/Linux):**
1. Buka CMD/Terminal, navigasi ke folder proyek: `cd SeleniumPostTiktok`
2. Jalankan: `python tiktok_login.py`
3. Jendela Chrome akan terbuka. Login secara manual.
4. Tutup terminal (`Ctrl + C`) setelah masuk ke Beranda.

### 2. Eksekusi Upload Masal
Setelah sesi login tersimpan dan folder `Post/` sudah diisi dengan konten Anda, jalankan mesin uploader.

**Cara Menjalankan:**
- **Termux:** `cd ~/SeleniumPostTiktok && DISPLAY=:1 python tiktok_uploader.py`
- **PC:** `python tiktok_uploader.py`

**Interaksi Terminal saat Skrip Berjalan:**
Saat skrip dijalankan, Anda akan ditanya 3 hal:
1. **Opsi Headless (y/n):** Ketik `y` jika Anda ingin browser berjalan di latar belakang (tanpa GUI, hemat RAM, tidak butuh VNC). Ketik `n` jika ingin melihat browser bergerak. *(Sangat disarankan `n` untuk Termux jika masih sering kena Captcha).*
2. **Nama Folder Media:** Tekan `Enter` jika konten Anda ada di folder default `Post`. Atau ketik nama folder lain jika Anda menggunakan direktori khusus.
3. **Jeda Antar Postingan:** Masukkan angka dalam menit (contoh: `15`). Jika dibiarkan kosong (tekan `Enter`), skrip akan mengacak jeda antara 2 hingga 5 menit secara otomatis.

### 3. Menggunakan Alat Pembantu XPath (`get_xpath.py`)
Jika TikTok memperbarui tampilan webnya dan uploader gagal menemukan kotak caption atau tombol post, Anda bisa mencari XPath baru secara manual.

**Cara Pakai:**
1. Jalankan: `python get_xpath.py` (Gunakan `export DISPLAY=:1` jika di Termux).
2. Masukkan URL: `tiktok.com/upload`
3. Browser akan terbuka. Di terminal, tekan `Enter` untuk mulai merekam klik.
4. Buka browser/VNC, klik pada elemen yang ingin Anda ketahui XPath-nya (misal: kotak caption).
5. XPath dan elemen HTML akan langsung tercetak di terminal Anda. Salin XPath tersebut dan perbarui di dalam `tiktok_uploader.py`.

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