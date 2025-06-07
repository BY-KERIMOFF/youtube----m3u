import requests

def get_live_stream_url(custom_url):
    live_url = f"https://www.youtube.com/{custom_url}/live"
    response = requests.get(live_url, allow_redirects=True)

    final_url = response.url

    if "watch?v=" in final_url and "live" not in final_url:
        print("🔴 Canlı yayım AKTİVDİR!")
        return final_url
    else:
        print("🔕 Canlı yayım yoxdur.")
        return None

def save_m3u(link):
    with open("latest.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1,NBC News - CANLI YAYIN\n")
        f.write(f"{link}\n")

if __name__ == "__main__":
    custom_url = "@NBCNewsNOW"
    live_link = get_live_stream_url(custom_url)
    if live_link:
        save_m3u(live_link)
