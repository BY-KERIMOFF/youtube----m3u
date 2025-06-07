import requests
from bs4 import BeautifulSoup
import re

def check_live_html(custom_url):
    url = f"https://www.youtube.com/{custom_url}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    html = resp.text
    
    # BeautifulSoup parse
    soup = BeautifulSoup(html, "html.parser")
    
    # 1) yt-badge-live badge-lər üçün
    badge = soup.find("span", class_="yt-badge yt-badge-live")
    if badge:
        print("🔴 Canlı yayım badge-lə aşkarlandı!")
        return True

    # 2) JSON text içində " watching"
    if re.search(r'\{"text":"\s*[\d,]+ watching"\}', html):
        print("🔴 Canlı yayım watching indikatoru aşkarlandı!")
        return True

    print("🔕 Canlı yayım yoxdur.")
    return False

def save_m3u(link="https://www.youtube.com/live"):
    with open("latest.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1,CANLI YAYIN\n")
        f.write(f"{link}\n")
    print("✅ latest.m3u faylı yaradıldı.")

if __name__ == "__main__":
    custom_url = "@Adanali"  # dəyişmək olar
    if check_live_html(custom_url):
        # Faraqlıq üçün /live sonluğunu istifadə edirik
        live_link = f"https://www.youtube.com/{custom_url}/live"
        save_m3u(live_link)
