import re
import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

BASE_URL = "https://filmmakinesi.to/"
OUTPUT = "films.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 20


def get(url):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        print(f"[HTTP {r.status_code}] {url}")

        return r

    except Exception as e:
        print("[ERROR]", url, e)
        return None


def same_domain(url):
    try:
        return urlparse(url).netloc == urlparse(BASE_URL).netloc
    except:
        return False


def movie_url(url):
    if not same_domain(url):
        return False

    path = urlparse(url).path.lower()

    if path in ("", "/"):
        return False

    blocked = [
        "/login",
        "/register",
        "/giris",
        "/kayit",
        "/search",
        "/arama",
        "/kategori",
        "/category",
        "/genre",
        "/tur",
        "/oyuncu",
        "/yonetmen",
        "/iletisim",
        "/hakkimizda",
        "/tag/",
        "/page/",
        "/sitemap",
        "/robots.txt",
    ]

    for x in blocked:
        if x in path:
            return False

    extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".css",
        ".js",
        ".json",
        ".xml",
        ".txt",
    )

    if path.endswith(extensions):
        return False

    return True


def robots_sitemaps():

    print()
    print("=" * 60)
    print("ROBOTS / SITEMAP")
    print("=" * 60)

    urls = [
        urljoin(BASE_URL, "robots.txt"),
        urljoin(BASE_URL, "sitemap.xml"),
        urljoin(BASE_URL, "sitemap_index.xml"),
        urljoin(BASE_URL, "wp-sitemap.xml"),
    ]

    sitemaps = set()

    for url in urls:

        r = get(url)

        if not r or r.status_code != 200:
            continue

        text = r.text

        # robots.txt
        for line in text.splitlines():

            if line.lower().startswith("sitemap:"):

                sitemap = line.split(":", 1)[1].strip()

                if sitemap:
                    print("[SITEMAP]", sitemap)
                    sitemaps.add(sitemap)

        # XML
        try:

            root = ET.fromstring(text)

            for element in root.iter():

                if element.tag.lower().endswith("loc"):

                    if element.text:

                        value = element.text.strip()

                        if value.startswith("http"):
                            sitemaps.add(value)

        except:
            pass

    return sitemaps


def read_sitemap(sitemap):

    r = get(sitemap)

    if not r or r.status_code != 200:
        return set()

    urls = set()

    try:

        root = ET.fromstring(r.text)

        for element in root.iter():

            if element.tag.lower().endswith("loc"):

                if element.text:

                    value = element.text.strip()

                    if value.startswith("http"):
                        urls.add(value)

    except Exception as e:

        print(
            "[XML ERROR]",
            sitemap,
            e
        )

    return urls


def discover_movies():

    movie_pages = set()

    sitemaps = robots_sitemaps()

    print()
    print("=" * 60)
    print("SITEMAP-LƏR OXUNUR")
    print("=" * 60)

    for sitemap in sitemaps:

        urls = read_sitemap(sitemap)

        print(
            sitemap,
            "->",
            len(urls),
            "URL"
        )

        for url in urls:

            if movie_url(url):
                movie_pages.add(url)

    # Ana səhifə
    if not movie_pages:

        print()
        print("=" * 60)
        print("ANA SƏHİFƏ YOXLAMASI")
        print("=" * 60)

        r = get(BASE_URL)

        if r and r.status_code == 200:

            matches = re.findall(
                r'href=["\']([^"\']+)["\']',
                r.text,
                re.I
            )

            for href in matches:

                full = urljoin(
                    r.url,
                    href
                )

                if movie_url(full):
                    movie_pages.add(full)

    return movie_pages


def extract_player(movie):

    print()
    print("[FILM]")
    print(movie)

    r = get(movie)

    if not r or r.status_code != 200:
        return []

    html = r.text

    players = set()

    patterns = [

        r'<iframe[^>]+src=["\']([^"\']+)["\']',

        r'<video[^>]+src=["\']([^"\']+)["\']',

        r'<source[^>]+src=["\']([^"\']+)["\']',

        r'<embed[^>]+src=["\']([^"\']+)["\']',

        r'data-src=["\']([^"\']+)["\']',

        r'data-url=["\']([^"\']+)["\']',

        r'data-video=["\']([^"\']+)["\']',

        r'data-player=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:

        for value in re.findall(
            pattern,
            html,
            re.I
        ):

            value = urljoin(
                movie,
                value
            )

            if value.startswith("http"):
                players.add(value)

    # HTML daxilində açıq URL-lər
    urls = re.findall(
        r'https?://[^"\'<>\s]+',
        html,
        re.I
    )

    keywords = [
        "m3u8",
        "mp4",
        "mpd",
        "player",
        "embed",
        "video",
        "stream",
        "iframe",
    ]

    for url in urls:

        low = url.lower()

        if any(
            x in low
            for x in keywords
        ):
            players.add(url)

    return sorted(players)


def create_m3u(results):

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for title, player in results:

            f.write(
                f"#EXTINF:-1,{title}\n"
            )

            f.write(
                player + "\n"
            )


def main():

    print("=" * 70)
    print("FILMMAKINESI PLAYER SCRAPER")
    print("=" * 70)

    movies = discover_movies()

    print()
    print("=" * 70)
    print("FILM SƏHİFƏLƏRİ:", len(movies))
    print("=" * 70)

    results = []

    for index, movie in enumerate(
        sorted(movies),
        1
    ):

        print(
            f"\n[{index}/{len(movies)}]"
        )

        players = extract_player(movie)

        title = (
            urlparse(movie)
            .path
            .strip("/")
            .split("/")[-1]
        )

        title = title.replace(
            "-",
            " "
        )

        for player in players:

            print(
                "[PLAYER]",
                player
            )

            results.append(
                (
                    title,
                    player
                )
            )

    # duplicate URL-ləri sil
    unique = []
    seen = set()

    for title, player in results:

        if player in seen:
            continue

        seen.add(player)

        unique.append(
            (
                title,
                player
            )
        )

    create_m3u(unique)

    print()
    print("=" * 70)
    print("M3U HAZIRDIR")
    print("=" * 70)
    print("FILMLƏR:", len(movies))
    print("PLAYER URL:", len(unique))
    print("FILE:", OUTPUT)
    print("=" * 70)


if __name__ == "__main__":
    main()
