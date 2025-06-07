# YouTube Live to M3U Playlist Generator

YouTube canlı yayım linklərini `yt-dlp` və `cookies.txt` ilə `.m3u8` formatında çıxarıb `playlist.m3u` faylı yaradır.

## İstifadə qaydası:

1. Chrome və ya digər brauzerdən YouTube hesabına daxil ol.
2. [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/lmjcdhbnlojpmjmnodnlpdfkdjflkobe) uzantısı ilə cookies faylını ixrac et.
3. `cookies.txt` faylını layihə qovluğuna yerləşdir.
4. `channels.json` faylında YouTube canlı yayım linklərini əlavə et.
5. Terminalda aşağıdakı əmri icra et:

```bash
pip install -r requirements.txt
python generate_m3u.py
