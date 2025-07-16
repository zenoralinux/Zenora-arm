import re
import requests
import sqlite3
import os
import base64
from urllib.parse import urlparse
from datetime import datetime, timedelta
import json

# ============ تنظیمات ============
BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
CHANNELS = ['mrsoulb', 'Proxymaco']
DB_PATH = 'configs.db'
MAX_DB_SIZE_MB = 50
FRAGMENT_NAME = "Ch : @zenoravpn 💫📯"

# ============ آماده‌سازی دیتابیس ============
def init_db():
    if os.path.exists(DB_PATH):
        try:
            size = os.path.getsize(DB_PATH) / (1024 * 1024)
            if size > MAX_DB_SIZE_MB:
                print("⚠️ حجم دیتابیس بیشتر از ۵۰MB است. حذف شد.")
                os.remove(DB_PATH)
            else:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("SELECT name FROM sqlite_master LIMIT 1;")
                ensure_signature_column(conn)
                return conn
        except Exception:
            print("⚠️ دیتابیس خراب بود. حذف شد.")
            os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config TEXT,
            signature TEXT UNIQUE,
            added_at DATETIME,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def ensure_signature_column(conn):
    try:
        conn.execute("ALTER TABLE configs ADD COLUMN signature TEXT UNIQUE")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# ============ استخراج کلید یونیک ============
def extract_key_info(config):
    if config.startswith("vmess://"):
        try:
            payload = config.split("vmess://")[1]
            padded = payload + '=' * (-len(payload) % 4)
            decoded = base64.b64decode(padded).decode()
            data = json.loads(decoded)
            return f"vmess|{data.get('add')}|{data.get('port')}|{data.get('id')}"
        except Exception:
            return None
    elif config.startswith("vless://"):
        try:
            url = urlparse(config)
            return f"vless|{url.hostname}|{url.port}|{url.username}"
        except Exception:
            return None
    return None

# ============ خواندن کانال‌ها ============
def fetch_channel_html(channel):
    try:
        url = f"https://t.me/s/{channel}"
        r = requests.get(url)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def extract_configs(text):
    return re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', text)

# ============ ذخیره‌سازی ============
def save_new_configs(conn, configs):
    cur = conn.cursor()
    now = datetime.utcnow()
    for cfg in configs:
        sig = extract_key_info(cfg)
        if sig:
            try:
                cur.execute(
                    "INSERT INTO configs (config, signature, added_at) VALUES (?, ?, ?)",
                    (cfg, sig, now)
                )
            except sqlite3.IntegrityError:
                pass
    conn.commit()

def delete_old_configs(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM configs WHERE added_at < datetime('now', '-1 day')")
    conn.commit()

def get_unsent_batch(conn, batch_size=10):
    cur = conn.cursor()
    cur.execute("SELECT id, config FROM configs WHERE sent = 0 ORDER BY added_at ASC LIMIT ?", (batch_size,))
    return cur.fetchall()

def mark_as_sent(conn, ids):
    cur = conn.cursor()
    cur.executemany("UPDATE configs SET sent = 1 WHERE id = ?", [(i,) for i in ids])
    conn.commit()

# ============ آماده‌سازی پیام ============
def replace_fragment(cfg, new_fragment):
    base = cfg.split('#')[0]
    return f"{base}#{new_fragment}"

def format_message(batch):
    lines = ["<b>📦 ۱۰ کانفیگ جدید V2Ray | @ZenoraVPN</b>\n", "<pre>"]
    for _, cfg in batch:
        updated = replace_fragment(cfg, FRAGMENT_NAME)
        lines.append(updated)
    lines.append("</pre>")
    lines.append(f"\n<i>🕒 تاریخ: {datetime.now().strftime('%Y/%m/%d - %H:%M')}</i>")
    lines.append("#ZenoraVPN")
    return '\n'.join(lines)

# ============ ارسال پیام ============
def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("✅ پیام با موفقیت ارسال شد.")
        return True
    else:
        print(f"❌ ارسال پیام ناموفق: {r.text}")
        return False

# ============ اجرای کلی ============
def main():
    conn = init_db()
    delete_old_configs(conn)

    for ch in CHANNELS:
        html = fetch_channel_html(ch)
        configs = extract_configs(html)
        save_new_configs(conn, configs)

    batch = get_unsent_batch(conn, 10)
    if not batch:
        print("✅ کانفیگ جدیدی برای ارسال نیست.")
        return

    msg = format_message(batch)
    if send_to_telegram(msg):
        mark_as_sent(conn, [row[0] for row in batch])
    conn.close()

if __name__ == "__main__":
    main()
