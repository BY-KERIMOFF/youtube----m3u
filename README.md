# YouTube Live M3U8 Playlist Generator

Bu GitHub repositoriyası avtomatik olaraq `.m3u8` formatında **YouTube canlı yayım** playlist faylı yaradır.

## 📺 Canlı Kanal
Hal-hazırda daxil edilmiş kanal:
- **TRT Haber** (Türkiyə xəbər kanalı)

## 🔁 Avtomatik Yenilənmə

GitHub Actions vasitəsilə `.m3u8` faylı avtomatik **hər 6 saatdan bir** yenilənir.

## ✅ İstifadə qaydası

`.m3u8` faylını bu linkdən birbaşa IPTV pleyerlərə əlavə edə bilərsiniz:

```
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/trt_haber_live.m3u8
```

> `YOUR_USERNAME` və `YOUR_REPO` hissələrini öz GitHub istifadəçi adı və repozitoriya adınızla əvəz edin.

## 🛠️ Fayllar

- `generate_m3u8.py` – `.m3u8` faylı yaradan Python skripti
- `.github/workflows/update.yml` – GitHub Actions workflow (avtomatik işləmə üçün)

## 🎯 Uyğun Proqramlar

Bu `.m3u8` faylı aşağıdakı proqramlarla işləyir:
- VLC Media Player
- Smart IPTV / OTT Navigator
- Kodi
- MX Player (Android)
- IPTV Smarters Pro

## 💬 Əlaqə

Əgər əlavə kanal və ya funksiyalar əlavə etmək istəyirsinizsə, issue açın və ya pull request göndərin.
