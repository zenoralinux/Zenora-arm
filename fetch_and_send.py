import requests
import re
import time
import hashlib
from datetime import datetime

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
    return re.findall(r'(vmess://[^\s<]+|vless://[^\s<]+)', html_text)

def hash_config(config):
    return hashlib.sha256(config.encode()).hexdigest()

def clean_and_tag_config(config):
    config = re.sub(r'#.*', '', config)
    return config + '#Ch : @zenoravpn 💫📯'

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    for ch in escape_chars:
        text = text.replace(ch, '\\' + ch)
    return text

def format_batch_message(batch):
    lines = ["📦 ۵ کانفیگ جدید V2Ray | @ZenoraVPN\n"]
    for config in batch:
        escaped = escape_markdown(config)
        lines.append('>' + escaped)
    lines.append(f"\n🕒 تاریخ: {escape_markdown(datetime.now().strftime('%Y/%m/%d - %H:%M'))}")
    lines.append("#ZenoraVPN")
    return '\n'.join(lines)

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True
    }
    r = requests.post(url, data=payload)
    print(f"Telegram response status: {r.status_code}")
    print(f"Telegram response text: {r.text}")
    if r.status_code != 200:
        print(f"❌ Failed to send message: {r.text}")
    else:
        print("✅ Message sent successfully")

def main():
    seen = load_seen()
    new_seen = set(seen)
    all_new_configs = []

    for channel in channels:
        html_text = fetch_channel_html(channel)
        configs = extract_recent_configs(html_text)
        for c in configs:
            tagged = clean_and_tag_config(c)
            h = hash_config(tagged)
            if h not in seen:
                all_new_configs.append(tagged)
                new_seen.add(h)

    batches = [all_new_configs[i:i + 5] for i in range(0, len(all_new_configs), 5)]

    print(f"✅ Found {len(all_new_configs)} new configs.")
    for i, batch in enumerate(batches):
        msg = format_batch_message(batch)
        send_to_telegram(msg)
        if i < len(batches) - 1:
            print("⏳ Waiting 15 minutes for next batch...")
            time.sleep(900)

    save_seen(new_seen)
    print("✅ Done. Waiting for next scheduled run.")

if __name__ == '__main__':
    main()
