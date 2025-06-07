# 📺 YouTube Live to M3U Playlist Converter

Bu layihə, `yt-dlp` vasitəsilə YouTube **canlı yayım linklərini** `.m3u8` formatında çıxarıb **media player-lərdə işləyən `.m3u` playlist** faylı yaradır.

---

## 📌 Məzmun

- 🔹 `channels.json` – YouTube kanallarının və ya canlı yayım URL-lərinin siyahısı
- 🔹 `generate_m3u.py` – JSON faylını oxuyur və `playlist.m3u` faylını yaradır
- 🔹 `playlist.m3u` – Nəticədə yaranan HLS playlist faylı (m3u8 linklərlə)

---

## 🔧 Quraşdırma

### 1. `yt-dlp` Qur

```bash
pip install yt-dlp
