#!/bin/bash

# YouTube canlı yayım linki (sabit)
STREAM_URL="https://www.youtube.com/watch?v=TnKHC3tgl3s"

cat <<EOF > stream.m3u8
#EXTM3U
#EXTINF:-1,Adanali Live Stream
$STREAM_URL
EOF

echo "✅ stream.m3u8 faylı yeniləndi"
