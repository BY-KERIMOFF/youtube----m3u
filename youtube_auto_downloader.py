import feedparser
import time
import subprocess
import os
import argparse

CHANNEL_ID = "UCOqe-z52nnpVSAe8Ds0fxaA"
CHECK_INTERVAL = 300
LAST_VIDEO_FILE = "last_video.txt"
DOWNLOAD_FOLDER = "downloads"

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
        "-o", os.path.join(DOWNLOAD_FOLDER, "%(upload_date)s_%(title)s.%(ext)s"),
        video_url
    ])

def run_once():
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

def run_loop():
    while True:
        print("⏱️  YouTube yoxlanılır...")
        run_once()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube video downloader")
    parser.add_argument("--manual", action="store_true", help="Əl ilə bir dəfəlik video yoxla və yüklə")
    args = parser.parse_args()

    if args.manual:
        run_once()
    else:
        run_loop()
