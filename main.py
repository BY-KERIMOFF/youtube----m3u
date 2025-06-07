import subprocess
import json

# İstədiyin YouTube canlı yayım linkini bura yaz
YOUTUBE_URL = "https://www.youtube.com/watch?v=5qap5aO4i9A"  # Lofi Girl

OUTPUT_FILE = "youtube_live.m3u"

def get_m3u8_link(url):
    try:
        print("Canlı yayım analiz edilir...")
        cmd = ['yt-dlp', '-J', url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("Xəta:", result.stderr)
            return None

        data = json.loads(result.stdout)
        for format in data.get("formats", []):
            if format.get("ext") == "mp4" and format.get("protocol") == "m3u8":
                return format["url"]

        print("m3u8 link tapılmadı.")
        return None

    except Exception as e:
        print("Xəta:", e)
        return None

def write_m3u_file(stream_url):
    with open(OUTPUT_FILE, "w") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1,YouTube Live Stream\n")
        f.write(f"{stream_url}\n")
    print(f"{OUTPUT_FILE} yaradıldı və link əlavə olundu.")

if __name__ == "__main__":
    m3u8_link = get_m3u8_link(YOUTUBE_URL)
    if m3u8_link:
        write_m3u_file(m3u8_link)
    else:
        print("m3u8 link əldə edilə bilmədi.")
