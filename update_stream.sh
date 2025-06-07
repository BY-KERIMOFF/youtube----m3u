#!/bin/bash

URL=$(python3 get_live_url.py)

if [[ "$URL" == *"🚫"* ]]; then
    echo "$URL"
    exit 1
fi

STREAM_URL=$(yt-dlp -g "$URL" 2>/dev/null | head -n1)

if [[ -z "$STREAM_URL" ]]; then
    echo "🚫 Canlı yayımın m3u8 linki tapılmadı."
    exit 1
fi

cat <<EOF > stream.m3u8
#EXTM3U
#EXTINF:-1,Adanali Live Stream
$STREAM_URL
EOF

echo "✅ m3u8 faylı yeniləndi: $STREAM_URL"
