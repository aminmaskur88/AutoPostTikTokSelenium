import os
import shutil
import socket
import subprocess
import time
import json
import sys
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
IS_WINDOWS = sys.platform == "win32"

if IS_TERMUX:
    CHROME_PATH = "/data/data/com.termux/files/usr/bin/chromium-browser"
    CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"
    os.environ["DISPLAY"] = ":1"
else:
    CHROME_PATH = None
    CHROMEDRIVER_PATH = None

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def cleanup_profile(profile_path):
    if not os.path.exists(profile_path):
        return

    folders_to_remove = [
        "Default/Cache", "Default/Code Cache", "Default/GPUCache",
        "Default/Service Worker/CacheStorage", "Default/Service Worker/ScriptCache",
        "Default/DawnWebGPUCache", "Default/DawnGraphiteCache", "Default/IndexedDB",
        "Default/Media Cache", "Default/Network/Reporting and NEL",
        "Default/VideoDecodeStats", "Default/Site Characteristics Database",
        "Default/optimization_guide_hint_cache_store",
        "Default/optimization_guide_model_metadata_store",
        "Default/AutofillStrikeDatabase", "Crashpad", "component_crx_cache",
        "TranslateKit", "WasmTtsEngine", "OptimizationHints",
        "GraphiteDawnCache", "GrShaderCache", "ShaderCache", "BrowserMetrics"
    ]

    for folder in folders_to_remove:
        full_path = os.path.join(profile_path, folder)
        if os.path.exists(full_path):
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
            except Exception:
                pass

def kill_profile_lock_and_processes(profile_path):
    profile_path = os.path.abspath(profile_path)
    
    if IS_TERMUX:
        try:
            res = subprocess.run(["pgrep", "-f", profile_path], stdout=subprocess.PIPE, text=True)
            if res.stdout.strip():
                pids = res.stdout.strip().split()
                current_pid = str(os.getpid())
                for pid in pids:
                    if pid != current_pid:
                        try:
                            os.kill(int(pid), 9)
                        except Exception:
                            pass
                time.sleep(0.5)
        except Exception:
            pass

    for lock_name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        lock_file = os.path.join(profile_path, lock_name)
        if os.path.exists(lock_file) or os.path.islink(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass

def setup_driver(profile_path, headless=False):
    profile_path = os.path.abspath(profile_path)
    os.makedirs(profile_path, exist_ok=True)
    kill_profile_lock_and_processes(profile_path)
    
    chrome_options = Options()
    if CHROME_PATH:
        chrome_options.binary_location = CHROME_PATH
    
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")
    
    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disk-cache-size=1")
    chrome_options.add_argument("--media-cache-size=1")

    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        if IS_TERMUX and CHROMEDRIVER_PATH:
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"[!] Gagal memulai Chrome ({e}), membersihkan file lock dan mencoba lagi...")
        kill_profile_lock_and_processes(profile_path)
        if IS_TERMUX and CHROMEDRIVER_PATH:
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass

    return driver

def update_post_status(post_path, status, progress=0):
    if not post_path:
        return
    if os.path.isfile(post_path):
        status_file = os.path.join(os.path.dirname(post_path), "upload_status.json")
    else:
        status_file = os.path.join(post_path, "upload_status.json")
        
    try:
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump({
                "status": status,
                "progress": int(progress),
                "timestamp": time.time()
            }, f, indent=4)
    except Exception:
        pass

def sync_from_mtp_device(local_target_dir=None):
    """
    Menyinkronkan folder konten dari HP Android MTP (Infinix SMART 6) ke folder konten PC lokal.
    Menggunakan Shell.Application COM dan menunggu file tersalin sempurna.
    """
    if not IS_WINDOWS:
        return None
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not local_target_dir:
        local_target_dir = os.path.join(base_dir, "content")
        
    os.makedirs(local_target_dir, exist_ok=True)
    
    ps_script = f"""
    $shell = New-Object -ComObject Shell.Application
    $thisPC = $shell.Namespace(17)
    $phone = $thisPC.Items() | Where-Object {{ $_.Name -like "*Infinix*" -or $_.Name -like "*SMART*" }}
    if (-not $phone) {{
        $phone = $thisPC.Items() | Where-Object {{ $_.GetFolder -ne $null }} | Select-Object -First 1
    }}
    if ($phone) {{
        $storage = $phone.GetFolder.Items() | Where-Object {{ $_.Name -like "*Penyimpanan*" -or $_.Name -like "*Internal*" }}
        if ($storage) {{
            $kurkur = $storage.GetFolder.Items() | Where-Object {{ $_.Name -eq "ProjectKURKUR" }}
            if ($kurkur) {{
                $outputDir = $kurkur.GetFolder.Items() | Where-Object {{ $_.Name -eq "output_AminMaskur" }}
                if ($outputDir) {{
                    $targetLocal = '{local_target_dir}'
                    foreach ($sub in $outputDir.GetFolder.Items()) {{
                        $destSub = Join-Path $targetLocal $sub.Name
                        $subItems = $sub.GetFolder.Items()
                        if (-not (Test-Path $destSub) -or (Get-ChildItem -Path $destSub -ErrorAction SilentlyContinue).Count -lt 2) {{
                            New-Item -ItemType Directory -Force -Path $destSub | Out-Null
                            $subDestShell = $shell.Namespace($destSub)
                            $subDestShell.CopyHere($subItems, 16)
                            $timeout = 15
                            while ((Get-ChildItem -Path $destSub -ErrorAction SilentlyContinue).Count -lt $subItems.Count -and $timeout -gt 0) {{
                                Start-Sleep -Milliseconds 400
                                $timeout--
                            }}
                            Write-Output "Synced: $($sub.Name)"
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=120)
        return local_target_dir
    except Exception as e:
        print(f"[!] Peringatan sinkronisasi MTP: {e}")
        return local_target_dir
