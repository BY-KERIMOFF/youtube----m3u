import re
import json
import time
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://720izle.com/"
OUTPUT_FILE = "films.m3u"

MAX_PAGES = 500
TIMEOUT = 20
DELAY = 0.3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


session = requests.Session()
session.headers.update(HEADERS)


# =========================================================
# URL
# =========================================================

def normalize_url(url, base=BASE_URL):

    if not url:
        return None

    url = str(url).strip()

    if not url:
        return None

    url = url.replace("\\/", "/")
    url = url.replace("&amp;", "&")

    if url.startswith("//"):
        url = "https:" + url

    elif not url.startswith(("http://", "https://")):
        url = urljoin(base, url)

    url, _ = urldefrag(url)

    return url


def same_domain(url):

    try:
        host = urlparse(url).netloc.lower()
        base = urlparse(BASE_URL).netloc.lower()

        return (
            host == base
            or host.endswith("." + base)
        )

    except Exception:
        return False


# =========================================================
# HTTP
# =========================================================

def get_page(url):

    try:

        r = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        print(f"[HTTP {r.status_code}] {url}")

        if r.status_code != 200:
            return None

        return r.text

    except Exception as e:

        print(f"[ERROR] {url}")
        print(e)

        return None


# =========================================================
# TITLE
# =========================================================

def get_title(html, url):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    h1 = soup.find("h1")

    if h1:

        title = h1.get_text(
            " ",
            strip=True
        )

        if title:
            return title

    meta = soup.find(
        "meta",
        attrs={"property": "og:title"}
    )

    if meta:

        title = meta.get("content")

        if title:
            return title.strip()

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

        if title:
            return title

    path = urlparse(url).path.strip("/")

    if path:

        return path.split("/")[-1]

    return "Unknown"


# =========================================================
# LINK DISCOVERY
# =========================================================

def extract_links(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = set()

    for tag in soup.find_all(
        "a",
        href=True
    ):

        url = normalize_url(
            tag.get("href")
        )

        if not url:
            continue

        if not same_domain(url):
            continue

        path = urlparse(url).path.lower()

        ignored = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".css",
            ".js",
            ".xml",
            ".pdf",
            ".zip",
        )

        if path.endswith(ignored):
            continue

        links.add(url)

    return links


# =========================================================
# PLAYER URL CHECK
# =========================================================

def looks_like_player_url(url):

    if not url:
        return False

    lower = url.lower()

    # Bunlar birbaşa media URL-ləri
    media_extensions = (
        ".m3u8",
        ".mp4",
        ".m4v",
        ".webm",
        ".mpd",
        ".mov",
        ".ts",
    )

    if any(
        ext in lower
        for ext in media_extensions
    ):
        return True

    # Player / embed URL-ləri
    keywords = (
        "player",
        "embed",
        "video",
        "stream",
        "play",
        "watch",
        "iframe",
    )

    if any(
        x in lower
        for x in keywords
    ):
        return True

    return False


# =========================================================
# PLAYER URL EXTRACTION
# =========================================================

def extract_player_urls(html, page_url):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    found = set()

    # -----------------------------------------------------
    # IFRAME
    # -----------------------------------------------------

    for iframe in soup.find_all("iframe"):

        attrs = [
            "src",
            "data-src",
            "data-url",
            "data-video",
            "data-player",
            "data-embed",
        ]

        for attr in attrs:

            value = iframe.get(attr)

            if not value:
                continue

            value = normalize_url(
                value,
                page_url
            )

            if value:
                found.add(value)

    # -----------------------------------------------------
    # VIDEO
    # -----------------------------------------------------

    for video in soup.find_all("video"):

        attrs = [
            "src",
            "data-src",
            "data-url",
            "data-video",
            "data-file",
        ]

        for attr in attrs:

            value = video.get(attr)

            if not value:
                continue

            value = normalize_url(
                value,
                page_url
            )

            if value:
                found.add(value)

    # -----------------------------------------------------
    # SOURCE
    # -----------------------------------------------------

    for source in soup.find_all("source"):

        attrs = [
            "src",
            "data-src",
            "data-url",
            "data-file",
            "data-video",
        ]

        for attr in attrs:

            value = source.get(attr)

            if not value:
                continue

            value = normalize_url(
                value,
                page_url
            )

            if value:
                found.add(value)

    # -----------------------------------------------------
    # OBJECT / EMBED
    # -----------------------------------------------------

    for tag in soup.find_all(
        ["object", "embed"]
    ):

        for attr in [
            "src",
            "data",
            "data-src",
            "data-url",
        ]:

            value = tag.get(attr)

            if not value:
                continue

            value = normalize_url(
                value,
                page_url
            )

            if value:
                found.add(value)

    # -----------------------------------------------------
    # DATA ATTRIBUTES
    # -----------------------------------------------------

    for tag in soup.find_all(True):

        for attr, value in tag.attrs.items():

            if not attr.startswith("data-"):
                continue

            if isinstance(value, list):
                value = " ".join(value)

            if not isinstance(value, str):
                continue

            value = value.strip()

            if not value:
                continue

            # Əgər data attribute URL-dirsə
            if (
                value.startswith("http://")
                or value.startswith("https://")
                or value.startswith("//")
                or value.startswith("/")
            ):

                url = normalize_url(
                    value,
                    page_url
                )

                if url:
                    found.add(url)

    # -----------------------------------------------------
    # ABSOLUTE URL-lər
    # -----------------------------------------------------

    patterns = [

        # http/https URL
        r'https?://[^"\'>\s\\]+',

        # protocol-relative
        r'//[^"\'>\s\\]+',

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.IGNORECASE
        )

        for value in matches:

            value = (
                value
                .replace("\\/", "/")
                .replace("&amp;", "&")
            )

            url = normalize_url(
                value,
                page_url
            )

            if not url:
                continue

            # yalnız player/media tipli URL-lər
            if looks_like_player_url(url):

                found.add(url)

    return found


