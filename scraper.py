import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://720izle.com/"
START_URL = "https://720izle.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(HEADERS)

film_links = set()
films = {}


def get(url):
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
        return ""


def clean_name(name):
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\b(izle|full hd|720p|1080p)\b", "", name, flags=re.I)
    return name.strip(" -|")


def find_film_links(url):
    print(f"[SCAN] {url}")

    html = get(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])

        if not href.startswith(BASE_URL):
            continue

        # Kateqoriya, ana səhifə və digər sistem linklərini keç
        if any(x in href for x in [
            "/kategori/",
            "/tag/",
            "/oyuncu/",
            "/yonetmen/",
            "/sayfa/",
            "/page/",
        ]):
            continue

        text = a.get_text(" ", strip=True)

        # Film linklərini təxmini müəyyən et
        if text and len(text) > 2:
            if "/film/" in href or "/dizi/" in href:
                film_links.add(href)

    print(f"[+] Film linkləri: {len(film_links)}")


def extract_video(url, html):
    soup = BeautifulSoup(html, "html.parser")

    # video/source tagları
    for tag in soup.find_all(["video", "source"]):
        for attr in ["src", "data-src"]:
            value = tag.get(attr)

            if value:
                value = urljoin(url, value)

                if ".m3u8" in value.lower() or ".mp4" in value.lower():
                    return value

    # Açıq şəkildə HTML-də olan m3u8/mp4
    patterns = [
        r'https?://[^"\']+\.m3u8[^"\']*',
        r'https?://[^"\']+\.mp4[^"\']*',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.I)

        if match:
            return match.group(0)

    return None


def parse_film(url):
    print(f"[FILM] {url}")

    html = get(url)

    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    title = ""

    # WordPress title
    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)

    if not title:
        title_tag = soup.find("title")

        if title_tag:
            title = title_tag.get_text(" ", strip=True)

    title = clean_name(title)

    if not title:
        return

    video = extract_video(url, html)

    if video:
        films[title] = video
        print(f"[OK] {title}")
        print(f"     {video}")
    else:
        print(f"[NO STREAM] {title}")


def save_m3u():
    with open("films.m3u", "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n\n")

        for title, url in sorted(films.items()):

            f.write(
                f'#EXTINF:-1 tvg-name="{title}",{title}\n'
            )

            f.write(url + "\n")

    print()
    print("=" * 50)
    print(f"TOTAL FILMS: {len(films)}")
    print("M3U: films.m3u")
    print("=" * 50)


def main():

    # Ana səhifə
    find_film_links(START_URL)

    # Kateqoriyalar
    categories = [
        "yerli-filmler",
        "aksiyon-filmleri",
        "macera-filmleri",
        "dram-filmleri",
        "komedi-filmleri",
        "korku-filmleri",
        "bilim-kurgu-filmleri",
        "gerilim-filmleri",
        "suç-filmleri",
        "romantik-filmler",
        "animasyon-filmleri",
        "fantastik-filmler",
        "tarih-filmleri",
        "savas-filmleri",
        "spor-filmleri",
        "western-kovboy",
    ]

    for category in categories:

        url = BASE_URL + "kategori/" + category + "/"

        find_film_links(url)

        time.sleep(1)

    # Toplanan film səhifələrini oxu
    print()
    print(f"[INFO] {len(film_links)} film səhifəsi tapıldı")

    for i, url in enumerate(film_links, 1):

        print(f"[{i}/{len(film_links)}]")

        parse_film(url)

        time.sleep(0.5)

    save_m3u()


if __name__ == "__main__":
    main()
