import json
import os
import re

def sanitize_filename(name):
    return re.sub(r'[^\w\-_.]', '_', name.strip())

def main():
    input_file = "youtube_channels.json"
    output_dir = "m3u8_channels"
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    for ch in channels:
        name = ch.get("name", "No_Name").strip()
        url = ch.get("url", "").strip()

        if not url:
            continue

        filename = sanitize_filename(name) + ".m3u8"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as out:
            out.write("#EXTM3U\n")
            out.write("#EXT-X-VERSION:3\n")
            out.write("#EXT-X-STREAM-INF:BANDWIDTH=2096000\n")
            out.write(f"{url}\n")
            out.write("#EXT-X-STREAM-INF:BANDWIDTH=796000\n")
            out.write(f"{url}\n")

        print(f"{filename} yaradıldı.")

if __name__ == "__main__":
    main()
