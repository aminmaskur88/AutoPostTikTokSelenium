import os
import sys
import time
from utils import setup_driver, cleanup_profile

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CORE_DIR)
PROFILES_DIR = os.path.join(BASE_DIR, "tt_profiles")

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_GREEN = "\033[92m"
CLR_CYAN = "\033[96m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"

def login_menu():
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profiles = sorted([d for d in os.listdir(PROFILES_DIR) if os.path.isdir(os.path.join(PROFILES_DIR, d))])
    
    print(f"\n{CLR_BOLD}{CLR_CYAN}=== 🔐 TIKTOK PROFILE & LOGIN MANAGER ==={CLR_RESET}\n")
    print("Daftar Profil Tersedia:")
    for idx, p in enumerate(profiles, 1):
        print(f"  {idx}. {p}")
    print(f"  {len(profiles) + 1}. ➕ Tambah Profil Baru")
    print("  0. Keluar")
    
    choice = input(f"\n➜ Pilih opsi (0-{len(profiles) + 1}): ").strip()
    
    if choice == '0':
        return
        
    profile_name = ""
    if choice == str(len(profiles) + 1):
        profile_name = input("➜ Masukkan nama profil baru (misal: AkunUtama / Akun1): ").strip()
        if not profile_name:
            print(f"{CLR_RED}[✗] Nama profil tidak boleh kosong!{CLR_RESET}")
            return
    elif choice.isdigit() and 1 <= int(choice) <= len(profiles):
        profile_name = profiles[int(choice) - 1]
    else:
        print(f"{CLR_RED}[✗] Pilihan tidak valid!{CLR_RESET}")
        return

    profile_path = os.path.join(PROFILES_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    
    print(f"\n{CLR_YELLOW}[*] Membuka browser untuk profil: {profile_name}...{CLR_RESET}")
    print("Silakan lakukan Login ke TikTok di jendela browser yang terbuka.")
    print("Setelah login berhasil, biarkan jendela tetap terbuka atau tekan ENTER di sini untuk menyimpan dan menutup.\n")
    
    driver = setup_driver(profile_path, headless=False)
    driver.get("https://www.tiktok.com/login")
    
    try:
        input(f"{CLR_GREEN}➜ Tekan [ENTER] di sini setelah Anda selesai login di TikTok...{CLR_RESET}")
        print(f"{CLR_GREEN}[✓] Sesi profil '{profile_name}' berhasil disimpan!{CLR_RESET}")
    finally:
        driver.quit()
        cleanup_profile(profile_path)
        print(f"{CLR_CYAN}[i] Browser ditutup. Profil siap digunakan untuk auto-posting.{CLR_RESET}")

if __name__ == "__main__":
    login_menu()
