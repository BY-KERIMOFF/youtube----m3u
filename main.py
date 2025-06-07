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
        group = ch.get("group", "GENEL").strip().upper()

        if not url:
            continue

        filename = sanitize_filename(name) + ".m3u8"
        filepath = os.path.join(output_dir, filename)

        # BANDWIDTH dəyərləri nümunə olaraq (istəyə görə dəyişə bilər)
        bandwidths = [2096000, 796000]

        with open(filepath, "w", encoding="utf-8") as out:
            out.write("#EXTM3U\n")
            out.write("#EXT-X-VERSION:3\n")
            for bw in bandwidths:
                out.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bw}\n")
                out.write(f"{url}?bandwidth={int(bw/1000)}\n")

        print(f"{filename} yaradıldı.")

if __name__ == "__main__":
    main()
