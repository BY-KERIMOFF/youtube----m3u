import json
from slugify import slugify
from pathlib import Path

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

Path("m3u8").mkdir(exist_ok=True)

for channel in channels:
    name = channel["name"]
    group = channel["group"]
    url = channel["url"]

    filename = slugify(name) + ".m3u8"
    with open(f"m3u8/{filename}", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write(f'#EXTINF:-1 group-title="{group}",{name}\n')
        f.write(f"{url}\n")
