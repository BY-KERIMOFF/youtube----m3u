import json
import os

# JSON faylını oxu
with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

# Nəticə fayllarının saxlanacağı qovluq
output_dir = "m3u8"
os.makedirs(output_dir, exist_ok=True)

# Hər kanal üçün ayrıca m3u8 faylı yarat
for ch in channels:
    # Fayl adı üçün "name" dan istifadə, boşluqları _ ilə əvəzlə, kiçik hərflə
    safe_name = ch["name"].lower().replace(" ", "_").replace("ç", "c").replace("ö", "o").replace("ş", "s").replace("ü", "u").replace("ğ", "g").replace("ı", "i").replace("ə", "e").replace(" ", "_")
    filename = os.path.join(output_dir, f"{safe_name}.m3u8")

    with open(filename, "w", encoding="utf-8") as f_out:
        f_out.write("#EXTM3U\n")
        f_out.write("#EXT-X-VERSION:3\n")
        f_out.write("#EXT-X-STREAM-INF:BANDWIDTH=2096000\n")
        f_out.write(f"{ch['url']}\n")

print(f"{len(channels)} m3u8 faylı '{output_dir}' qovluğunda yaradıldı.")
