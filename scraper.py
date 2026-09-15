import re
import time
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.hdfilmcehennemi.nl/"
OUTPUT_FILE = "films.m3u"

MAX_PAGES = 500
TIMEOUT = 20
DELAY = 0.5

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

    url = (
        url
        .replace("\\/", "/")
        .replace("&amp;", "&")
    )

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

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        print(
            f"[HTTP {response.status_code}] {url}"
        )

        if response.status_code != 200:
            return None

        return response.text

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
        attrs={
            "property": "og:title"
        }
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
# FILM URL
# =========================================================

def is_film_page(url):

    path = urlparse(url).path.lower()

    # HDFilmCehennemi-də film URL-lərinin
    # əsas hissəsi slug şəklindədir.
    #
    # Buna görə yalnız kateqoriya və sistem
    # səhifələrini çıxarırıq.

    blocked = (
        "/kategori/",
        "/category/",
        "/page/",
        "/tag/",
        "/etiket/",
        "/search/",
        "/iletisim",
        "/hakkimizda",
        "/giris",
        "/kayit",
        "/login",
        "/register",
    )

    if any(
        item in path
        for item in blocked
    ):
        return False

    if not path or path == "/":
        return False

    return True


# =========================================================
# PLAYER URL
# =========================================================

def player_candidate(url):

    if not url:
        return False

    low = url.lower()

    keywords = (
        "player",
        "embed",
        "iframe",
        "video",
        "stream",
        "watch",
        "play",
        "rapidrame",
    )

    media = (
        ".m3u8",
        ".mp4",
        ".m4v",
        ".webm",
        ".mpd",
        ".mov",
        ".ts",
    )

    if any(x in low for x in media):
        return True

    if any(x in low for x in keywords):
        return True

    return False


# =========================================================
# EXTRACT PLAYER
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

    for iframe in soup.find_all(
        "iframe"
    ):

        for attr in (
            "src",
            "data-src",
            "data-url",
            "data-video",
            "data-player",
            "data-embed",
        ):

            value = iframe.get(attr)

            if not value:
                continue

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # VIDEO
    # -----------------------------------------------------

    for video in soup.find_all(
        "video"
    ):

        for attr in (
            "src",
            "data-src",
            "data-url",
            "data-video",
            "data-file",
        ):

            value = video.get(attr)

            if not value:
                continue

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # SOURCE
    # -----------------------------------------------------

    for source in soup.find_all(
        "source"
    ):

        for attr in (
            "src",
            "data-src",
            "data-url",
            "data-file",
            "data-video",
        ):

            value = source.get(attr)

            if not value:
                continue

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # OBJECT / EMBED
    # -----------------------------------------------------

    for tag in soup.find_all(
        ["object", "embed"]
    ):

        for attr in (
            "src",
            "data",
            "data-src",
            "data-url",
        ):

            value = tag.get(attr)

            if not value:
                continue

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # DATA ATTRIBUTES
    # -----------------------------------------------------

    for tag in soup.find_all(True):

        for attr, value in tag.attrs.items():

            if not attr.startswith(
                "data-"
            ):
                continue

            if isinstance(value, list):
                value = " ".join(value)

            if not isinstance(
                value,
                str
            ):
                continue

            if not (
                value.startswith("http")
                or value.startswith("//")
                or value.startswith("/")
            ):
                continue

            url = normalize_url(
                value,
                page_url
            )

            if url:
                found.add(url)

    # -----------------------------------------------------
    # JAVASCRIPT URL
    # -----------------------------------------------------

    decoded = (
        html
        .replace("\\/", "/")
        .replace("\\u002F", "/")
        .replace("\\u002f", "/")
        .replace("\\u0026", "&")
        .replace("&amp;", "&")
    )

    patterns = [

        r'https?://[^"\'>\s\\]+',

        r'//[^"\'>\s\\]+',

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
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

            if player_candidate(url):
                found.add(url)

    return found


# =========================================================
# CRAWLER
# =========================================================

def crawl_site():

    queue = [
        BASE_URL
    ]

    visited = set()
    film_pages = set()

    while (
        queue
        and len(visited) < MAX_PAGES
    ):

        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        print()
        print(
            f"[SCAN {len(visited)}/{MAX_PAGES}]"
        )
        print(url)

        html = get_page(url)

        if not html:
            continue

        links = extract_links(html)

        print(
            f"[+] Linklər: {len(links)}"
        )

        for link in links:

            if is_film_page(link):

                film_pages.add(link)

            path = urlparse(
                link
            ).path.lower()

            # Saytı daha dərindən gəzmək
            if (
                link not in visited
                and link not in queue
                and (
                    "/kategori/" in path
                    or "/category/" in path
                    or "/page/" in path
                    or "/filmler" in path
                    or link == BASE_URL
                )
            ):

                queue.append(link)

        time.sleep(DELAY)

    return film_pages


# =========================================================
# PROCESS
# =========================================================

def process_films(film_pages):

    results = []

    pages = sorted(
        film_pages
    )

    print()
    print("=" * 70)
    print(
        f"FILM SAYI: {len(pages)}"
    )
    print("=" * 70)

    for index, url in enumerate(
        pages,
        1
    ):

        print()
        print(
            f"[FILM {index}/{len(pages)}]"
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

        players = extract_player_urls(
            html,
            url
        )

        # lazımsız faylları çıxart
        cleaned = set()

        for player in players:

            low = player.lower()

            if low.endswith((
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".css",
                ".js",
            )):
                continue

            cleaned.add(player)

        if cleaned:

            print(
                f"[PLAYER] {len(cleaned)}"
            )

            for player in sorted(
                cleaned
            ):

                print(
                    f" -> {player}"
                )

                results.append({
                    "title": title,
                    "url": player,
                    "page": url,
                })

        else:

            print(
                "[NO PLAYER URL]"
            )

        time.sleep(DELAY)

    return results


# =========================================================
# M3U
# =========================================================

def write_m3u(results):

    unique = set()
    final = []

    for item in results:

        title = item["title"]
        url = item["url"]

        key = (
            title.lower().strip(),
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
        f"TOTAL: {len(final)}"
    )
    print("=" * 70)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print(
        "HDFILMCEHENNEMI PLAYER SCRAPER"
    )
    print("=" * 70)

    print()
    print(
        "[1] Film səhifələri tapılır..."
    )

    films = crawl_site()

    print()
    print(
        f"[INFO] Film səhifəsi: {len(films)}"
    )

    print()
    print(
        "[2] Player URL-ləri çıxarılır..."
    )

    results = process_films(
        films
    )

    print()
    print(
        "[3] M3U yaradılır..."
    )

    write_m3u(
        results
    )


if __name__ == "__main__":
    main()
