import json
import subprocess
import os

# Giriş JSON faylı
INPUT_FILE = "channels.json"
# Çıxış qovluğu
OUTPUT_DIR = "m3u8"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    channels = json.load(f)

for ch in channels:
    name = ch.get("name", "Unknown")
    url = ch.get("url")
    group = ch.get("group", "GENERIC")

    if not url:
        print(f"[SKIP] URL yoxdur: {name}")
        continue

    safe_name = name.lower().replace(" ", "_").replace("/", "_")
    filename = os.path.join(OUTPUT_DIR, f"{safe_name}.m3u8")

    try:
        result = subprocess.run(
            ["yt-dlp", "-g", url],
            capture_output=True,
            text=True,
            check=True
        )
        m3u8_url = result.stdout.strip().split("\n")[0]

        with open(filename, "w", encoding="utf-8") as out:
            out.write("#EXTM3U\n")
            out.write("#EXT-X-VERSION:3\n")
            out.write(f"#EXTINF:-1 tvg-name=\"{name}\" group-title=\"{group}\",{name}\n")
            out.write(m3u8_url + "\n")

        print(f"[OK] {name} yazıldı → {filename}")

    except subprocess.CalledProcessError as e:
        print(f"[Xəta] {name}: yt-dlp uğursuz oldu. {e.stderr.strip()}")
    except Exception as e:
        print(f"[Xəta] {name}: {str(e)}")
