import os
import subprocess

CHANNELS = {
    "Adanali": "https://www.youtube.com/@AvrupaYakasi/live"
}

OUTPUT_DIR = "output"
TOKEN_FILE = "token.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"[!] Xəta: '{TOKEN_FILE}' tapılmadı!")
        return None

def get_stream_url(youtube_url, token):
    if not token:
        print("[!] Token mövcud deyil!")
        return None
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--add-header", f"Authorization: Bearer {token}",
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
    token = get_token()
    for name, url in CHANNELS.items():
        print(f"[+] Yoxlanır: {name}")
        stream_url = get_stream_url(url, token)
        if stream_url:
            save_m3u(name, stream_url)
        else:
            print(f"[✘] Uğursuz: {name}\n")

if __name__ == "__main__":
    main()
