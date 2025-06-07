import os
import subprocess

CHANNELS = {
    "SHOW MAX": "https://www.youtube.com/watch?v=ouuCjEjyKVI",
    "YASAK ELMA": "https://www.youtube.com/watch?v=35Pf54Be3lo",
    "SEKSENLER": "https://www.youtube.com/watch?v=8-uHZ4CCb-E",
    "ASKI MEMMU": "https://www.youtube.com/@AskMemnuKanalD",
    "GULSAH FILM": "https://www.youtube.com/watch?v=hfx8H7YrmTw",
    "CENNET MAHALLESI": "https://www.youtube.com/watch?v=XXXXXXX",  # dəyiş
    "MUHTESEM YUZYIL": "https://www.youtube.com/watch?v=4HZW53S0bv8",
    "ADINI FERIHA KOYDUM": "https://www.youtube.com/watch?v=PikNiUKUGM4",
    "MEDCEZIR": "https://www.youtube.com/watch?v=MLUGblGpm8A",
    "YESIL DENIZ": "https://www.youtube.com/watch?v=YyZlgKdiJP0",
    "NOSTALIJ TRT": "https://www.youtube.com/watch?v=5CMiYHTZX8o",
    "ALEMIN KRALI": "https://www.youtube.com/watch?v=avDRwKKjeSI",
    "SIHIRLI ANNEM": "https://www.youtube.com/watch?v=KCejwr4z7NQ",
    "YEDI NUMARA": "https://www.youtube.com/watch?v=rS5dHYQsSxs",
    "KIRALIK ASK": "https://www.youtube.com/watch?v=n3_DG0Sv0kw",
    "SOZ": "https://www.youtube.com/watch?v=2TPSPnQwy34",
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
