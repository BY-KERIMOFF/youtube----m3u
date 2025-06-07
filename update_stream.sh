#!/bin/bash

URL="https://www.youtube.com/@Adanali/live"
OUTPUT_FILE="stream.m3u8"

STREAM_URL=$(yt-dlp -g "$URL" 2>/dev/null)

if [[ -n "$STREAM_URL" ]]; then
    echo "#EXTM3U" > $OUTPUT_FILE
    echo "#EXTINF:-1,Adanali Live Stream" >> $OUTPUT_FILE
    echo "$STREAM_URL" >> $OUTPUT_FILE
    echo "✅ m3u8 faylı yeniləndi: $STREAM_URL"
else
    echo "🚫 Canlı yayım tapılmadı."
fi
