import yt_dlp

channels = [
    ("SHOW MAX", "https://www.youtube.com/@showtv/live"),
    ("YASAK ELMA", "https://www.youtube.com/@YasakElma/live"),
    # Buraya istədiyin qədər əlavə et...
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
            return info_dict.get('url')
        except Exception as e:
            print(f"Xəta: {youtube_url} -> {e}")
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
    generate_m3u()
