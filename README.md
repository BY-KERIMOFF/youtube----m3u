# YouTube Live M3U8 Generator

Bu repository YouTube canlı yayım linklərini `json` fayldan oxuyub `.m3u8` playlist yaradır.

## Hazır TV kanal siyahısı

Repo daxilində `youtube_channels.json` faylı hazır gəlir və bu kanalları ehtiva edir:
- Kanal D
- Show TV
- Star TV
- ATV
- TRT 1

İstəsən bu fayla əlavə kanallar da yaza bilərsən.

## İstifadə

```bash
pip install -r requirements.txt
python script.py
```

Default olaraq `youtube_channels.json` oxunur və `live_channels.m3u8` yenilənir.

## Token avtomatik yenilənsin (watch rejimi)

YouTube axın URL-lərindəki tokenlər vaxt keçdikcə köhnəlir. Bunu azaltmaq üçün scripti periodik yenilənmə rejimində işlət:

```bash
python script.py --watch --interval 1800
```

Bu, hər 30 dəqiqədən bir `live_channels.m3u8` faylını yenidən yaradacaq.

## Parametrlər

- `--source-json youtube_channels.json` — kanalların oxunacağı json faylı.
- `--cookies youtube_cookies.txt` — `yt-dlp` üçün cookie faylı (fayl yoxdursa cookies-siz davam edir).
- `--output live_channels.m3u8` — çıxış playlist adı.
- `--watch` — fasiləsiz yeniləmə rejimi.
- `--interval 1800` — yenilənmə intervalı (saniyə, 0-dan böyük olmalıdır).

## JSON formatı

`script.py` `channels` massivində `name` və `url` açarlarını gözləyir. İstəyə görə
`extractor: "web_m3u8"` verərək saytdan hər yeniləmədə yeni token-li `.m3u8`
linkini avtomatik çıxara bilərsən:

```json
{
  "channels": [
    {
      "name": "Kanal D",
      "url": "https://www.youtube.com/@KanalD/live"
    },
    {
      "name": "tv8",
      "url": "https://www.tv8.com.tr/canli-yayin",
      "extractor": "web_m3u8",
      "preferred_keyword": "tv8_1080p.m3u8"
    }
  ]
}
```

## Tələblər

- Python 3.9+
- `yt-dlp`
