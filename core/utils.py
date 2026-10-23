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

def find_browser_binary():
    """Mendeteksi lokasi binary browser berbasis Chromium yang terpasang (Brave, Chrome, Edge)."""
    candidates = [
        os.environ.get("CHROME_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def find_chromedriver():
    """Mendeteksi chromedriver yang terpasang dan dapat dijalankan (tidak terblokir policy Windows)."""
    candidates = [
        os.environ.get("CHROMEDRIVER_PATH"),
    ]
    cache_base = os.path.expanduser(r"~/.cache/selenium/chromedriver/win64")
    if os.path.exists(cache_base):
        for ver in sorted(os.listdir(cache_base), reverse=True):
            p = os.path.join(cache_base, ver, "chromedriver.exe")
            if os.path.exists(p) and p not in candidates:
                candidates.append(p)
                
    for c in candidates:
        if c and os.path.exists(c):
            try:
                res = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    return c
            except Exception:
                continue
    return None

def setup_driver(profile_path, headless=False):
    profile_path = os.path.abspath(profile_path)
    os.makedirs(profile_path, exist_ok=True)
    kill_profile_lock_and_processes(profile_path)
    
    chrome_options = Options()
    
    browser_bin = CHROME_PATH or find_browser_binary()
    if browser_bin:
        chrome_options.binary_location = browser_bin
    
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

    driver_bin = CHROMEDRIVER_PATH or find_chromedriver()
    service = Service(driver_bin) if driver_bin else None

    try:
        if IS_TERMUX and CHROMEDRIVER_PATH:
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        elif service:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"[!] Gagal memulai Browser ({e}), membersihkan file lock dan mencoba lagi...")
        kill_profile_lock_and_processes(profile_path)
        if IS_TERMUX and CHROMEDRIVER_PATH:
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        elif service:
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

def sync_from_mtp_device(mtp_source_path=None, local_target_dir=None):
    """
    Menyinkronkan folder konten dari HP / Tablet Android MTP (POCO Pad, Infinix, dll) ke folder lokal PC.
    Mendukung path dinamis spesifik maupun fallback deteksi otomatis perangkat MTP.
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
    $sourcePath = @'
{mtp_source_path or ''}
'@.Trim().Trim('"').Trim("'")
    $targetLocal = '{local_target_dir}'

    $targetFolder = $null

    if ($sourcePath -and $sourcePath -ne "") {{
        $parts = $sourcePath -split '[\\\\/]' | Where-Object {{ $_.Trim() -ne "" }}
        if ($parts.Count -gt 0 -and $parts[0] -match "^(This PC|Computer)$") {{
            $parts = $parts[1..($parts.Length - 1)]
        }}

        $currentFolder = $thisPC
        $allMatched = $true
        for ($i = 0; $i -lt $parts.Length; $i++) {{
            $seg = $parts[$i]
            $found = $null
            foreach ($item in $currentFolder.Items()) {{
                if ($item.Name -eq $seg -or $item.Name -like "*$seg*") {{
                    $found = $item
                    break
                }}
            }}
            if (-not $found) {{
                $allMatched = $false
                break
            }}
            $currentFolder = $found.GetFolder
            if (-not $currentFolder) {{
                $allMatched = $false
                break
            }}
        }}
        if ($allMatched -and $currentFolder) {{
            $targetFolder = $currentFolder
        }}
    }}

    # Fallback auto-detection jika path tidak diberikan atau tidak cocok persis
    if (-not $targetFolder) {{
        $devices = $thisPC.Items() | Where-Object {{ $_.GetFolder -ne $null }}
        foreach ($dev in $devices) {{
            $devFolder = $dev.GetFolder
            foreach ($st in $devFolder.Items()) {{
                if ($st.GetFolder) {{
                    $stFolder = $st.GetFolder
                    foreach ($sub in $stFolder.Items()) {{
                        if ($sub.Name -eq "output_AminMaskur") {{
                            $targetFolder = $sub.GetFolder
                            break
                        }}
                        if ($sub.Name -eq "ProjectKURKUR" -and $sub.GetFolder) {{
                            foreach ($sub2 in $sub.GetFolder.Items()) {{
                                if ($sub2.Name -eq "output_AminMaskur") {{
                                    $targetFolder = $sub2.GetFolder
                                    break
                                }}
                            }}
                        }}
                        if ($targetFolder) {{ break }}
                    }}
                }}
                if ($targetFolder) {{ break }}
            }}
            if ($targetFolder) {{ break }}
        }}
    }}

    if (-not $targetFolder) {{
        Write-Error "MTP_SOURCE_NOT_FOUND"
        exit 1
    }}

    if (-not (Test-Path $targetLocal)) {{
        New-Item -ItemType Directory -Force -Path $targetLocal | Out-Null
    }}

    $items = $targetFolder.Items()
    $synced = 0
    foreach ($sub in $items) {{
        $subName = $sub.Name
        $destSub = Join-Path $targetLocal $subName
        if (-not (Test-Path $destSub)) {{
            New-Item -ItemType Directory -Force -Path $destSub | Out-Null
        }}
        $destSubShell = $shell.Namespace($destSub)
        if ($sub.GetFolder) {{
            $subItems = $sub.GetFolder.Items()
            $existingCount = (Get-ChildItem -Path $destSub -ErrorAction SilentlyContinue).Count
            if ($existingCount -lt $subItems.Count) {{
                $destSubShell.CopyHere($subItems, 16)
                $timeout = 25
                while ((Get-ChildItem -Path $destSub -ErrorAction SilentlyContinue).Count -lt $subItems.Count -and $timeout -gt 0) {{
                    Start-Sleep -Milliseconds 400
                    $timeout--
                }}
                $synced++
                Write-Output "Synced: $subName"
            }}
        }}
    }}
    Write-Output "SYNC_SUCCESS"
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=180)
        if "SYNC_SUCCESS" in res.stdout:
            return local_target_dir
        else:
            if "MTP_SOURCE_NOT_FOUND" in res.stderr or "MTP_SOURCE_NOT_FOUND" in res.stdout:
                print(f"[!] Perangkat atau path MTP tidak ditemukan: '{mtp_source_path}'")
            return None
    except Exception as e:
        print(f"[!] Peringatan sinkronisasi MTP: {e}")
        return None
