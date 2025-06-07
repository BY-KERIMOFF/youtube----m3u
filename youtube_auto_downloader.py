import feedparser
import time
import subprocess
import os
import yaml

# YAML faylından konfiqurasiyanı oxuyuruq
with open("yt-downloader.yml", "r") as f:
    config = yaml.safe_load(f)

CHANNEL_ID = config["settings"]["channel_id"]
CHECK_INTERVAL = config["settings"]["check_interval_seconds"]
LAST_VIDEO_FILE = config["settings"]["last_video_file"]
DOWNLOAD_FOLDER = config["settings"]["download_folder"]
OUTPUT_TEMPLATE = config["settings"]["output_template"]
MODE = config["settings"].get("mode", "auto").lower()

def get_latest_video_url(channel_id):
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)
    return feed.entries[0].link if feed.entries else None

def read_last_video():
    try:
        with open(LAST_VIDEO_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def write_last_video(url):
    with open(LAST_VIDEO_FILE, "w") as f:
        f.write(url)

def download_video(video_url):
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    print(f"🎥 Yüklənir: {video_url}")
    subprocess.run([
        "yt-dlp",
        "-o", os.path.join(DOWNLOAD_FOLDER, OUTPUT_TEMPLATE),
        video_url
    ])

def check_and_download():
    latest = get_latest_video_url(CHANNEL_ID)
    if latest:
        last_saved = read_last_video()
        if latest != last_saved:
            print("✔️ Yeni video tapıldı!")
            write_last_video(latest)
            download_video(latest)
        else:
            print("ℹ️ Video eynidir, yükləmə yoxdur.")
    else:
        print("⚠️ Heç bir video tapılmadı.")

def main():
    if MODE == "manual":
        check_and_download()
    else:
        while True:
            print("⏱️ YouTube yoxlanılır...")
            check_and_download()
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
