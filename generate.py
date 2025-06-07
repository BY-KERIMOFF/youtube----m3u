import os
import json
import subprocess

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

output_dir = "m3u8"
os.makedirs(output_dir, exist_ok=True)

for channel in channels:
    name = channel["name"]
    url = channel["url"]
    
    try:
        stream_url = subprocess.check_output(["yt-dlp", "-g", url], text=True).strip()
        file_name = os.path.join(output_dir, f"{name.replace(' ', '_').lower()}.m3u8")
        m3u8_content = f"""#EXTM3U
#EXTINF:-1,{name}
{stream_url}
"""
        with open(file_name, "w", encoding="utf-8") as out_file:
            out_file.write(m3u8_content)
        print(f"[+] {name} üçün yazıldı: {file_name}")
    except subprocess.CalledProcessError:
        print(f"[!] {name} üçün stream tapılmadı.")
