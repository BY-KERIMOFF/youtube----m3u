### generate\_m3u.py

```python
import os
import json
import subprocess
from pathlib import Path

CHANNELS_FILE = Path("channels.json")
COOKIES = os.getenv("COOKIES_CONTENT", "cookies.txt")

# Directory for individual playlists
OUTPUT_DIR = Path("playlists")
OUTPUT_DIR.mkdir(exist_ok=True)

# Function to generate m3u for one channel
def generate_for_channel(name, url):
    cmd = [
        "yt-dlp",
        "--no-progress",
        "--no-warnings",
        "--no-check-certificate",
        "-g",
        url
    ]
    # Add login if provided
    user = os.getenv("YT_USERNAME")
    pwd  = os.getenv("YT_PASSWORD")
    if user and pwd:
        cmd[1:1] = ["--username", user, "--password", pwd]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        if proc.returncode != 0:
            print(f"[!] {name}: error {proc.returncode}\n{proc.stderr}")
            return False
        link = proc.stdout.strip().splitlines()[0]
        if not link.startswith("http"):
            print(f"[!] {name}: invalid link")
            return False
        # Write individual playlist file
        out_file = OUTPUT_DIR / f"{name}.m3u"
        with out_file.open('w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"#EXTINF:-1,{name}\n")
            f.write(link + "\n")
            f.write("#EXTVLCOPT:http-user-agent=okhttp/4.12.0\n")
        print(f"    ✅ {out_file}")
        return True
    except Exception as e:
        print(f"[!] {name}: Exception: {e}")
        return False

if __name__ == "__main__":
    if not CHANNELS_FILE.exists():
        print("channels.json tapılmadı. exiting.")
        exit(1)
    channels = json.loads(CHANNELS_FILE.read_text(encoding='utf-8'))
    for ch in channels:
        name = ch.get("name", "unknown").replace(" ", "_")
        url  = ch.get("url", "")
        print(f"Processing {name}")
        generate_for_channel(name, url)
```

---

### .github/workflows/generate.yml

```yaml
name: Generate Individual M3U Playlists

on:
  workflow_dispatch:
  schedule:
    - cron: '*/10 * * * *'  # hər 10 dəqiqədə bir işə düşəcək

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Create cookies.txt
        run: echo "${{ secrets.COOKIES_TXT }}" > cookies.txt
        shell: bash

      - name: Generate individual playlists
        shell: bash
        timeout-minutes: 7
        env:
          YT_USERNAME: ${{ secrets.YT_USERNAME }}
          YT_PASSWORD: ${{ secrets.YT_PASSWORD }}
        run: |
          python generate_m3u.py

      - name: Commit & Push changes
        shell: bash
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add playlists/*.m3u
          git diff --cached --quiet || (git commit -m "Update individual playlists" && \
            git push https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }} HEAD:main)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
