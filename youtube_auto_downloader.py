import feedparser
import time
import subprocess
import os

# YouTube kanal ID – cennetmahallesishowtv üçün tapılmış ID
CHANNEL_ID = "UCOqe-z52nnpVSAe8Ds0fxaA"

# Videonu yoxlama intervalı (saniyə ilə): 5 dəqiqə
CHECK_INTERVAL = 300

# Əvvəlki video linki bu faylda saxlanacaq
LAST_VIDEO_FILE = "last_video.txt"

# Videolar bu qovluqda saxlanacaq
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

def main():
    while True:
        print("⏱️  YouTube yoxlanılır...")
        latest = get_latest_video_url(CHANNEL_ID)
        if latest:
            last_saved = read_last_video()
            if latest != last_saved:
                print("✔️ Yeni video tapıldı!")
                write_last_video(latest)
                download_video(latest)
            else:
                print("🔄 Hələ yenilik yoxdur.")
        else:
            print("⚠️ Kanaldan video alınmadı.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
