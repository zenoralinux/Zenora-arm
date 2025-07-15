import re
import requests
import html
import sqlite3
import os
from datetime import datetime

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
DB_PATH = 'configs.db'
channels = ['mrsoulb', 'Proxymaco']

MAX_DB_SIZE_MB = 50  # محدودیت حجم فایل دیتابیس

def init_db():
    if os.path.exists(DB_PATH):
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        if size_mb > MAX_DB_SIZE_MB:
            print(f"⚠️ حجم فایل دیتابیس {size_mb:.2f} مگابایت است. حذف و ایجاد مجدد...")
            os.remove(DB_PATH)
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("SELECT name FROM sqlite_master LIMIT 1;")
                return conn
            except sqlite3.DatabaseError:
                print("⚠️ فایل دیتابیس خراب است. حذف و ایجاد مجدد...")
                os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config TEXT UNIQUE,
            added_at DATETIME,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def fetch_channel_html(channel_username):
    url = f'https://t.me/s/{channel_username}'
    r = requests.get(url)
    if r.status_code == 200:
        return r.text
    else:
        print(f"⚠️ دریافت کانال @{channel_username} با خطا مواجه شد: {r.status_code}")
        return ""

def extract_configs(html_text):
    return re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', html_text)

def save_new_configs(conn, configs):
    cur = conn.cursor()
    now = datetime.utcnow()
    for c in configs:
        try:
            cur.execute("INSERT INTO configs (config, added_at) VALUES (?, ?)", (c, now))
        except sqlite3.IntegrityError:
            pass  # کانفیگ تکراری

    conn.commit()

def get_unsent_batch(conn, batch_size=5):
    cur = conn.cursor()
    cur.execute("SELECT id, config FROM configs WHERE sent = 0 ORDER BY added_at ASC LIMIT ?", (batch_size,))
    return cur.fetchall()

def mark_as_sent(conn, ids):
    cur = conn.cursor()
    cur.executemany("UPDATE configs SET sent = 1 WHERE id = ?", [(i,) for i in ids])
    conn.commit()

def format_batch_message(batch, base_index=1):
    lines = ["📦 <b>۵ کانفیگ جدید V2Ray</b> | <b>@ZenoraVPN</b>\n"]
    for idx, (_, config) in enumerate(batch):
        tag = f"Config #{base_index + idx}"
        title = f"🔐 <b>{'VMESS' if config.startswith('vmess') else 'VLESS'} - {tag}</b>"
        lines.append(f"{title}\n<code>{html.escape(config)}</code>\n")
    lines.append(f"🕒 تاریخ: {datetime.now().strftime('%Y/%m/%d - %H:%M')}\n#ZenoraVPN")
    return '\n'.join(lines)

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
        print(f"❌ ارسال پیام با خطا مواجه شد: {r.text}")
        return False
    return True

def main():
    conn = init_db()

    for channel in channels:
        html_text = fetch_channel_html(channel)
        new_configs = extract_configs(html_text)
        save_new_configs(conn, new_configs)

    batch = get_unsent_batch(conn, 5)
    if not batch:
        print("✅ هیچ کانفیگ جدیدی برای ارسال وجود ندارد.")
        return

    msg = format_batch_message(batch)
    if send_to_telegram(msg):
        mark_as_sent(conn, [row[0] for row in batch])
        print("✅ پیام ارسال و کانفیگ‌ها علامت‌گذاری شدند.")
    else:
        print("❌ ارسال پیام ناموفق بود.")

    conn.close()

if __name__ == '__main__':
    main()
