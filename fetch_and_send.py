import re
import requests
import html

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'

# فایل لوکال برای جلوگیری از تکرار
SEEN_FILE = 'sent_configs.txt'

def load_seen():
    try:
        with open(SEEN_FILE, 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        f.write('\n'.join(seen))

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"Error sending message: {r.text}")

def extract_configs(text):
    configs = re.findall(r'(vmess://[^\s]+|vless://[^\s]+)', text)
    return configs

def fetch_channel(channel_username):
    # هشدار: این روش از scraping صفحه عمومی tgstat یا rss feed استفاده می‌کند
    url = f'https://t.me/s/{channel_username}'
    r = requests.get(url)
    if r.status_code == 200:
        return r.text
    else:
        print(f"Failed to fetch {channel_username}")
        return ""

def main():
    channels = ['mrsoulb', 'Proxymaco']
    seen = load_seen()
    new_seen = set(seen)

    for channel in channels:
        html_text = fetch_channel(channel)
        matches = extract_configs(html_text)
        for conf in matches:
            if conf not in seen:
                msg = f"<b>🔐 New Config Found</b>\n<code>{html.escape(conf)}</code>"
                send_to_telegram(msg)
                new_seen.add(conf)

    save_seen(new_seen)

if __name__ == "__main__":
    main()
