import os
import json
import subprocess
from slugify import slugify

# Yaradılacaq m3u8 fayllarını saxlayacağımız qovluq
OUTPUT_DIR = "m3u8"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# JSON faylını oxu
with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

for channel in channels:
    name = channel.get("name")
    url = channel.get("url")
    slug = slugify(name)
    output_path = os.path.join(OUTPUT_DIR, f"{slug}.m3u8")

    try:
        print(f"[+] Alınır: {name} → {url}")
        # yt-dlp ilə canlı yayım linkini əldə et
        result = subprocess.run(
            [
                "yt-dlp",
                "-g",
                url
            ],
            capture_output=True,
            text=True
        )

        stream_url = result.stdout.strip()

        if stream_url:
            with open(output_path, "w", encoding="utf-8") as m3u8_file:
                m3u8_file.write("#EXTM3U\n")
                m3u8_file.write("#EXT-X-VERSION:3\n")
                m3u8_file.write("#EXT-X-STREAM-INF:BANDWIDTH=800000\n")
                m3u8_file.write(f"{stream_url}\n")
            print(f"[✔] Yazıldı: {output_path}")
        else:
            print(f"[!] Stream tapılmadı: {name}")

    except Exception as e:
        print(f"[✘] Xəta baş verdi: {name} → {e}")
