import requests

def get_live_stream_url(custom_url):
    url = f"https://www.youtube.com/{custom_url}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 
    }
    response = requests.get(url, headers=headers, allow_redirects=False)
    
    # Əgər redirect varsa və "Location" headerində watch?v=... varsa
    if response.status_code in (301, 302) and "Location" in response.headers:
        final_url = response.headers["Location"]
        if "watch?v=" in final_url:
            print("🔴 Canlı yayım AKTİVDİR! Redirected URL tapıldı.")
            return final_url
    
    # Əlavə yoxlama: .url əli istənilən halda
    final_url = response.url
    if "watch?v=" in final_url and "live" not in final_url:
        print("🔴 Canlı yayım AKTİVDİR! Redirect sonrası URL.")
        return final_url
    
    print("🔕 Canlı yayım yoxdur.")
    return None

def save_m3u(link):
    with open("latest.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1,CANLI YAYIN\n")
        f.write(f"{link}\n")

if __name__ == "__main__":
    custom_url = "@NBCNewsNOW"  # Canlı çıxışlı kanal
    live_link = get_live_stream_url(custom_url)
    if live_link:
        save_m3u(live_link)
