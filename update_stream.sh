#!/bin/bash

# Canlı yayım URL-i (real video linki olmalıdır)
# Məsələn: https://www.youtube.com/watch?v=CANLI_YAYIM_ID
URL="https://www.youtube.com/@Adanali/live"

OUTPUT_FILE="stream.m3u8"

# Canlı video URL-ni tapmaq üçün yt-dlp ilə JSON məlumat alırıq
LIVE_VIDEO_URL=$(yt-dlp --skip-download --print-json "$URL" 2>/dev/null | jq -r '.url // .webpage_url' | head -n1)

if [[ -z "$LIVE_VIDEO_URL" || "$LIVE_VIDEO_URL" == "null" ]]; then
    echo "🚫 Canlı yayım tapılmadı."
    exit 1
fi

# İndi həmin linkdən m3u8 axını alırıq
STREAM_URL=$(yt-dlp -g "$LIVE_VIDEO_URL" 2>/dev/null | head -n1)

if [[ -z "$STREAM_URL" ]]; then
    echo "🚫 Canlı yayımın m3u8 linki tapılmadı."
    exit 1
fi

# stream.m3u8 faylını yazırıq
echo "#EXTM3U" > $OUTPUT_FILE
echo "#EXTINF:-1,Adanali Live Stream" >> $OUTPUT_FILE
echo "$STREAM_URL" >> $OUTPUT_FILE

echo "✅ m3u8 faylı yeniləndi: $STREAM_URL"
