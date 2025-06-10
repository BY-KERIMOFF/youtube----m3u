import yt_dlp

def get_m3u8_url(youtube_url):
    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = info.get('formats', [])
        for f in formats:
            if f.get('ext') == 'mp4' and 'm3u8' in f.get('protocol', ''):
                return f.get('url')
        # alternativ olaraq ən yaxşı formatı qaytarmaq üçün
        return info.get('url')

if __name__ == '__main__':
    youtube_url = 'https://www.youtube.com/watch?v=VIDEO_ID'  # videonun linkini yaz
    m3u8_url = get_m3u8_url(youtube_url)
    print("M3U8 URL:", m3u8_url)
