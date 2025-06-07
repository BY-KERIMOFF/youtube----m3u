import subprocess

INPUT_M3U = "channels.m3u"
OUTPUT_M3U = "streams.m3u"

def extract_stream_url(youtube_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", youtube_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[!] Xəta: {youtube_url} → {result.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        print(f"[!] TIMEOUT: {youtube_url}")
        return None
    except Exception as e:
        print(f"[!] İstisna: {youtube_url} → {e}")
        return None

def main():
    with open(INPUT_M3U, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_M3U, "w", encoding="utf-8") as out_f:
        out_f.write("#EXTM3U\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF:"):
                info_line = line
                group_line = lines[i+1].strip() if (i+1) < len(lines) else ""
                url_line = lines[i+2].strip() if (i+2) < len(lines) else ""

                print(f"[+] Kanal işlənir: {info_line} → {url_line}")

                stream_url = extract_stream_url(url_line)
                if stream_url:
                    out_f.write(f"{info_line}\n")
                    if group_line.startswith("#EXTGRP:"):
                        out_f.write(f"{group_line}\n")
                    out_f.write(f"{stream_url}\n")
                else:
                    print(f"[✘] Xəta: Stream URL tapılmadı → {url_line}")

                i += 3
            else:
                i += 1

    print(f"[✔] Tamamlandı. Yeni .m3u faylı: {OUTPUT_M3U}")

if __name__ == "__main__":
    main()
