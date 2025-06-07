import json
import subprocess

# Fayl adları
input_file = "channels.json"
output_file = "playlist.m3u"

def get_m3u8_url(youtube_url):
    try:
        result = subprocess.run(
            ['yt-dlp', '-g', youtube_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[X] Problem: {youtube_url}\n{result.stderr}")
    except Exception as e:
        print(f"[!] Xəta baş verdi: {e}")
    return None

def main():
    with open(input_file, 'r', encoding='utf-8') as f:
        channels = json.load(f)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")

        for channel in channels:
            name = channel["name"]
            url = channel["url"]
            print(f"[+] Yoxlanır: {name}")
            stream_url = get_m3u8_url(url)
            if stream_url:
                f.write(f"#EXTINF:-1,{name}\n{stream_url}\n")
                print(f"    ✅ OK: {stream_url}")
            else:
                print(f"    ❌ Stream tapılmadı.")

    print(f"\n🎉 Hazırlandı: {output_file}")

if __name__ == "__main__":
    main()
