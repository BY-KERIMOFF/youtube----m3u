channel_name = "TRT Haber"
youtube_live_url = "https://www.youtube.com/channel/UCHyFz8p4Nnbd4JaGQwPb6Xg/live"

m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="trthaber" tvg-name="{channel_name}" group-title="News", {channel_name}
{youtube_live_url}
"""

with open("trt_haber_live.m3u8", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print("✅ trt_haber_live.m3u8 yaradıldı.")
