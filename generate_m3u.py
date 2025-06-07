import yt_dlp
import os

channels = {
    "SHOW_MAX": "https://www.youtube.com/channel/UC...1",
    "YASAK_ELMA": "https://www.youtube.com/channel/UC...2",
    "SEKSENLER": "https://www.youtube.com/channel/UC...3",
}

cookies = "cookies.txt"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

for name, url in channels.items():
    print(f"[+] Processing: {name}")
    try:
        ydl_opts = {
            "quiet": True,
            "cookies": cookies,
            "extract_flat": True,
            "dump_single_json": True,
            "playlistend": 5,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)

        if "entries" in result:
            m3u_lines = ["#EXTM3U"]
            for entry in result["entries"]:
                m3u_lines.append(f'#EXTINF:-1,{entry["title"]}')
                m3u_lines.append(entry["url"])
            
            with open(f"{output_dir}/{name}.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_lines))
            print(f"→ {name}.m3u yaradıldı.")
        else:
            print(f"→ {name} üçün heç nə tapılmadı.")
    except Exception as e:
        print(f"[X] {name} xətası: {e}")
