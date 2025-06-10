import yt_dlp

# YouTube video linki
youtube_url = "https://www.youtube.com/watch?v=6wHAK439FDI"

def get_m3u8_url(youtube_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = info.get('formats', [])
        for f in formats:
            # 'm3u8_native' protokolu olan axını tap
            if f.get('protocol') == 'm3u8_native':
                return f.get('url')
    return None

def write_m3u8_file(m3u8_url, filename="youtube_live.m3u8"):
    if not m3u8_url:
        print("M3U8 URL tapılmadı!")
        return
    m3u_content = f"""#EXTM3U
#EXTINF:-1, YouTube Live Stream
{m3u8_url}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"✅ {filename} yaradıldı!")

if __name__ == "__main__":
    m3u8_url = get_m3u8_url(youtube_url)
    write_m3u8_file(m3u8_url)
