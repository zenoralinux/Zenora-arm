import requests
import re
import html
import time
from datetime import datetime, timedelta

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
SEEN_FILE = 'sent_configs.txt'

channels = ['mrsoulb', 'Proxymaco']

def load_seen():
    try:
        with open(SEEN_FILE, 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        f.write('\n'.join(seen))

def fetch_channel_html(channel_username):
    url = f'https://t.me/s/{channel_username}'
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def extract_recent_configs(html_text):
    recent_configs = []
    now = datetime.utcnow()
    yesterday = now - timedelta(hours=24)

    # تاریخ‌ها در HTML کانال نیستند. پس اگر scraping ساده می‌کنی، فرض کن همه اخیرند.
    # اگر از Telethon استفاده شود، می‌توان زمان دقیق داشت.
    configs = re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', html_text)
    return configs

def format_batch_message(batch, base_index=1):
    lines = ["📦 <b>۵ کانفیگ جدید V2Ray</b> | <b>@ZenoraVPN</b>\n"]
    for idx, config in enumerate(batch):
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
        print(f"❌ Failed to send message: {r.text}")
    else:
        print("✅ Message sent successfully")

def main():
    seen = load_seen()
    new_seen = set(seen)
    all_new_configs = []

    # استخراج کانفیگ‌ها
    for channel in channels:
        html_text = fetch_channel_html(channel)
        configs = extract_recent_configs(html_text)
        for c in configs:
            if c not in seen:
                all_new_configs.append(c)
                new_seen.add(c)

    # دسته‌بندی به گروه‌های ۵تایی
    batches = [all_new_configs[i:i + 5] for i in range(0, len(all_new_configs), 5)]

    print(f"Found {len(all_new_configs)} new configs in total.")
    for i, batch in enumerate(batches):
        msg = format_batch_message(batch, base_index=i*5 + 1)
        send_to_telegram(msg)
        print(f"Sleeping 15 minutes before sending next batch...")
        if i < len(batches) - 1:
            time.sleep(900)  # 15 دقیقه بین هر پست

    save_seen(new_seen)

if __name__ == '__main__':
    main()
