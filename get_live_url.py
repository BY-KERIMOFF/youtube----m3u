import requests
import re
import json

def deep_search(d, key):
    if isinstance(d, dict):
        if key in d:
            yield d[key]
        for v in d.values():
            yield from deep_search(v, key)
    elif isinstance(d, list):
        for item in d:
            yield from deep_search(item, key)

URL = "https://www.youtube.com/@Adanali/live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

resp = requests.get(URL, headers=HEADERS)
html = resp.text

match = re.search(r"ytInitialData\s*=\s*({.*?});</script>", html, re.DOTALL)
if not match:
    print("🚫 ytInitialData tapılmadı.")
    exit(1)

data_json = match.group(1)

try:
    data = json.loads(data_json)
except Exception as e:
    print("🚫 JSON parsing xətası:", e)
    exit(1)

video_ids = set()
for videoRenderer in deep_search(data, "videoRenderer"):
    if isinstance(videoRenderer, dict):
        video_id = videoRenderer.get("videoId")
        if video_id:
            video_ids.add(video_id)

if not video_ids:
    print("🚫 Canlı yayım tapılmadı.")
    exit(1)

# Birinci video ID-ni seçirik (ümumiyyətlə canlı yayım bir olur)
video_id = video_ids.pop()
print(f"https://www.youtube.com/watch?v={video_id}")
