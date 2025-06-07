import subprocess
import json

INPUT_FILE = "channels.txt"
OUTPUT_FILE = "playlist.m3u"

def get_stream_url(youtube_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-j", youtube_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
        data = json.loads(result.stdout.decode())
        return data.get("url")
    except Exception as e:
        print(f"Xəta: {youtube_url} → {e}")
        return None

def generate_m3u():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        channels = [line.strip().split("|") for line in f if "|" in line]

    m3u_lines = ["#EXTM3U\n"]

    for name, url in channels:
        stream_url = get_stream_url(url)
        if stream_url:
            m3u_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="DIZILER",{name}')
            m3u_lines.append(stream_url + "\n")
        else:
            print(f"Skip: {name}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print("✅ Playlist yaradıldı:", OUTPUT_FILE)

if __name__ == "__main__":
    generate_m3u()
