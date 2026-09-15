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
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)

visited = set()
film_pages = set()
streams = {}


def normalize(url):
    return url.split("#")[0].rstrip("/") + "/"


def same_domain(url):
    return urlparse(url).netloc == urlparse(BASE).netloc


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


def discover_page(url):
    url = normalize(url)

    if url in visited:
        return

    visited.add(url)

    print("[SCAN]", url)

    html = fetch(url)

    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):

        href = normalize(urljoin(url, a["href"]))

        if not same_domain(href):
            continue

        if href == normalize(BASE):
            continue

        if href in visited:
            continue

        text = a.get_text(" ", strip=True)

        if not text:
            continue

        # Kateqoriya
        if "/kategori/" in href:

            discover_page(href)
            continue

        # Pagination
        if "/page/" in href:

            discover_page(href)
            continue

        # Sistem səhifələrini keç
        ignored = [
            "/giris/",
            "/kayit/",
            "/iletisim/",
            "/hakkimizda/",
            "/gizlilik/",
            "/kvkk/",
            "/sitemap",
            "/etiket/",
            "/tag/",
            "/author/",
        ]

        if any(x in href.lower() for x in ignored):
            continue

        # Film səhifəsi
        film_pages.add(href)


def extract_streams(page_url, html):

    soup = BeautifulSoup(html, "html.parser")

    found = []

    # --------------------------------
    # VIDEO
    # --------------------------------

    for video in soup.find_all("video"):

        for attr in ["src", "data-src"]:

            src = video.get(attr)

            if src:

                src = urljoin(page_url, src)

                if ".m3u8" in src.lower() or ".mp4" in src.lower():
                    found.append(src)

    # --------------------------------
    # SOURCE
    # --------------------------------

    for source in soup.find_all("source"):

        for attr in ["src", "data-src"]:

            src = source.get(attr)

            if src:

                src = urljoin(page_url, src)

                if ".m3u8" in src.lower() or ".mp4" in src.lower():
                    found.append(src)

    # --------------------------------
    # IFRAME
    # --------------------------------

    for iframe in soup.find_all("iframe"):

        src = iframe.get("src")

        if not src:
            continue

        src = urljoin(page_url, src)

        print("    [IFRAME]", src)

        # iframe URL-ni də açıq şəkildə yoxla
        try:

            iframe_html = fetch(src)

            if iframe_html:

                for pattern in [
                    r'https?://[^"\'<>\s]+\.m3u8(?:\?[^"\'<>\s]*)?',
                    r'https?://[^"\'<>\s]+\.mp4(?:\?[^"\'<>\s]*)?',
                ]:

                    matches = re.findall(
                        pattern,
                        iframe_html,
                        re.I
                    )

                    found.extend(matches)

        except Exception as e:

            print("    [IFRAME ERROR]", e)

    # --------------------------------
    # HTML-də açıq M3U8 / MP4
    # --------------------------------

    patterns = [

        r'https?://[^"\'<>\s]+\.m3u8(?:\?[^"\'<>\s]*)?',

        r'https?://[^"\'<>\s]+\.mp4(?:\?[^"\'<>\s]*)?',

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.I
        )

        found.extend(matches)

    # təkrarları sil
    result = []

    for url in found:

        url = url.replace("\\/", "/")

        if url not in result:

            result.append(url)

    return result


def parse_film(url):

    print()
    print("=" * 70)
    print("[FILM]", url)
    print("=" * 70)

    html = fetch(url)

    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    # Film adı
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
        title = urlparse(url).path.strip("/").split("/")[-1]

    found = extract_streams(url, html)

    if not found:

        print("[NO OPEN STREAM]")

        return

    print()
    print("[STREAM FOUND]")

    for stream in found:

        print(stream)

        streams[title] = stream

        # İlk açıq stream kifayətdir
        break


def save_m3u():

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n\n")

        for title, url in sorted(streams.items()):

            title = title.replace('"', "'")

            f.write(
                f'#EXTINF:-1,{title}\n'
            )

            f.write(
                url + "\n"
            )

    print()
    print("=" * 70)
    print("M3U HAZIR")
    print("Film sayı:", len(streams))
    print("Fayl:", OUTPUT)
    print("=" * 70)


def main():

    print("=" * 70)
    print("720IZLE M3U SCRAPER")
    print("=" * 70)

    print()
    print("[1] Sayt və kateqoriyalar tapılır...")

    discover_page(BASE)

    print()
    print("=" * 70)
    print("TAPILAN SƏHİFƏLƏR:", len(film_pages))
    print("=" * 70)

    # İlk 300 film
    pages = list(film_pages)[:300]

    for i, url in enumerate(pages, 1):

        print()
        print(f"[{i}/{len(pages)}]")

        parse_film(url)

        time.sleep(0.5)

    save_m3u()


if __name__ == "__main__":
    main()
