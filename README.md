# YouTube Live M3U8 Generator

Bu repository YouTube canlı yayım linklərini `json` fayldan oxuyub `.m3u8` playlist yaradır.

## Hazır TV kanal siyahısı

Repo daxilində `youtube_channels.json` faylı hazır gəlir və genişləndirilmiş Türkiyə canlı kanal siyahısı ehtiva edir (məs: Kanal D, Show TV, Star TV, ATV, TRT 1, A Haber, CNN TÜRK, SABAH və s.).

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

`script.py` `channels` massivində `name` və `url` açarlarını gözləyir:

```json
{
  "channels": [
    {
      "name": "Kanal D",
      "url": "https://www.youtube.com/@KanalD/live"
    }
  ]
}
```

## Tələblər

- Python 3.9+
- `yt-dlp`
