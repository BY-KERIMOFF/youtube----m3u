import subprocess
from datetime import datetime

# Buraya istədiyin YouTube canlı yayımlarını əlavə et
youtube_links = {
    "Space TV": "https://www.youtube.com/watch?v=lf1NxAexRAE"
}

m3u8_content = "#EXTM3U\n"

for name, url in youtube_links.items():
    try:
        stream_url = subprocess.check_output(["yt-dlp", "-g", "-f", "best", url]).decode().strip()
        m3u8_content += f"#EXTINF:-1,{name}\n{stream_url}\n"
    except Exception as e:
        print(f"[X] {name} üçün link çıxarıla bilmədi: {e}")

with open("live_channels.m3u8", "w") as f:
    f.write(m3u8_content)

print(f"[✓] {datetime.now()} tarixində m3u8 faylı yeniləndi.")
