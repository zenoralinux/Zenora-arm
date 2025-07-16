import re
import requests
from datetime import datetime

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
channels = ['mrsoulb', 'Proxymaco']

def fetch_channel_html(channel_username):
    url = f'https://t.me/s/{channel_username}'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"⚠️ خطا در دریافت کانال @{channel_username}: {e}")
        return ""

def extract_configs(html_text):
    # استخراج vmess و vless
    return re.findall(r'(vmess://[^\s<"\']+|vless://[^\s<"\']+)', html_text)

def replace_fragment(config, new_fragment):
    if '#' in config:
        base = config.split('#')[0]
        return f"{base}#{new_fragment}"
    else:
        return f"{config}#{new_fragment}"

def format_batch_message(configs, new_fragment="Ch : @zenoravpn 💫📯"):
    lines = ["<b>📦 ۵ کانفیگ جدید V2Ray | @ZenoraVPN</b>\n", "<pre>"]
    for idx, config in enumerate(configs, 1):
        updated = replace_fragment(config, new_fragment)
        lines.append(f"{idx}️⃣\n{updated}\n")
    lines.append("</pre>")
    lines.append(f"\n<i>🕒 تاریخ ارسال: {datetime.now().strftime('%Y/%m/%d - %H:%M')}</i>")
    lines.append("#ZenoraVPN")
    return '\n'.join(lines)

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"❌ خطا در ارسال پیام تلگرام: {e}")
        return False

def main(batch_size=5):
    all_configs = []
    for channel in channels:
        html = fetch_channel_html(channel)
        if not html:
            continue
        configs = extract_configs(html)
        all_configs.extend(configs)

    # حذف تکراری ها با استفاده از set (در همین اجرا)
    unique_configs = list(dict.fromkeys(all_configs))  # حفظ ترتیب و حذف تکراری‌ها

    if not unique_configs:
        print("✅ هیچ کانفیگ جدیدی یافت نشد.")
        return

    batch = unique_configs[:batch_size]

    msg = format_batch_message(batch)
    if send_to_telegram(msg):
        print("✅ پیام با موفقیت ارسال شد.")
    else:
        print("❌ ارسال پیام ناموفق بود.")

if __name__ == '__main__':
    main()
