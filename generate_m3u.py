import json
import subprocess
from pathlib import Path

CHANNELS = Path("channels.json")
OUTPUT = Path("playlist.m3u")
COOKIES = Path("cookies.txt")

def get_m3u8_url(name, url):
    cmd = [
        "yt-dlp",
        "--no-progress",
        "--no-warnings",
        "--no-check-certificate",
        "--cookies", str(COOKIES),
        "-g", url
    ]
    try:
        # 60 saniyə gözləyəcək, sonra çıxacaq
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        if proc.returncode == 0:
            link = proc.stdout.strip().splitlines()[0]
            if link.startswith("http"):
                return link
        print(f"[!] {name}: returncode={proc.returncode}", proc.stderr)
    except subprocess.TimeoutExpired:
        print(f"[!] {name}: TIMEOUT after 60s")
    except Exception as e:
        print(f"[!] {name}: Exception: {e}")
    return None

def main():
    if not CHANNELS.exists():
        print("Error: channels.json tapılmadı")
        return
    with CHANNELS.open(encoding="utf-8") as f:
        channels = json.load(f)

    lines = ["#EXTM3U"]
    for ch in channels:
        name = ch.get("name","?")
        url  = ch.get("url","")
        print(f"\n[+] Checking: {name}")
        m3u8 = get_m3u8_url(name, url)
        if m3u8:
            lines.append(f"#EXTINF:-1,{name}\n{m3u8}")
            print(f"    → OK")
        else:
            print(f"    → FAILED")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n🎉 playlist.m3u hazırlandı.")

if __name__=="__main__":
    main()
