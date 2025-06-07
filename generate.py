import json
import subprocess
from slugify import slugify

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

m3u = "#EXTM3U\n#EXT-X-VERSION:3\n"

for ch in channels:
    url = ch["url"]
    name = ch["name"]
    group = ch.get("group", "General")
    try:
        stream_url = subprocess.check_output(
            ["yt-dlp", "-g", url], text=True).strip()
        m3u += f'#EXTINF:-1 group-title="{group}",{name}\n{stream_url}\n'
    except subprocess.CalledProcessError:
        print(f"[!] Skipped: {name} (stream not available)")

filename = "output.m3u8"
with open(filename, "w", encoding="utf-8") as f:
    f.write(m3u)

print(f"[*] M3U8 file generated: {filename}")
