### generate\_m3u.py

```python
import os
import json
import subprocess
from pathlib import Path

# JSON file containing channel names and live URLs
CHANNELS_FILE = Path("channels.json")
# Directory to store individual M3U playlists
OUTPUT_DIR = Path("playlists")
OUTPUT_DIR.mkdir(exist_ok=True)

# Function to fetch HLS (.m3u8) URL using yt-dlp
def get_m3u8_url(name, url):
    cmd = [
        "yt-dlp",
        "--no-progress",
        "--no-warnings",
        "--no-check-certificate",
        "-g",
        url
    ]
    # Add login credentials if provided
    user = os.getenv("YT_USERNAME")
    pwd  = os.getenv("YT_PASSWORD")
    if user and pwd:
        cmd.insert(1, user)
        cmd.insert(1, "--username")
        cmd.insert(3, pwd)
        cmd.insert(3, "--password")

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        if proc.returncode == 0:
            link = proc.stdout.strip().splitlines()[0]
            return link
        else:
            print(f"[!] {name}: error {proc.returncode}\n{proc.stderr}")
    except subprocess.TimeoutExpired:
        print(f"[!] {name}: TIMEOUT after 60s")
    except Exception as e:
        print(f"[!] {name}: Exception: {e}")
    return None

# Main execution
if __name__ == "__main__":
    if not CHANNELS_FILE.exists():
        print("channels.json not found. Exiting.")
        exit(1)

    channels = json.loads(CHANNELS_FILE.read_text(encoding='utf-8'))
    for ch in channels:
        name = ch.get("name", "unknown").replace(" ", "_")
        url  = ch.get("url", "")
        print(f"Processing {name}")
        link = get_m3u8_url(name, url)
        if link:
            out_file = OUTPUT_DIR / f"{name}.m3u"
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"#EXTINF:-1,{name}\n")
                f.write(link + "\n")
                f.write("#EXTVLCOPT:http-user-agent=okhttp/4.12.0\n")
            print(f"    ✅ Created {out_file}")
        else:
            print(f"    ❌ Failed for {name}")
```
