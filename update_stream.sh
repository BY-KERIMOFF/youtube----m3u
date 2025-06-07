#!/bin/bash

URL="https://www.youtube.com/watch?v=TnKHC3tgl3s"

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
