import requests
import re

CHANNEL_LIVE_URL = "https://www.youtube.com/@Adanali/live"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(CHANNEL_LIVE_URL, headers=headers)
html = response.text

match = re.search(r'"url":"\\/watch\\?v=([\w-]{11})"', html)
if not match:
    match = re.search(r'"url":"/watch?v=([\w-]{11})"', html)

if match:
    video_id = match.group(1)
    print(f"https://www.youtube.com/watch?v={video_id}")
else:
    print("🚫 Canlı yayım tapılmadı.")
