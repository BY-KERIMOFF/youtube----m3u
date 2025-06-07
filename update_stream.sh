#!/bin/bash

URL="https://www.youtube.com/watch?v=TnKHC3tgl3s"

STREAM_URL=$(streamlink --stream-url "$URL" best 2>/dev/null)

if [[ -z "$STREAM_URL" ]]; then
    echo "🚫 Canlı yayımın m3u8 linki tapılmadı (streamlink)."
    exit 1
fi

cat <<EOF > stream.m3u8
#EXTM3U
#EXTINF:-1,Adanali Live Stream
$STREAM_URL
EOF

echo "✅ m3u8 faylı yeniləndi (streamlink): $STREAM_URL"
