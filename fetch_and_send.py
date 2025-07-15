import re
import requests
import sqlite3
import os
import base64
from urllib.parse import urlparse, unquote
from datetime import datetime, timedelta

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
DB_PATH = 'configs.db'
channels = ['mrsoulb', 'Proxymaco']
MAX_DB_SIZE_MB = 50

# ---------------- DB Init ----------------
def init_db():
    if os.path.exists(DB_PATH):
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        if size_mb > MAX_DB_SIZE_MB:
            print("⚠️ حجم دیتابیس زیاد است. حذف شد.")
            os.remove(DB_PATH)
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("SELECT name FROM sqlite_master LIMIT 1;")
                return conn
            except sqlite3.DatabaseError:
                print("⚠️ دیتابیس خراب بود. حذف شد.")
                os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config TEXT,
            signature TEXT UNIQUE,
            added_at DATETIME,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

# ---------------- کانفیگ آنالیز و کلید ----------------
def extract_key_info(config):
    if config.startswith("vless://") or config.startswith("vmess://"):
        proto = config.split("://")[0]

        if proto == "vmess":
            try:
                payload = config.split("vmess://")[1]
                padded = payload + '=' * (-len(payload) % 4)
                decoded = base64.b64decode(padded).decode()
                if decoded.strip().startswith('{'):
                    import json
                    data = json.loads(decoded)
                    return f"{proto}|{data.get('add')}|{data.get('port')}|{data.get('id')}"
            except Exception:
                return None

        elif proto == "vless":
            try:
                url = urlparse(config)
                host = url.hostname
                port = url.port
                uuid = url.username
                return f"{proto}|{host}|{port}|{uuid}"
            except Exception:
                return None
    return None

# ---------------- HTML آماده‌سازی ----------------
def replace_fragment(config, new_fragment):
    base = config.split('#')[0]
    return f"{base}#{new_fragment}"

def format_batch_message(batch):
    new_fragment = "Ch : @zenoravpn 💫📯"
    lines = ["<b>📦 ۱۰ کانفیگ جدید V2Ray | @ZenoraVPN</b>\n", "<pre>"]
    for _, config in batch:
        updated_config = replace_fragment(config, new_fragment)
        lines.append(updated_config)
    lines.append("</pre>")
    lines.append(f"\n<i>🕒 تاریخ: {datetime.now().strftime('%Y/%m/%d - %H:%M')}</i>")
    lines.append("#ZenoraVPN")
    return '\n'.join(lines)

# ---------------- دریافت کانال ----------------
def fetch_channel_html(channel_username):
    url = f'https://t.me/s/{channel_username}'
    try:
        r = requests.get(url)
        return r.text if r.status_code == 200 else ""
    except Exception as e:
        print(f"❌ خطا در دریافت کانال @{channel_username}")
        return ""

def extract_configs(html_text):
    return re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', html_text)

# ---------------- ذخیره‌سازی امن ----------------
def save_new_configs(conn, configs):
    cur = conn.cursor()
    now = datetime.utcnow()
    for c in configs:
        sig = extract_key_info(c)
        if sig:
            try:
                cur.execute("INSERT INTO configs (config, signature, added_at) VALUES (?, ?, ?)", (c, sig, now))
            except sqlite3.IntegrityError:
                pass
    conn.commit()

def delete_old_configs(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM configs WHERE added_at < datetime('now', '-1 day')")
    conn.commit()

# ---------------- پردازش ارسال ----------------
def get_unsent_batch(conn, batch_size=10):
    cur = conn.cursor()
    cur.execute("SELECT id, config FROM configs WHERE sent = 0 ORDER BY added_at ASC LIMIT ?", (batch_size,))
    return cur.fetchall()

def mark_as_sent(conn, ids):
    cur = conn.cursor()
    cur.executemany("UPDATE configs SET sent = 1 WHERE id = ?", [(i,) for i in ids])
    conn.commit()

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"❌ ارسال پیام ناموفق: {r.text}")
        return False
    return True

# ---------------- main ----------------
def main():
    conn = init_db()
    delete_old_configs(conn)

    for channel in channels:
        html = fetch_channel_html(channel)
        configs = extract_configs(html)
        save_new_configs(conn, configs)

    batch = get_unsent_batch(conn, 10)
    if not batch:
        print("✅ هیچ کانفیگ جدیدی برای ارسال وجود ندارد.")
        return

    msg = format_batch_message(batch)
    if send_to_telegram(msg):
        mark_as_sent(conn, [row[0] for row in batch])
        print("✅ پیام ارسال شد.")
    else:
        print("❌ ارسال پیام با شکست مواجه شد.")

    conn.close()

if __name__ == '__main__':
    main()