# =========================================================
# JAVASCRIPT PLAYER CONFIG
# =========================================================

def extract_js_player_data(html, page_url):

    found = set()

    decoded = (
        html
        .replace("\\/", "/")
        .replace("\\u002F", "/")
        .replace("\\u002f", "/")
        .replace("&amp;", "&")
        .replace("\\u0026", "&")
    )

    # -----------------------------------------------------
    # JSON kimi görünən URL-lər
    # -----------------------------------------------------

    patterns = [

        r'"(?:src|file|url|source|video|stream|embed|player)"\s*:\s*"([^"]+)"',

        r"'(?:src|file|url|source|video|stream|embed|player)'\s*:\s*'([^']+)'",

        r'(?:src|file|url|source|video|stream|embed|player)\s*=\s*["\']([^"\']+)["\']',

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            decoded,
            re.IGNORECASE
        )

        for value in matches:

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # URL-ləri ümumi regex ilə də tap
    # -----------------------------------------------------

    matches = re.findall(
        r'https?://[^"\'>\s\\]+',
        decoded,
        re.IGNORECASE
    )

    for value in matches:

        value = value.rstrip(
            ".,);}]"
        )

        url = normalize_url(
            value,
            page_url
        )

        if not url:
            continue

        if looks_like_player_url(url):

            found.add(url)

    return found


# =========================================================
# FILM PAGE
# =========================================================

def is_film_page(url):

    path = urlparse(url).path.lower()

    return "/filmler" in path


# =========================================================
# CRAWLER
# =========================================================

def crawl():

    queue = [
        BASE_URL
    ]

    visited = set()

    film_pages = set()

    while queue and len(visited) < MAX_PAGES:

        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        print()
        print(
            f"[SCAN {len(visited)}/{MAX_PAGES}] "
            f"{url}"
        )

        html = get_page(url)

        if not html:
            continue

        links = extract_links(html)

        print(
            f"[+] Linklər: {len(links)}"
        )

        for link in links:

            # Film səhifəsi
            if is_film_page(link):

                film_pages.add(link)

            # Saytı gəzməyə davam et
            if (
                link not in visited
                and link not in queue
            ):

                path = urlparse(
                    link
                ).path.lower()

                # Kateqoriya
                if (
                    "/kategori/" in path
                    or "/category/" in path
                    or "/page/" in path
                    or "/filmler" in path
                ):

                    queue.append(link)

        time.sleep(DELAY)

    return film_pages


# =========================================================
# PROCESS FILMS
# =========================================================

def process_films(film_pages):

    results = []

    print()
    print("=" * 70)
    print(
        f"FILM SAYI: {len(film_pages)}"
    )
    print("=" * 70)

    for index, url in enumerate(
        sorted(film_pages),
        1
    ):

        print()
        print(
            f"[FILM {index}/{len(film_pages)}]"
        )

        print(url)

        html = get_page(url)

        if not html:
            continue

        title = get_title(
            html,
            url
        )

        print(
            f"[TITLE] {title}"
        )

        # Player URL-ləri
        urls = extract_player_urls(
            html,
            url
        )

        # JavaScript player məlumatları
        js_urls = extract_js_player_data(
            html,
            url
        )

        urls.update(js_urls)

        # Eyni saytın adi linklərini çıxar
        cleaned = set()

        for player_url in urls:

            if not player_url:
                continue

            lower = player_url.lower()

            # şəkil/css/js kimi faylları at
            if lower.endswith((
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".css",
                ".js",
            )):
                continue

            cleaned.add(
                player_url
            )

        if cleaned:

            print(
                f"[PLAYER URL] {len(cleaned)}"
            )

            for player_url in sorted(
                cleaned
            ):

                print(
                    f"   -> {player_url}"
                )

                results.append({
                    "title": title,
                    "url": player_url,
                    "page": url,
                })

        else:

            print(
                "[NO PLAYER URL]"
            )

        time.sleep(DELAY)

    return results


# =========================================================
# WRITE M3U
# =========================================================

def write_m3u(results):

    unique = set()

    final = []

    for item in results:

        title = item["title"]
        url = item["url"]

        key = (
            title.strip().lower(),
            url.strip()
        )

        if key in unique:
            continue

        unique.add(key)

        final.append(
            (title, url)
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "#EXTM3U\n"
        )

        for title, url in final:

            title = (
                title
                .replace("\n", " ")
                .replace("\r", " ")
            )

            f.write(
                f"#EXTINF:-1,{title}\n"
            )

            f.write(
                url.strip()
                + "\n"
            )

    print()
    print("=" * 70)
    print(
        f"M3U HAZIRDIR: {OUTPUT_FILE}"
    )
    print(
        f"TOTAL PLAYER URL: {len(final)}"
    )
    print("=" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("720IZLE PLAYER URL SCRAPER")
    print("=" * 70)

    print()
    print(
        "[1] Film səhifələri tapılır..."
    )

    film_pages = crawl()

    print()
    print(
        f"[INFO] Film səhifələri: "
        f"{len(film_pages)}"
    )

    print()
    print(
        "[2] Player URL-ləri çıxarılır..."
    )

    results = process_films(
        film_pages
    )

    print()
    print(
        "[3] films.m3u yaradılır..."
    )

    write_m3u(
        results
    )


if __name__ == "__main__":
    main()
