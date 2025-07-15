import re
import requests
import html
import time
import sqlite3
from datetime import datetime

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
DB_PATH = 'configs.db'
channels = ['mrsoulb', 'Proxymaco']

def init_db():
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
    return r.text if r.status_code == 200 else ""

def extract_configs(html_text):
    return re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', html_text)

def save_new_configs(conn, configs):
    cur = conn.cursor()
    now = datetime.utcnow()
    for c in configs:
        try:
            cur.execute("INSERT INTO configs (config, added_at) VALUES (?, ?)", (c, now))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

def get_unsent_batches(conn, batch_size=5):
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
        if config.startswith("vmess://"):
            title = f"🔐 <b>VMESS - {tag}</b>"
        else:
            title = f"🔐 <b>VLESS - {tag}</b>"
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
        print(f"❌ Send failed: {r.text}")
        return False
    return True

def main():
    conn = init_db()

    # Step 1: Fetch configs from channels
    for channel in channels:
        html_text = fetch_channel_html(channel)
        new_configs = extract_configs(html_text)
        save_new_configs(conn, new_configs)

    # Step 2: Loop and send unsent batches every 15 minutes
    index = 0
    while True:
        batch = get_unsent_batches(conn, 5)
        if not batch:
            print("✅ All configs sent.")
            break

        msg = format_batch_message(batch, base_index=index*5 + 1)
        if send_to_telegram(msg):
            mark_as_sent(conn, [row[0] for row in batch])
            index += 1
            if get_unsent_batches(conn, 1):  # اگر هنوز هست برای دفعه بعد
                print("⏳ Waiting 15 minutes...")
                time.sleep(900)  # 15 minutes
        else:
            print("❌ Failed to send. Exiting.")
            break

    conn.close()

if __name__ == '__main__':
    main()
