import os
import subprocess

CHANNELS = {
    "Kurtlar Vadisi": "https://www.youtube.com/@KurtlarVadisiOfficial",
    "Kurtlar Vadisi Pusu": "https://www.youtube.com/channel/UCz1UfNp9VFp9R1HEFn5PY5A",
    "SHOW MAX": "https://www.youtube.com/watch?v=ouuCjEjyKVI",
    "YASAK ELMA": "https://www.youtube.com/watch?v=35Pf54Be3lo",
    "SEKSENLER": "https://www.youtube.com/watch?v=8-uHZ4CCb-E",
    "ASKI MEMMU": "https://www.youtube.com/@AskMemnuKanalD",
    "GULSAH FILM": "https://www.youtube.com/watch?v=hfx8H7YrmTw",
    "CENNET MAHALLESI": "https://www.youtube.com/watch?v=XXXXXXX",
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
    "Show TV": "https://www.youtube.com/watch?v=ouuCjEjyKVI",
    "Star TV": "https://www.youtube.com/watch?v=6wHAK439FDI",
    "Kanal D": "https://www.youtube.com/watch?v=6wHAK439FDI",
    "atv": "https://www.youtube.com/channel/UCUVZ7T_kwkxDOGFcDlFI-hg/live",
    "TRT Haber": "https://www.youtube.com/watch?v=qj5k4yqH6nk",
    "A Haber": "https://www.youtube.com/watch?v=n8ZzARa5IjQ",
    "NTV": "https://www.youtube.com/watch?v=lMfRYzZ3XG8",
    "CNN Türk": "https://www.youtube.com/watch?v=VXMR3YQ7W3s",
    "Habertürk TV": "https://www.youtube.com/watch?v=RNVNlJSUFoE",
    "Haber Global TV": "https://www.youtube.com/watch?v=6g_DvD8e2T0",
    "Yasak Elma": "https://www.youtube.com/@YasakElmaDizi",
    "Aşk-ı Memnu": "https://www.youtube.com/@AskMemnuKanalD",
    "Muhteşem Yüzyıl": "https://www.youtube.com/@MuhtesemYuzyilDizi",
    "Adını Feriha Koydum": "https://www.youtube.com/@AdiniFerihaKoydumDizi",
    "Medcezir": "https://www.youtube.com/@MedcezirDizi",
    "Sihirli Annem": "https://www.youtube.com/@SihirliAnnemDizi",
    "Yedi Numara": "https://www.youtube.com/@YediNumaraDizi",
    "Kiralık Aşk": "https://www.youtube.com/@KiralikAskDizi",
    "Söz": "https://www.youtube.com/@SozDizi",
    "Kuruluş Osman": "https://www.youtube.com/@KurulusOsman",
    "Kurtlar Vadisi": "https://www.youtube.com/@KurtlarVadisiOfficial",
    "Kurtlar Vadisi Pusu": "https://www.youtube.com/channel/UCz1UfNp9VFp9R1HEFn5PY5A"
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
