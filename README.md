# YouTube Live M3U8 Generator

Bu repository YouTube video linkindən canlı yayımın `.m3u8` axın URL-sini çıxarıb `.m3u8` faylı yaradır.

## Necə istifadə etmək olar?

1. `generate_m3u8.py` faylında `youtube_url` dəyişənini istədiyiniz YouTube canlı yayım linki ilə dəyişin.
2. Repository-də `.github/workflows/update.yml` faylı var, workflow-u GitHub Actions-da əl ilə işə sala bilərsiniz.
3. Workflow işləyəndə `youtube_live.m3u8` faylı yenilənəcək və repoya push olunacaq.
4. Bu `.m3u8` faylını IPTV playerlərdə və ya hər hansı `.m3u8` dəstəkləyən pleyerdə istifadə edə bilərsiniz.

## Tələblər

- Python 3.7+
- `yt-dlp` kitabxanası

## Lokal işə salmaq

```bash
pip install yt-dlp
python generate_m3u8.py
