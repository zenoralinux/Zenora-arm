import re
import requests
from datetime import datetime, timedelta

BOT_TOKEN = '7650919465:AAGDm2FtgRdjuEVclSlsEeUNaGgngcXMrCI'
CHAT_ID = '@zenoravpn'
channels = ['@Alpha_V2ray_Iran','@proxystore11','@WarV2Ray','@Farah_VPN','@iMTProto','@DALTON_PING','@anty_filter','@PASARGAD_V2rayNG','@xixv2ray']

def fetch_channel_html(channel_username):
    url = f'https://t.me/s/{channel_username.lstrip("@")}'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"⚠️ خطا در دریافت کانال @{channel_username}: {e}")
        return ""

def extract_recent_configs(html_text, hours=4):
    # الگوی پست‌ها در تلگرام (نمونه): 
    # <time datetime="2025-07-16T09:15:00+00:00" class="time" title="2025-07-16T09:15:00+00:00">9:15</time>
    # یا مشابه
    # پس ابتدا همه پست‌ها رو میگیریم به صورت (زمان، محتوای html پست)
    
    # پست‌ها معمولاً div با کلاس message هستند:
    posts = re.findall(r'(<div class="tgme_widget_message\b.*?</div>\s*</div>)', html_text, re.DOTALL)
    
    recent_configs = []
    now = datetime.utcnow()
    time_limit = now - timedelta(hours=hours)

    for post_html in posts:
        # استخراج زمان پست
        time_match = re.search(r'<time datetime="([^"]+)"', post_html)
        if not time_match:
            continue
        post_time_str = time_match.group(1)
        try:
            post_time = datetime.fromisoformat(post_time_str.replace('Z', '+00:00')).replace(tzinfo=None)  # بدون timezone
        except Exception:
            continue
        
        if post_time < time_limit:
            # این پست قدیمی‌تر از ۴ ساعت است، ردش کن
            continue
        
        # حالا کانفیگ‌ها رو داخل این پست استخراج کن
        configs = re.findall(r'(vmess://[^\s<"\']+|vless://[^\s<"\']+)', post_html)
        recent_configs.extend(configs)
    
    return recent_configs

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
        configs = extract_recent_configs(html, hours=4)
        all_configs.extend(configs)

    # حذف تکراری‌ها در همین اجرا
    unique_configs = list(dict.fromkeys(all_configs))

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
