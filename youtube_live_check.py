import requests
import sys

def get_live_stream_url(channel_handle):
    # Invidious public instance (işlək mirror): yewtu.be
    api_url = f"https://yewtu.be/channel/{channel_handle}/live"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(api_url, headers=headers, allow_redirects=True)
        final_url = response.url

        # Əgər linkdə "watch?v=" varsa və "live" URL deyil – deməli canlı yayımdır
        if "watch?v=" in final_url and "/live" not in final_url:
            print("🔴 Canlı yayım AŞKARLANDI!")
            return final_url
        else:
            print("🔕 Canlı yayım YOXDUR.")
            return None

    except Exception as e:
        print(f"❌ Xəta baş verdi: {e}")
        return None

def save_m3u(link):
    with open("latest.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1,CANLI YAYIN\n")
        f.write(f"{link}\n")
        print("✅ latest.m3u uğurla yazıldı.")

if __name__ == "__main__":
    # Buraya istədiyin kanalın handle-ını yaz: məsələn @NBCNewsNOW, @Adanali, s.
    channel_handle = "@NBCNewsNOW"  # dəyişmək olar
    live_url = get_live_stream_url(channel_handle)
    if live_url:
        save_m3u(live_url)
