import requests
import re
import xml.etree.ElementTree as ET

def get_channel_id(custom_url):
    url = f"https://www.youtube.com/{custom_url}/about"
    response = requests.get(url)
    if response.status_code != 200:
        print("Kanal səhifəsi tapılmadı.")
        return None
    match = re.search(r'"channelId":"(UC[\w-]{22})"', response.text)
    if match:
        return match.group(1)
    else:
        print("Kanal ID tapılmadı.")
        return None

def get_latest_video_link(channel_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    response = requests.get(rss_url)
    if response.status_code != 200:
        print("RSS feed tapılmadı.")
        return None
    root = ET.fromstring(response.content)
    video = root.find('{http://www.w3.org/2005/Atom}entry')
    if video is not None:
        link = video.find('{http://www.w3.org/2005/Atom}link').attrib['href']
        title = video.find('{http://www.w3.org/2005/Atom}title').text
        return title, link
    else:
        print("Video tapılmadı.")
        return None

def save_m3u(title, link):
    with open("latest.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1,{title}\n")
        f.write(f"{link}\n")

if __name__ == "__main__":
    custom_url = "@cennetmahallesishowtv"
    channel_id = get_channel_id(custom_url)
    if channel_id:
        result = get_latest_video_link(channel_id)
        if result:
            title, link = result
            print(f"Son video:\nBaşlıq: {title}\nLink: {link}")
            save_m3u(title, link)
