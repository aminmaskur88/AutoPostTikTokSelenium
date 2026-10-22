import os
import json
import time
import random
import sys
import re
import threading
import http.server
import socketserver
import base64
import webbrowser
import html
import shutil
from functools import partial
from datetime import datetime, timedelta
from pathlib import Path

# BASE DIRECTORIES
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CORE_DIR)
PROFILES_DIR = os.path.join(BASE_DIR, "tt_profiles")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from utils import setup_driver, cleanup_profile, update_post_status
from tt_executor import run_tt_scheduled_task

# --- TERMINAL COLOR & STYLING UTILS ---
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_DIM = "\033[2m"
CLR_UNDERLINE = "\033[4m"

CLR_RED = "\033[91m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_BLUE = "\033[94m"
CLR_MAGENTA = "\033[95m"
CLR_CYAN = "\033[96m"
CLR_WHITE = "\033[97m"

TAG_INFO = f"{CLR_CYAN}[i]{CLR_RESET}"
TAG_SUCCESS = f"{CLR_GREEN}[✓]{CLR_RESET}"
TAG_WARNING = f"{CLR_YELLOW}[!]{CLR_RESET}"
TAG_ERROR = f"{CLR_RED}[✗]{CLR_RESET}"
TAG_INPUT = f"{CLR_MAGENTA}➜{CLR_RESET}"

def print_header(title):
    print(f"\n{CLR_BOLD}{CLR_WHITE}=== {title} ==={CLR_RESET}\n")

def print_menu_box(title, items):
    print(f"\n{CLR_BOLD}{CLR_WHITE}=== {title} ==={CLR_RESET}")
    for item in items:
        print(f"  {CLR_CYAN}{item}{CLR_RESET}")
    print()

def print_progress_bar(current, total):
    """Menampilkan progress bar secara inline."""
    try:
        _, cols = os.get_terminal_size()
    except Exception:
        cols = 80
        
    if total == 0:
        percent = 0.0
        filled_len = 0
    else:
        percent = (current / total) * 100
        bar_len = min(cols - 35, 40)
        if bar_len < 10: bar_len = 10
        filled_len = int(bar_len * current // total)
        
    bar_len = min(cols - 35, 40)
    if bar_len < 10: bar_len = 10
    bar = '█' * filled_len + '░' * (bar_len - filled_len)
    bar_text = f"{CLR_GREEN}⚡ [PROGRESS TIKTOK] : [{bar}] {current}/{total} ({percent:.1f}%){CLR_RESET}"
    print(f"\n{bar_text}\n")

def clear_screen():
    try:
        sys.stdout.write("\033[r")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    except Exception:
        pass
    os.system('cls' if os.name == 'nt' else 'clear')

def getch():
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b'\x00', b'\xe0'):
            ch2 = msvcrt.getch()
            if ch2 == b'H': return 'up'
            elif ch2 == b'P': return 'down'
            elif ch2 == b'K': return 'left'
            elif ch2 == b'M': return 'right'
            return 'special'
        elif ch in (b'\r', b'\n'):
            return '\r'
        else:
            try:
                return ch.decode('utf-8', errors='ignore')
            except Exception:
                return ch.decode('latin1', errors='ignore')
    else:
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A': return 'up'
                        elif ch3 == 'B': return 'down'
                        else: return 'esc'
                    return 'esc'
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except Exception:
            return sys.stdin.read(1)

def select_menu_option(title, options, default_index=0):
    if not sys.stdin.isatty():
        print(f"\n=== {title} ===")
        for i, opt in enumerate(options):
            print(f"  {opt}")
        val = input(f"➜ Pilihan (1-{len(options)}): ").strip()
        try:
            for idx, opt in enumerate(options):
                clean_opt = re.sub(r'\033\[[0-9;]*m', '', opt).strip()
                if clean_opt.startswith(val):
                    return idx
            return int(val) - 1
        except Exception:
            return default_index

    selected = default_index
    while True:
        sys.stdout.write("\033[H\033[J")
        print(f"=== {title} ===")
        print()
        for i, opt in enumerate(options):
            clean_opt = re.sub(r'\033\[[0-9;]*m', '', opt).strip()
            display_text = clean_opt
            if re.match(r'^\d+\.\s*', clean_opt):
                display_text = re.sub(r'^\d+\.\s*', '', clean_opt)
                
            if i == selected:
                print(f"  {CLR_GREEN}❯ {CLR_BOLD}{display_text}{CLR_RESET}")
            else:
                print(f"    {CLR_DIM}{display_text}{CLR_RESET}")
        print()
        print(f"{CLR_DIM}➜ Gunakan [↑/↓] lalu [Enter], atau tekan angka (1-{len(options)}) langsung...{CLR_RESET}")
        sys.stdout.flush()

        ch = getch()
        if ch == 'up':
            selected = (selected - 1) % len(options)
        elif ch == 'down':
            selected = (selected + 1) % len(options)
        elif ch in ['\r', '\n']:
            return selected
        elif ch.isdigit():
            for idx, opt in enumerate(options):
                clean_opt = re.sub(r'\033\[[0-9;]*m', '', opt).strip()
                if clean_opt.startswith(ch):
                    return idx

def natural_sort_key(s):
    basename = os.path.splitext(os.path.basename(s))[0]
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', basename)]

def get_media_files(path):
    valid_ext = (".mp4", ".mov", ".webm", ".jpg", ".png", ".jpeg", ".webp")
    if os.path.isfile(path):
        return [os.path.abspath(path)] if path.lower().endswith(valid_ext) else []
    
    media = []
    if os.path.exists(path):
        for f in os.listdir(path):
            if f.lower().endswith(valid_ext):
                file_path = os.path.abspath(os.path.join(path, f))
                media.append(file_path)
    
    media.sort(key=natural_sort_key)
    return media

def get_post_metadata(post_path):
    """Membaca file post_meta.json atau plan_gemini.json."""
    post_path_norm = os.path.normpath(post_path)
    is_file = os.path.isfile(post_path_norm)
    meta = {}
    
    if not is_file:
        for candidate_name in ["post_meta.json", "plan_gemini.json"]:
            meta_file = os.path.join(post_path, candidate_name)
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    break
                except Exception:
                    pass
    else:
        base_no_ext = os.path.splitext(post_path_norm)[0]
        for candidate in [post_path_norm + ".json", base_no_ext + ".json"]:
            if os.path.exists(candidate):
                try:
                    with open(candidate, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    break
                except Exception:
                    pass
    return meta

def get_caption_text(post_path):
    """Menyusun teks caption & hashtags untuk TikTok."""
    post_path_norm = os.path.normpath(post_path)
    item_name = os.path.basename(post_path_norm)
    is_file = os.path.isfile(post_path_norm)
    
    meta = get_post_metadata(post_path)
    
    # Cek jika ada file caption .txt di dalam folder
    if not meta and not is_file:
        txt_files = [f for f in os.listdir(post_path) if f.lower().endswith('.txt') and not f.lower().startswith('uploaded')]
        if txt_files:
            try:
                with open(os.path.join(post_path, txt_files[0]), 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass

    clean_name = os.path.splitext(item_name)[0] if is_file else item_name
    default_title = clean_name.replace("_", " ").replace("-", " ").title()
    
    parts = []
    title = meta.get('post_title') or default_title
    if title: parts.append(title)
    
    summary = meta.get('summary', '').strip()
    if summary: parts.append(f"\n\n{summary}")
    
    hashtags = meta.get('hashtags', [])
    if hashtags:
        tags_list = [f"#{tag.lstrip('#').strip()}" for tag in hashtags if tag.strip()]
        parts.append(f"\n\n{' '.join(tags_list)}")
        
    caption = "".join(parts).strip()
    return caption or default_title

def get_datetime_input(prompt: str):
    while True:
        val = input(f"⏰ {CLR_BOLD}{prompt}{CLR_RESET}\n   (format: YYYY-MM-DD HH:MM, HH:MM, '+3 jam', atau ketik 'now'): ").strip().lower()
        if not val or val in ['now', 'sekarang', 'y']:
            return 'now'
            
        now = datetime.now()
        
        # 1. Format Relatif Jam (+3 jam / 3h / +3)
        m_jam = re.match(r'^\+?(\d+)\s*(h|jam)?$', val)
        if m_jam and ('h' in val or 'jam' in val or val.startswith('+')):
            hours = int(m_jam.group(1))
            res = now + timedelta(hours=hours)
            print(f"   {TAG_SUCCESS} Dijadwalkan {hours} jam dari sekarang: {res.strftime('%Y-%m-%d %H:%M')}")
            return res
            
        # 2. Format Relatif Menit (+30 menit / 30m)
        m_menit = re.match(r'^\+?(\d+)\s*(m|menit)$', val)
        if m_menit:
            mins = int(m_menit.group(1))
            res = now + timedelta(minutes=mins)
            print(f"   {TAG_SUCCESS} Dijadwalkan {mins} menit dari sekarang: {res.strftime('%Y-%m-%d %H:%M')}")
            return res

        # 3. Format Relatif Hari (+1 hari / 1d)
        m_hari = re.match(r'^\+?(\d+)\s*(d|hari)$', val)
        if m_hari:
            days = int(m_hari.group(1))
            res = now + timedelta(days=days)
            print(f"   {TAG_SUCCESS} Dijadwalkan {days} hari dari sekarang: {res.strftime('%Y-%m-%d %H:%M')}")
            return res

        # 4. Format Jam Saja (HH:MM atau HH.MM) -> Otomatis hari ini atau besok jika jam sudah lewat
        m_time = re.match(r'^(\d{1,2})[:.](\d{2})$', val)
        if m_time:
            h = int(m_time.group(1))
            m = int(m_time.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                print(f"   {TAG_SUCCESS} Waktu ditetapkan: {target.strftime('%Y-%m-%d %H:%M')}")
                return target

        # 5. Format Lengkap YYYY-MM-DD HH:MM
        try:
            clean_val = val.replace('.', ':')
            res = datetime.strptime(clean_val, "%Y-%m-%d %H:%M")
            print(f"   {TAG_SUCCESS} Waktu ditetapkan: {res.strftime('%Y-%m-%d %H:%M')}")
            return res
        except ValueError:
            print(f"   {TAG_ERROR} Format tidak dikenali. Contoh yang valid: '19:30', '+3 jam', '2026-10-21 19:30', atau 'now'.")

# --- WEB PREVIEW & EDITOR INTERAKTIF (LOCAL HTTP SERVER) ---

class TTPreviewState:
    def __init__(self, pending_items, item_data_map):
        self.pending_items = pending_items
        self.item_data_map = item_data_map
        self.lock = threading.Lock()
        self.server_should_shutdown = False

class TTPreviewRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, state, *args, **kwargs):
        self.state = state
        http.server.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = self.generate_html()
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path.startswith('/media/'):
            # /media/<item_idx>/<media_idx>
            parts = self.path.split('/')
            if len(parts) >= 4:
                try:
                    item_idx = int(parts[2])
                    media_idx = int(parts[3])
                    item_key = self.state.pending_items[item_idx]
                    media_files = self.state.item_data_map.get(item_key, {}).get('media_files', [])
                    if 0 <= media_idx < len(media_files):
                        media_path = media_files[media_idx]
                        if os.path.exists(media_path):
                            self.send_response(200)
                            ext = os.path.splitext(media_path)[1].lower()
                            mime = "video/mp4" if ext in ['.mp4', '.mov', '.webm'] else "image/jpeg"
                            self.send_header("Content-type", mime)
                            self.end_headers()
                            with open(media_path, 'rb') as f:
                                self.wfile.write(f.read())
                            return
                except Exception:
                    pass
            self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(content_length))

        if self.path == '/shutdown':
            self.send_response(200)
            self.end_headers()
            self.state.server_should_shutdown = True
        elif self.path == '/edit_caption':
            with self.state.lock:
                idx = data['index']
                item_path = self.state.pending_items[idx]
                self.state.item_data_map[item_path]['caption'] = data['caption']
            self.send_response(200)
            self.end_headers()
        elif self.path == '/edit_schedule':
            with self.state.lock:
                idx = data['index']
                item_path = self.state.pending_items[idx]
                self.state.item_data_map[item_path]['schedule_time'] = data.get('schedule_time')
            self.send_response(200)
            self.end_headers()
        elif self.path == '/delete_item':
            with self.state.lock:
                idx = data['index']
                item_path = self.state.pending_items.pop(idx)
                if item_path in self.state.item_data_map:
                    del self.state.item_data_map[item_path]
            self.send_response(200)
            self.end_headers()
        elif self.path == '/reorder':
            with self.state.lock:
                new_order = data['order']
                self.state.pending_items[:] = [self.state.pending_items[int(i)] for i in new_order]
            self.send_response(200)
            self.end_headers()

    def generate_html(self):
        items_html = ""
        for i, path in enumerate(self.state.pending_items):
            data = self.state.item_data_map[path]
            name = os.path.basename(path)
            media_files = data.get('media_files', [])
            sched = data.get('schedule_time') or '🚀 Posting SEKARANG'
            
            # Media thumbnail
            media_preview = ""
            if media_files:
                first_media = media_files[0]
                is_video = first_media.lower().endswith(('.mp4', '.mov', '.webm'))
                media_url = f"/media/{i}/0"
                if is_video:
                    media_preview = f'''
                    <div class="video-preview-box">
                        <video src="{media_url}" preload="metadata" style="max-height:160px; max-width:200px; border-radius:6px; background:#000;"></video>
                        <div class="video-badge">▶ Video ({len(media_files)})</div>
                    </div>'''
                else:
                    media_preview = f'''
                    <div class="image-preview-box">
                        <img src="{media_url}" style="max-height:160px; max-width:200px; border-radius:6px; object-fit:cover;">
                        <div class="image-badge">🖼️ Foto ({len(media_files)})</div>
                    </div>'''

            items_html += f"""
            <div class="item-card" data-index="{i}">
                <div class="item-header">
                    <div class="handle">☰</div>
                    <div class="item-info">
                        <div class="item-title">{html.escape(name)}</div>
                        <div class="item-meta">🕒 {html.escape(sched)} | 📁 {len(media_files)} Media</div>
                    </div>
                    <button class="btn-delete" onclick="deleteItem({i})">×</button>
                </div>
                <div class="item-body">
                    {media_preview}
                    <div class="caption-box">
                        <label style="font-size:12px; font-weight:bold; color:#fe2c55; margin-bottom:4px; display:block;">Caption & Hashtags TikTok:</label>
                        <textarea onchange="editCaption({i}, this.value)">{html.escape(data.get('caption', ''))}</textarea>
                    </div>
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <title>TikTok Auto-Poster Preview & Editor</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #0f0f0f; color: #f1f1f1; }}
                .header {{ background: #000; border-bottom: 1px solid #272727; color: white; padding: 16px; text-align: center; position: sticky; top: 0; z-index: 1000; display:flex; align-items:center; justify-content:center; gap:10px; }}
                .container {{ max-width: 860px; margin: 20px auto; padding: 0 16px; padding-bottom: 110px; }}
                .item-card {{ background: #1a1a1a; margin-bottom: 18px; border-radius: 10px; border: 1px solid #333; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
                .item-header {{ padding: 12px 16px; border-bottom: 1px solid #2a2a2a; display: flex; align-items: center; gap: 12px; background: #222; }}
                .handle {{ cursor: grab; font-size: 20px; color: #888; }}
                .item-info {{ flex: 1; }}
                .item-title {{ font-weight: bold; font-size: 15px; color: #fff; }}
                .item-meta {{ font-size: 12px; color: #aaa; margin-top: 3px; }}
                .btn-delete {{ background: #fe2c55; color: white; border: none; width: 26px; height: 26px; border-radius: 50%; cursor: pointer; font-size: 16px; font-weight: bold; }}
                .item-body {{ padding: 14px 16px; display: flex; gap: 16px; align-items: flex-start; }}
                .caption-box {{ flex: 1; }}
                textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #333; border-radius: 6px; padding: 10px; font-family: inherit; font-size: 13px; min-height: 120px; resize: vertical; background: #121212; color: #fff; outline:none; }}
                textarea:focus {{ border-color: #fe2c55; }}
                .video-preview-box, .image-preview-box {{ position: relative; }}
                .video-badge, .image-badge {{ position: absolute; bottom: 6px; left: 6px; background: rgba(0,0,0,0.7); color: #fff; font-size: 10px; padding: 3px 6px; border-radius: 4px; }}
                .footer-actions {{ position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; padding: 14px; border-top: 1px solid #333; display: flex; justify-content: center; z-index: 1000; }}
                .btn-start {{ background: #fe2c55; color: white; border: none; padding: 12px 40px; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer; transition: 0.2s; }}
                .btn-start:hover {{ background: #e02449; }}
                .sortable-ghost {{ opacity: 0.3; background: #333; }}
            </style>
        </head>
        <body>
            <div class="header">
                <span style="font-size:24px;">🎵</span>
                <h1 style="margin:0; font-size: 18px; font-weight:bold;">TikTok Scheduled Post Preview & Editor</h1>
            </div>
            
            <div class="container" id="items-container">
                {items_html}
            </div>
            
            <div class="footer-actions">
                <button class="btn-start" onclick="startUpload()">MULAI UPLOAD KE TIKTOK SEKARANG</button>
            </div>

            <script>
                function postAction(path, body) {{
                    return fetch(path, {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(body) }});
                }}

                document.addEventListener('DOMContentLoaded', () => {{
                    const container = document.getElementById('items-container');
                    new Sortable(container, {{
                        handle: '.handle',
                        animation: 150,
                        ghostClass: 'sortable-ghost',
                        onEnd: function() {{
                            const order = Array.from(container.querySelectorAll('.item-card')).map(el => el.dataset.index);
                            postAction('/reorder', {{ order }});
                        }}
                    }});
                }});

                function editCaption(index, caption) {{
                    postAction('/edit_caption', {{ index, caption }});
                }}

                function deleteItem(index) {{
                    if(confirm('Hapus item ini dari antrean TikTok?')) {{
                        postAction('/delete_item', {{ index }}).then(() => location.reload());
                    }}
                }}

                function startUpload() {{
                    if(confirm('Mulai proses upload TikTok via Selenium?')) {{
                        postAction('/shutdown', {{}}).then(() => {{
                            document.body.innerHTML = `
                                <div style="text-align:center; margin-top:100px; font-family:sans-serif;">
                                    <h2 style="color:#fe2c55;">✅ Server Ditutup</h2>
                                    <p style="color:#aaa;">Silakan kembali ke Terminal untuk melihat proses otomasi TikTok.</p>
                                </div>`;
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        """

class SilentTCPServer(socketserver.TCPServer):
    def handle_error(self, request, client_address):
        exc_type, _, _ = sys.exc_info()
        if exc_type in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        super().handle_error(request, client_address)

def run_interactive_preview_web(pending_items, item_data_map):
    state = TTPreviewState(list(pending_items), dict(item_data_map))
    PORT = 8085
    Handler = partial(TTPreviewRequestHandler, state)
    SilentTCPServer.allow_reuse_address = True
    
    while True:
        try:
            httpd = SilentTCPServer(('', PORT), Handler)
            break
        except Exception:
            PORT += 1

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n{TAG_SUCCESS} Server Pratinjau TikTok berjalan di: {CLR_CYAN}{url}{CLR_RESET}")
    print("   Silakan edit caption, hashtags, atau urutan di browser.")
    
    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        while not state.server_should_shutdown:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[!] Pratinjau dihentikan pengguna.")

    httpd.shutdown()
    httpd.server_close()
    server_thread.join()
    print("✅ Pratinjau selesai. Memulai upload TikTok...\n")
    return state.pending_items, state.item_data_map

# --- ASCII LIVE UPLOAD DASHBOARD ---

class UploadDashboard:
    def __init__(self, pending_items, item_data_map):
        self.pending_items = list(pending_items)
        self.item_data_map = dict(item_data_map)
        self.statuses = {item: "pending" for item in self.pending_items}
        self.current_idx = 0
        self.success_count = 0
        self.failed_count = 0
        self.current_job = {
            "name": "",
            "date": "",
            "upload": "Pending",
            "caption": "Pending",
            "scheduling": "Pending",
            "activity": "Pending"
        }

    def render(self):
        sys.stdout.write("\033[H\033[J")
        print("╭──────────────────────────────────────────────────────────────╮")
        print("│                 🎵 TIKTOK AUTO-POSTER MANAGER                │")
        print("│                     Scheduled & Instant                      │")
        print("╰──────────────────────────────────────────────────────────────╯\n")
        
        # Progress Bar
        total = len(self.pending_items)
        current = self.current_idx
        percent = 0.0 if total == 0 else (current / total) * 100
        bar_len = 36
        filled_len = int(bar_len * current // total) if total > 0 else 0
        bar = '█' * filled_len + '░' * (bar_len - filled_len)
        print("  Progress")
        print(f"  {CLR_GREEN}{bar}{CLR_RESET}  {current}/{total}  ({percent:.1f}%)\n")
        
        # Current Job
        print("  CURRENT JOB")
        job = self.current_job
        name_tr = job["name"][:50] + "..." if len(job["name"]) > 53 else job["name"]
        print(f"  📄 {CLR_BOLD}{CLR_WHITE}{name_tr}{CLR_RESET}")
        print(f"  📅 {CLR_YELLOW}{job['date']}{CLR_RESET}\n")
        
        def format_status(val):
            if val in ["Completed", "Injected"]:
                return f"{CLR_GREEN}✓ Selesai{CLR_RESET}"
            elif val == "Pending":
                return f"{CLR_DIM}Pending{CLR_RESET}"
            elif val == "Failed":
                return f"{CLR_RED}✗ Gagal{CLR_RESET}"
            else:
                return f"{CLR_BLUE}⟳ {val}{CLR_RESET}"

        print(f"  📤 Upload       {format_status(job['upload'])}")
        print(f"  📝 Caption      {format_status(job['caption'])}")
        print(f"  🗓️  Scheduling  {format_status(job['scheduling'])}\n")
        
        act = job.get("activity", "-")
        act_tr = act[:50] + "..." if len(act) > 53 else act
        print(f"  ⚙️ Aktivitas   {CLR_DIM}{act_tr}{CLR_RESET}\n")
        
        # Recent items
        print("  RECENT")
        recent_items = []
        for idx, item in enumerate(self.pending_items):
            item_name = os.path.basename(item)
            item_tr = item_name[:35] + "..." if len(item_name) > 38 else item_name
            status = self.statuses[item]
            sched_time = self.item_data_map.get(item, {}).get('schedule_time')
            time_str = sched_time.split()[1] if sched_time else "now"
            
            if status == "success":
                recent_items.append(f"  {CLR_GREEN}✓{CLR_RESET} {item_tr:<38} {CLR_DIM}{time_str:>8}{CLR_RESET}")
            elif status == "failed":
                recent_items.append(f"  {CLR_RED}✗{CLR_RESET} {item_tr:<38} {CLR_RED}{time_str:>8}{CLR_RESET}")
            elif idx == current:
                recent_items.append(f"  {CLR_BLUE}⟳{CLR_RESET} {CLR_BOLD}{item_tr:<38} {CLR_YELLOW}{time_str:>8}{CLR_RESET}")
            else:
                recent_items.append(f"  {CLR_DIM}○{CLR_RESET} {CLR_DIM}{item_tr:<38} {time_str:>8}{CLR_RESET}")
                
        start_slice = max(0, current - 2)
        end_slice = min(len(recent_items), start_slice + 4)
        for r_line in recent_items[start_slice:end_slice]:
            print(r_line)
        print()
        
        proc_count = 1 if current < total else 0
        print("──────────────────────────────────────────────────────────────")
        print(f"  {CLR_GREEN}✓ Success: {self.success_count}{CLR_RESET}     {CLR_RED}✗ Failed: {self.failed_count}{CLR_RESET}     {CLR_BLUE}⟳ Processing: {proc_count}{CLR_RESET}")
        print("──────────────────────────────────────────────────────────────\n")
        sys.stdout.flush()

# --- DRAFT STORAGE HELPERS ---
def load_drafts():
    path = os.path.join(BASE_DIR, "draft_posts_tt.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_drafts(drafts):
    path = os.path.join(BASE_DIR, "draft_posts_tt.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=4)

# --- WORKFLOW UTAMA POSTING TIKTOK ---

def run_tiktok_post_workflow(args=None):
    clear_screen()
    print_header("🎵 MODE UPLOAD & JADWAL TIKTOK")
    
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profiles = sorted([d for d in os.listdir(PROFILES_DIR) if os.path.isdir(os.path.join(PROFILES_DIR, d))])
    if not profiles:
        print(f"{TAG_ERROR} Belum ada profil TikTok! Jalankan tt_login.py terlebih dahulu.")
        return

    profile_options = [f"{i+1}. {p}" for i, p in enumerate(profiles)] + ["0. Batal / Kembali"]
    sel_idx = select_menu_option("PILIH PROFIL TIKTOK", profile_options)
    if sel_idx == len(profiles):
        return
    sel_profile = profiles[sel_idx]

    default_content_dir = os.path.join(BASE_DIR, "content")
    prompt_str = f"\n{TAG_INPUT} Masukkan Path Folder / File Konten"
    if os.path.exists(default_content_dir):
        prompt_str += f" [Enter = folder lokal: {default_content_dir}]"
    prompt_str += ": "

    parent_folder = input(prompt_str).strip().replace('"', '').replace("'", "")
    if not parent_folder and os.path.exists(default_content_dir):
        parent_folder = default_content_dir
    
    # Deteksi jika input berupa perangkat HP MTP (seperti Infinix SMART 6)
    if parent_folder.lower().startswith("this pc") or "infinix" in parent_folder.lower() or "projectkurkur" in parent_folder.lower():
        print(f"\n{TAG_INFO} Terdeteksi perangkat HP MTP (Infinix). Menyinkronkan konten ke penyimpanan lokal...")
        from utils import sync_from_mtp_device
        local_dir = sync_from_mtp_device()
        if local_dir and os.path.exists(local_dir):
            parent_folder = local_dir
            print(f"{TAG_SUCCESS} Konten MTP berhasil disinkronkan ke: {parent_folder}")

    if not os.path.exists(parent_folder):
        print(f"\n{TAG_ERROR} Path tidak ditemukan atau perangkat tidak terhubung: '{parent_folder}'")
        return

    # Deteksi Pending Items (Lewati yang sudah ditandai uploadedtt)
    all_detected_items = []
    pending_items = []
    if os.path.isfile(parent_folder):
        all_detected_items.append(parent_folder)
        if not os.path.exists(parent_folder + ".uploadedtt"):
            pending_items.append(parent_folder)
    else:
        for f in sorted(os.listdir(parent_folder), key=natural_sort_key):
            f_path = os.path.join(parent_folder, f)
            if os.path.isdir(f_path):
                media = get_media_files(f_path)
                if media:
                    all_detected_items.append(f_path)
                    marker = os.path.join(f_path, "uploadedtt.txt")
                    if not os.path.exists(marker):
                        pending_items.append(f_path)
            elif os.path.isfile(f_path) and f_path.lower().endswith((".mp4", ".mov", ".webm")):
                all_detected_items.append(f_path)
                if not os.path.exists(f_path + ".uploadedtt"):
                    pending_items.append(f_path)

    if not pending_items:
        if all_detected_items:
            print(f"\n{TAG_WARNING} Terdeteksi {len(all_detected_items)} item konten, namun semuanya sudah ditandai pernah diupload (uploadedtt.txt).")
            print("   Jika Anda ingin mengunggah ulang, hapus file 'uploadedtt.txt' di dalam folder konten terkait.")
        else:
            print(f"\n{TAG_WARNING} Tidak ditemukan file video (.mp4/.mov) atau folder media di path ini.")
        return

    print(f"\n{TAG_SUCCESS} Ditemukan {CLR_BOLD}{CLR_GREEN}{len(pending_items)}{CLR_RESET} item konten baru yang siap diunggah.")

    # Pilihan Strategi Penjadwalan
    sched_options = [
        "1. Jadwalkan dengan Interval Jam (Otomatis)",
        "2. Jadwalkan dengan Interval Hari (Otomatis)",
        "3. Manual per Post (Tanya jadwal tiap item)",
        "4. Langsung Posting Semua (Post Now)",
        "5. Simpan sebagai Draf Lokal"
    ]
    choice_idx = select_menu_option("STRATEGI PENJADWALAN TIKTOK", sched_options)
    choice = str(choice_idx + 1)

    is_post_now = (choice == '4')
    is_draft = (choice == '5')
    current_time_obj = None
    interval_mins = 0

    if choice in ['1', '2']:
        start_time_input = get_datetime_input("Masukkan waktu mulai untuk postingan PERTAMA")
        current_time_obj = datetime.now() + timedelta(minutes=20) if start_time_input == 'now' else start_time_input
        unit = "jam" if choice == '1' else "hari"
        try:
            interval_val = int(input(f"\n{TAG_INPUT} Masukkan interval per post (dalam {unit}): ").strip())
            interval_mins = interval_val * 60 if choice == '1' else interval_val * 1440
        except ValueError:
            interval_mins = 60 if choice == '1' else 1440
    elif choice == '4':
        try:
            interval_mins = int(input(f"\n{TAG_INPUT} Jeda antar posting (menit) [Enter=0]: ") or 0)
        except ValueError:
            interval_mins = 0

    is_headless = input(f"\n{TAG_INPUT} Gunakan Mode Headless? (y/n, default n): ").lower() == 'y'

    preview_options = [
        "1. Tanpa Pratinjau (Langsung Eksekusi)",
        "2. Pratinjau Web Interaktif (Edit Caption / Urutan)",
    ]
    preview_idx = select_menu_option("PILIHAN PRATINJAU", preview_options)
    is_web_preview = (preview_idx == 1)

    # Proteksi Batas Jadwal TikTok: Maksimal 10 Hari
    max_allowed_tt = datetime.now() + timedelta(days=10)
    item_data_map = {}
    temp_time = current_time_obj

    valid_pending_items = []
    overflow_pending_items = []

    for item in pending_items:
        sched_str = None
        if choice in ['1', '2'] and temp_time:
            # Bulatkan menit ke kelipatan 5 (kebijakan waktu TikTok Studio)
            rounded_minute = (temp_time.minute // 5) * 5
            temp_time = temp_time.replace(minute=rounded_minute, second=0)
            
            if temp_time > max_allowed_tt:
                overflow_pending_items.append(item)
                continue
            sched_str = temp_time.strftime("%Y-%m-%d %H:%M")
            temp_time += timedelta(minutes=interval_mins)

        item_data_map[item] = {
            'caption': get_caption_text(item),
            'media_files': get_media_files(item),
            'schedule_time': sched_str
        }
        valid_pending_items.append(item)

    if overflow_pending_items:
        print(f"\n{TAG_WARNING} {len(overflow_pending_items)} item melebihi batas maksimal penjadwalan TikTok (10 hari).")
        print("   Item yang melebihi batas otomatis dilewati dan dapat dijadwalkan kemudian.")
        pending_items = valid_pending_items

    if is_web_preview:
        pending_items, item_data_map = run_interactive_preview_web(pending_items, item_data_map)
        if not pending_items:
            print("[!] Upload dibatalkan.")
            return

    if is_draft:
        drafts = load_drafts()
        for item in pending_items:
            drafts[item] = item_data_map[item]
            drafts[item]['profile'] = sel_profile
        save_drafts(drafts)
        print(f"\n{TAG_SUCCESS} {len(pending_items)} postingan disimpan ke draf lokal TikTok.")
        return

    # START SELENIUM EXECUTION
    clear_screen()
    dashboard = UploadDashboard(pending_items, item_data_map)
    profile_path = os.path.join(PROFILES_DIR, sel_profile)
    driver = setup_driver(profile_path, headless=is_headless)
    
    try:
        for i, item in enumerate(pending_items):
            dashboard.current_idx = i
            print_progress_bar(i, len(pending_items))
            data = item_data_map.get(item, {})
            sched_str = data.get('schedule_time')
            caption = data.get('caption')
            media_files = data.get('media_files', [])
            
            if choice == '3':
                res = get_datetime_input(f"Jadwal untuk {os.path.basename(item)}")
                sched_str = None if res == 'now' else res.strftime("%Y-%m-%d %H:%M")
                
            success = run_tt_scheduled_task(
                driver=driver,
                profile_name=sel_profile,
                post_path=item,
                schedule_time=sched_str,
                pre_caption=caption,
                custom_media=media_files,
                dashboard=dashboard
            )
            
            if success:
                if not sched_str and interval_mins > 0 and item != pending_items[-1]:
                    time.sleep(interval_mins * 60)
            else:
                if input(f"\n{TAG_INPUT} Terjadi kendala. Lanjut ke item berikutnya? (y/n, default y): ").lower() == 'n':
                    break
                    
        dashboard.current_idx = len(pending_items)
        dashboard.render()
        print_progress_bar(len(pending_items), len(pending_items))
        print(f"\n{TAG_SUCCESS} {CLR_BOLD}{CLR_GREEN}SELURUH PROSES POSTING TIKTOK SELESAI.{CLR_RESET}")
    finally:
        driver.quit()
        cleanup_profile(profile_path)

def main_menu():
    while True:
        clear_screen()
        options = [
            "1. 🎵 Mode Upload & Jadwal TikTok",
            "2. 🔐 Kelola Profil & Login TikTok",
            "3. 🗓️  Kelola Draf Tersimpan",
            "0. 🚪 Keluar"
        ]
        choice_idx = select_menu_option("🚀 TIKTOK AUTO-POSTER TERPADU 🚀", options)
        choice = options[choice_idx].split('.')[0].strip()
        
        if choice == '1':
            run_tiktok_post_workflow()
        elif choice == '2':
            import subprocess
            subprocess.run([sys.executable, os.path.join(CORE_DIR, "tt_login.py")])
        elif choice == '3':
            drafts = load_drafts()
            print(f"\n{TAG_INFO} Total Draf Tersimpan: {len(drafts)}")
            for k in drafts:
                print(f"  - {os.path.basename(k)}")
        elif choice == '0':
            break

        if choice != '0':
            input(f"\n{TAG_INPUT} Tekan Enter untuk kembali ke menu utama...")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TikTok Smart Scheduled Uploader")
    parser.add_argument("--profile", help="Nama profil TikTok di tt_profiles/")
    parser.add_argument("--path", help="Path folder konten")
    parser.add_argument("--limit", type=int, default=0, help="Jumlah video yang diupload")
    parser.add_argument("--mode", type=int, choices=[1, 2], help="1: Jadwalkan, 2: Post Now")
    parser.add_argument("--interval", type=int, default=0, help="Jeda antar jadwal (menit)")
    parser.add_argument("--start", help="Waktu mulai (YYYY-MM-DD HH:MM)")
    parser.add_argument("--headless", action="store_true", help="Gunakan mode headless")
    parser.add_argument("--web-preview", action="store_true", help="Tampilkan web preview interaktif")
    args = parser.parse_args()

    if not any([args.profile, args.path]):
        main_menu()
    else:
        # Menjalankan langsung via CLI mode
        run_tiktok_post_workflow(args)
