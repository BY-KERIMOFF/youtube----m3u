import os
import subprocess

CHANNELS = {
    "Adanali": "https://www.youtube.com/@AvrupaYakasi/live"
}

COOKIES_FILE = "cookies.txt"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_stream_url(youtube_url):
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--cookies", COOKIES_FILE,
                "-g", youtube_url
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[!] Xəta: {youtube_url} → {result.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        print(f"[!] TIMEOUT: {youtube_url}")
        return None

def save_m3u(channel_name, stream_url):
    filename = f"{channel_name.replace(' ', '_').lower()}.m3u"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1,{channel_name}\n")
        f.write(f"{stream_url}\n")
    print(f"[✔] Yazıldı: {filepath}")

def main():
    for name, url in CHANNELS.items():
        print(f"[+] Yoxlanır: {name}")
        stream_url = get_stream_url(url)
        if stream_url:
            save_m3u(name, stream_url)
        else:
            print(f"[✘] Uğursuz: {name}\n")

if __name__ == "__main__":
    main()
