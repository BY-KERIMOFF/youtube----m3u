import json
import os
import re

def sanitize_filename(name):
    """Fayl adını təhlükəsiz hala sal (boşluqları və simvolları təmizlə)."""
    return re.sub(r'[^\w\-_.]', '_', name.strip())

def main():
    input_file = "youtube_channels.json"
    output_dir = "m3u8_channels"

    # Çıxış qovluğunu yarat (əgər yoxdursa)
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    for ch in channels:
        name = ch.get("name", "No_Name")
        url = ch.get("url", "").strip()
        group = ch.get("group", "GENEL").strip().upper()

        if not url:
            continue  # URL boşdursa keç

        filename = sanitize_filename(name) + ".m3u8"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as out:
            out.write("#EXTM3U\n")
            out.write(f'#EXTINF:-1 group-title="{group}",{name.strip()}\n')
            out.write(f'{url}\n')

        print(f"{filename} yaradıldı.")

if __name__ == "__main__":
    main()
