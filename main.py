import json

def main():
    input_file = "youtube_channels.json"
    output_file = "channels.m3u"

    with open(input_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "No Name").strip().upper()
            url = ch.get("url", "").strip()
            group = ch.get("group", "GENEL").strip().upper()
            if url:
                f.write(f'#EXTINF:-1 group-title="{group}",{name}\n')
                f.write(f'{url}\n')

    print(f"{output_file} faylı yaradıldı.")

if __name__ == "__main__":
    main()
