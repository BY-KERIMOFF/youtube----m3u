import yt_dlp
import time

# Burada istədiyin YouTube kanallarını əlavə et
channels = [
    ("SHOW MAX", "https://www.youtube.com/@showtv/live"),
    ("YASAK ELMA", "https://www.youtube.com/@YasakElma/live"),
    ("SEKSENLER", "https://www.youtube.com/@seksenlertrt/live"),
    ("ASKI MEMMU", "https://www.youtube.com/AskMemnuKanalD/live"),
    ("GULSAH FILM", "https://www.youtube.com/@GulsahFilmOfficial/live"),
    ("CENNET MAHALLESI", "https://www.youtube.com/@cennetmahallesishowtv"),
    ("MUHTESEM YUZYIL", "https://www.youtube.com/@muhtesemyuzyilofficial/live"),
    ("ADINI FERIHA KOYDUM", "https://www.youtube.com/@AdiniFerihaKoydumDizi/live"),
    ("MEDCEZIR", "https://www.youtube.com/@Medcezirtvdizisi/live"),
    ("YESIL DENIZ", "https://www.youtube.com/@yesildeniztrt1/live"),
    # ... buraya digər kanalları da əlavə edə bilərsən ...
]

def fetch_stream_url(youtube_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'format': 'best[ext=m3u8]',
        'force_generic_extractor': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(youtube_url, download=False)
            # 'url' əsas stream üçün olur
            return info_dict.get('url')
        except Exception as e:
            print(f"Xəta baş verdi ({youtube_url}): {e}")
            return None

def generate_m3u():
    m3u = "#EXTM3U\n"
    for name, url in channels:
        stream_url = fetch_stream_url(url)
        if stream_url:
            m3u += f"#EXTINF:0,{name}\n{stream_url}\n"
        else:
            m3u += f"#EXTINF:0,{name}\n# Stream tapılmadı\n"
    with open("youtube_live.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

if __name__ == "__main__":
    while True:
        print("M3U faylı yenilənir...")
        generate_m3u()
        print("Yeniləndi! 30 dəqiqə sonra təkrar yenilənəcək.")
        time.sleep(1800)  # 30 dəqiqə
