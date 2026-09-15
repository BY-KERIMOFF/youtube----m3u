import re
import time
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://720izle.com/"
OUTPUT_FILE = "films.m3u"

MAX_PAGES = 500
REQUEST_TIMEOUT = 20
DELAY = 0.3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

session = requests.Session()
session.headers.update(HEADERS)


def normalize_url(url):
    if not url:
        return None

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = urljoin(BASE_URL, url)

    url, _ = urldefrag(url)

    return url


def is_same_domain(url):
    try:
        host = urlparse(url).netloc.lower()
        base_host = urlparse(BASE_URL).netloc.lower()

        return host == base_host or host.endswith("." + base_host)

    except Exception:
        return False


def get_page(url):
    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        print(f"[HTTP {response.status_code}] {url}")

        if response.status_code != 200:
            return None

        return response.text

    except requests.RequestException as e:
        print(f"[ERROR] {url} -> {e}")
        return None


def is_stream_url(url):
    if not url:
        return False

    lower = url.lower()

    return ".m3u8" in lower or ".mp4" in lower


def extract_streams(html):
    streams = set()

    soup = BeautifulSoup(html, "html.parser")

    # video
    for tag in soup.find_all("video"):
        for attr in ["src", "data-src", "data-url", "data-file"]:
            value = tag.get(attr)

            if value:
                value = normalize_url(value)

                if is_stream_url(value):
                    streams.add(value)

    # source
    for tag in soup.find_all("source"):
        for attr in ["src", "data-src", "data-url", "data-file"]:
            value = tag.get(attr)

            if value:
                value = normalize_url(value)

                if is_stream_url(value):
                    streams.add(value)

    # iframe
    for tag in soup.find_all("iframe"):
        src = tag.get("src")

        if src:
            src = normalize_url(src)

            if is_stream_url(src):
                streams.add(src)

    # HTML içində birbaşa m3u8/mp4
    patterns = [
        r'https?://[^"\'>\s\\]+\.m3u8(?:\?[^"\'>\s\\]*)?',
        r'https?://[^"\'>\s\\]+\.mp4(?:\?[^"\'>\s\\]*)?',
    ]

    decoded = (
        html
        .replace("\\/", "/")
        .replace("&amp;", "&")
        .replace("\\u0026", "&")
    )

    for pattern in patterns:
        for url in re.findall(
            pattern,
            decoded,
            re.IGNORECASE
        ):
            if is_stream_url(url):
                streams.add(url)

    return streams


def get_title(html, url):
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)

        if title:
            return title

    if soup.title:
        title = soup.title.get_text(" ", strip=True)

        if title:
            return title

    return urlparse(url).path.strip("/").split("/")[-1]


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")

    links = set()

    for tag in soup.find_all("a", href=True):

        href = normalize_url(tag.get("href"))

        if not href:
            continue

        if not is_same_domain(href):
            continue

        path = urlparse(href).path.lower()

        if path.endswith((
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".css",
            ".js",
            ".xml",
            ".pdf",
            ".zip",
        )):
            continue

        links.add(href)

    return links


def crawl_site():
    queue = [BASE_URL]
    visited = set()
    pages = set()

    while queue and len(visited) < MAX_PAGES:

        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        print()
        print(f"[SCAN {len(visited)}/{MAX_PAGES}] {url}")

        html = get_page(url)

        if not html:
            continue

        links = extract_links(html)

        print(f"[+] Linklər: {len(links)}")

        for link in links:

            path = urlparse(link).path.lower()

            # Kateqoriya / pagination
            if (
                "/kategori/" in path
                or "/category/" in path
                or "/page/" in path
            ):
                if link not in visited and link not in queue:
                    queue.append(link)

                continue

            # Digər same-domain səhifələri film namizədi kimi saxla
            if link != BASE_URL:
                pages.add(link)

            if link not in visited and link not in queue:
                queue.append(link)

    return pages


def process_pages(pages):

    results = []

    total = len(pages)

    print()
    print("=" * 60)
    print(f"FILM SƏHİFƏLƏRİ: {total}")
    print("=" * 60)

    for index, url in enumerate(pages, 1):

        print()
        print(f"[FILM {index}/{total}]")
        print(url)

        html = get_page(url)

        if not html:
            continue

        title = get_title(html, url)

        streams = extract_streams(html)

        if streams:

            print(f"[FOUND] {title}")

            for stream in streams:

                print(f" -> {stream}")

                results.append(
                    (title, stream)
                )

        else:

            print(
                f"[NO STREAM] {title}"
            )

        time.sleep(DELAY)

    return results


def write_m3u(results):

    unique = set()
    final = []

    for title, stream in results:

        key = (title.lower(), stream)

        if key in unique:
            continue

        unique.add(key)

        final.append(
            (title, stream)
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for title, stream in final:

            title = (
                title
                .replace("\n", " ")
                .replace("\r", " ")
            )

            f.write(
                f"#EXTINF:-1,{title}\n"
            )

            f.write(
                stream + "\n"
            )

    print()
    print("=" * 60)
    print(f"M3U HAZIRDIR: {OUTPUT_FILE}")
    print(f"STREAM SAYI: {len(final)}")
    print("=" * 60)


def main():

    print("=" * 60)
    print("720IZLE M3U SCRAPER")
    print("=" * 60)

    print()
    print("[1] Sayt taranır...")

    pages = crawl_site()

    print()
    print(f"[INFO] Səhifə sayı: {len(pages)}")

    print()
    print("[2] Stream linkləri axtarılır...")

    results = process_pages(pages)

    print()
    print("[3] M3U yaradılır...")

    write_m3u(results)


if __name__ == "__main__":
    main()
