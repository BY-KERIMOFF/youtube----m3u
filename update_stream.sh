#!/bin/bash

STREAM_URL="https://manifest.googlevideo.com/api/manifest/hls_variant/xyz123.m3u8?..."

cat <<EOF > stream.m3u8
#EXTM3U
#EXTINF:-1,Adanali Live Stream
$STREAM_URL
EOF

echo "✅ m3u8 faylı yeniləndi"
