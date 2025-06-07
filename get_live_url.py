import requests
import re
import json

URL = "https://www.youtube.com/@Adanali/live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

resp = requests.get(URL, headers=HEADERS)
html = resp.text

# YouTube səhifəsində 'ytInitialData' adlı JavaScript dəyişəni var,
# içindən canlı yayımın video ID-sini çıxarırıq.

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

# JSON içində canlı yayım video id-sini tapmağa çalışırıq:
try:
    # "videoRenderer" obyektində canlı video olur
    contents = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]

    video_id = None
    for section in contents:
        items = section.get("itemSectionRenderer", {}).get("contents", [])
        for item in items:
            video_renderer = item.get("videoRenderer")
            if video_renderer:
                video_id = video_renderer.get("videoId")
                if video_id:
                    break
        if video_id:
            break

    if not video_id:
        print("🚫 Canlı yayım tapılmadı.")
        exit(1)

    print(f"https://www.youtube.com/watch?v={video_id}")

except Exception as e:
    print("🚫 Canlı yayım tapılmadı:", e)
    exit(1)
