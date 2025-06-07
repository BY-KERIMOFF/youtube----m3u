# YouTube Live to M3U Generator

YouTube canlı yayım linklərini `yt-dlp` və `cookies.txt` vasitəsilə `.m3u8` formatında çıxarıb `playlist.m3u` yaradır.

## İstifadə:

1. Brauzerinizdən `cookies.txt` faylını ixrac edin (YouTube-da giriş etdikdən sonra).
2. `channels.json` faylında YouTube canlı yayım URL-lərini yazın.
3. Skripti işə salın:

```bash
python generate_m3u.py
