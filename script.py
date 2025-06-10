import subprocess
from datetime import datetime

youtube_links = {
    "Space TV": "https://www.youtube.com/watch?v=lf1NxAexRAE"
}

cookie_file = "youtube_cookies.txt"  # eyni qovluqda saxla

m3u8_content = "#EXTM3U\n"
stream_count = 0

for name, url in youtube_links.items():
    print(f"➡️ {name} üçün link çıxarılır...")
    try:
        stream_url = subprocess.check_output([
            "yt-dlp",
            "--cookies", cookie_file,
            "-g", url
        ]).decode().strip()
        print(f"✅ {name} link: {stream_url}")
        m3u8_content += f"#EXTINF:-1,{name}\n{stream_url}\n"
        stream_count += 1
    except Exception as e:
        print(f"❌ {name} üçün çıxarış mümkün olmadı: {e}")

if stream_count > 0:
    with open("live_channels.m3u8", "w") as f:
        f.write(m3u8_content)
    print(f"[✓] {stream_count} stream link fayla yazıldı.")
else:
    print("[X] Heç bir stream çıxmadı. Fayl yaradılmadı.")
