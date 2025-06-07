import subprocess
import json
import os

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

output_dir = "m3u8"
os.makedirs(output_dir, exist_ok=True)

for ch in channels:
    safe_name = ch["name"].lower().replace(" ", "_")  # sadələşdir
    filename = os.path.join(output_dir, f"{safe_name}.m3u8")

    # yt-dlp ilə real m3u8 linki al
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", ch["url"]],
            capture_output=True, text=True, check=True
        )
        streams = result.stdout.strip().split('\n')
        # Birinci xətt əsas streaming link olur
        m3u8_url = streams[0] if streams else ""

        with open(filename, "w", encoding="utf-8") as f_out:
            f_out.write("#EXTM3U\n")
            f_out.write("#EXT-X-VERSION:3\n")
            f_out.write(f"#EXT-X-STREAM-INF:BANDWIDTH=2096000\n")
            f_out.write(m3u8_url + "\n")

        print(f"{ch['name']} üçün m3u8 yaradıldı")
    except Exception as e:
        print(f"{ch['name']} üçün xəta: {e}")
