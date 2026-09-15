import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE = "https://720izle.com/"
OUTPUT = "films.m3u"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)

visited = set()
film_pages = set()
streams = {}


def fetch(url):
    try:
        r = session.get(url, timeout=30)

        print(f"[HTTP {r.status_code}] {url}")

        if r.status_code != 200:
            return ""

        return r.text

    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
        return ""


def same_domain(url):
    return urlparse(url).netloc == urlparse(BASE).netloc


def normalize(url):
    url = url.split("#")[0]
    return url.rstrip("/") + "/"


def discover_links(url):
    html = fetch(url)

    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):

        href = urljoin(url, a["href"])
        href = normalize(href)

        if not same_domain(href):
            continue

        # artıq baxılıbsa keç
        if href in visited:
            continue

        text = a.get_text(" ", strip=True)

        # video/film səhifəsinə oxşayan linklər
        if text and len(text) >= 2:

            bad = [
                "/kategori/",
                "/category/",
                "/tag/",
                "/etiket/",
                "/author/",
                "/page/",
                "/iletisim/",
                "/hakkimizda/",
                "/gizlilik/",
            ]

            if not any(x in href.lower() for x in bad):

                # ana səhifə deyil
                if href != normalize(BASE):

                    film_pages.add(href)

        # pagination və kateqoriyaları da sonradan analiz etmək üçün saxla
        if (
            "/kategori/" in href
            or "/category/" in href
            or "/page/" in href
        ):
            if href not in visited:
                discover_links(href)

    visited.add(url)


def find_stream(url, html):

    soup = BeautifulSoup(html, "html.parser")

    # video/source tagları
    for tag in soup.find_all(["video", "source"]):

        for attr in ["src", "data-src"]:

            value = tag.get(attr)

            if not value:
                continue

            value = urljoin(url, value)

            if (
                ".m3u8" in value.lower()
                or ".mp4" in value.lower()
            ):
                return value

    # iframe
    for iframe in soup.find_all("iframe", src=True):

        src = urljoin(url, iframe["src"])

        print(f"    [IFRAME] {src}")

    # HTML daxilində açıq m3u8
    patterns = [
        r'https?://[^"\'<>\s]+\.m3u8(?:\?[^"\'<>\s]*)?',
        r'https?://[^"\'<>\s]+\.mp4(?:\?[^"\'<>\s]*)?',
    ]

    for pattern in patterns:

        matches = re.findall(pattern, html, re.I)

        if matches:
            return matches[0]

    return None


def parse_film(url):

    print()
    print("[FILM]", url)

    html = fetch(url)

    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    title = ""

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)

    if not title:

        title_tag = soup.find("title")

        if title_tag:
            title = title_tag.get_text(" ", strip=True)

    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        return

    stream = find_stream(url, html)

    if stream:

        streams[title] = stream

        print("[STREAM FOUND]")
        print(stream)

    else:

        print("[NO OPEN M3U8/MP4]")


def save():

    with open(OUTPUT, "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n\n")

        for title, url in sorted(streams.items()):

            title = title.replace('"', "'")

            f.write(
                f'#EXTINF:-1,{title}\n'
            )

            f.write(url + "\n")

    print()
    print("=" * 60)
    print("FOUND:", len(streams))
    print("OUTPUT:", OUTPUT)
    print("=" * 60)


def main():

    print("=" * 60)
    print("720IZLE SCRAPER")
    print("=" * 60)

    print()
    print("[1] Sayt analiz edilir...")

    discover_links(BASE)

    print()
    print("[2] Tapilan səhifələr:", len(film_pages))

    # İlk mərhələdə maksimum 500 səhifə
    pages = list(film_pages)[:500]

    for i, url in enumerate(pages, 1):

        print()
        print(f"[{i}/{len(pages)}]")

        parse_film(url)

        time.sleep(0.3)

    save()


if __name__ == "__main__":
    main()
