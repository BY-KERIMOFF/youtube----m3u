import re
import time
import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

BASE_URL = "https://filmmakinesi.to/"
OUTPUT = "films.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

TIMEOUT = 20
DELAY = 0.5  # saniyə - saytı yormamaq üçün

# Saytın film URL strukturu (filmmakinesi.to üçün)
MOVIE_PATTERNS = [
    re.compile(r"^/[^/]+-\d{4}(?:-\d+)?/?$"),      # /film-adi-2023/
    re.compile(r"^/film/[^/]+/?$"),                  # /film/film-adi/
    re.compile(r"^/izle/[^/]+/?$"),                  # /izle/film-adi/
    re.compile(r"^/[a-z0-9-]+-\d{4}-izle/?$"),       # /film-adi-2023-izle/
    re.compile(r"^/[a-z0-9-]+/?$"),                  # ümumi slug (son fallback)
]

BLOCKED_PATHS = [
    "/login", "/register", "/giris", "/kayit", "/uye",
    "/search", "/arama", "/kategori", "/category",
    "/genre", "/tur", "/oyuncu", "/actor", "/yonetmen",
    "/iletisim", "/contact", "/hakkimizda", "/about",
    "/tag/", "/etiket/", "/page/", "/sayfa/",
    "/sitemap", "/robots.txt", "/feed", "/rss",
    "/wp-", "/api/", "/ajax/", "/assets/",
    "/static/", "/css/", "/js/", "/images/",
    "/dizi", "/series", "/tv",  # film istəyiriksə, serialları blokla
]

BLOCKED_EXT = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".css", ".js", ".json", ".xml", ".txt", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".pdf",
    ".zip", ".rar", ".mp4", ".m3u8", ".mpd",  # media faylları
)


def get(url, retries=2):
    """HTTP GET with retry"""
    for attempt in range(retries + 1):
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            print(f"[HTTP {r.status_code}] {url}")
            if r.status_code == 200:
                return r
            if r.status_code in (403, 429, 503):
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")
            time.sleep(1)
    return None


def same_domain(url):
    try:
        return urlparse(url).netloc == urlparse(BASE_URL).netloc
    except Exception:
        return False


def is_movie_url(url):
    """Saytın film URL strukturu ilə uyğunluğu yoxla"""
    if not same_domain(url):
        return False

    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")

    if not path or path == "":
        return False

    # Bloklanmış yollar
    for blocked in BLOCKED_PATHS:
        if blocked in path:
            return False

    # Fayl uzantıları
    if path.endswith(BLOCKED_EXT):
        return False

    # Çox dərin yolları blokla (məs. /a/b/c/d/e)
    if path.count("/") > 3:
        return False

    # Film pattern-lərindən birinə uyğun olmalı
    for pattern in MOVIE_PATTERNS:
        if pattern.match(path):
            return True

    return False


def robots_sitemaps():
    """robots.txt və sitemap-ləri tap"""
    print("\n" + "=" * 60)
    print("ROBOTS / SITEMAP")
    print("=" * 60)

    candidates = [
        urljoin(BASE_URL, "robots.txt"),
        urljoin(BASE_URL, "sitemap.xml"),
        urljoin(BASE_URL, "sitemap_index.xml"),
        urljoin(BASE_URL, "sitemap-index.xml"),
        urljoin(BASE_URL, "wp-sitemap.xml"),
        urljoin(BASE_URL, "sitemap1.xml"),
    ]

    sitemaps = set()

    for url in candidates:
        r = get(url)
        if not r or r.status_code != 200:
            continue

        text = r.text

        # robots.txt
        for line in text.splitlines():
            if line.lower().startswith("sitemap:"):
                sm = line.split(":", 1)[1].strip()
                if sm:
                    print(f"[SITEMAP] {sm}")
                    sitemaps.add(sm)

        # XML sitemap
        try:
            root = ET.fromstring(text)
            for el in root.iter():
                if el.tag.lower().endswith("loc") and el.text:
                    val = el.text.strip()
                    if val.startswith("http"):
                        sitemaps.add(val)
        except Exception:
            pass

    return sitemaps


def read_sitemap(sitemap):
    """Sitemap oxu (gzip dəstəyi ilə)"""
    r = get(sitemap)
    if not r or r.status_code != 200:
        return set()

    urls = set()
    try:
        root = ET.fromstring(r.content)
        for el in root.iter():
            if el.tag.lower().endswith("loc") and el.text:
                val = el.text.strip()
                if val.startswith("http"):
                    urls.add(val)
    except Exception as e:
        print(f"[XML ERROR] {sitemap} -> {e}")

    return urls


def get_movie_title(html, url):
    """Film başlığını HTML-dən çıxar"""
    # <title> teqi
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        title = m.group(1).strip()
        # Sayt adını təmizlə
        title = re.split(r"\s*[-–|]\s*(?:FilmMakinesi|Full|İzle)", title, flags=re.I)[0]
        if title and len(title) > 2:
            return title.strip()

    # og:title
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if m:
        return m.group(1).strip()

    # h1
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.I)
    if m:
        return m.group(1).strip()

    # URL fallback
    return urlparse(url).path.strip("/").split("/")[-1].replace("-", " ").title()


def discover_movies():
    """Film səhifələrini tap - çoxmərhələli"""
    movie_pages = set()
    sitemaps = robots_sitemaps()

    # 1. Sitemap-lərdən
    print("\n" + "=" * 60)
    print("SITEMAP-LƏR OXUNUR")
    print("=" * 60)

    for sitemap in sitemaps:
        urls = read_sitemap(sitemap)
        print(f"{sitemap} -> {len(urls)} URL")
        for u in urls:
            if is_movie_url(u):
                movie_pages.add(u)

    # 2. Ana səhifə + pagination
    print("\n" + "=" * 60)
    print("ANA SƏHİFƏ + PAGINATION")
    print("=" * 60)

    page = 1
    max_pages = 50
    empty_streak = 0

    while page <= max_pages:
        if page == 1:
            url = BASE_URL
        else:
            url = urljoin(BASE_URL, f"page/{page}/")

        r = get(url)
        if not r or r.status_code != 200:
            break

        html = r.text
        found = 0

        # Bütün linkləri tap
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
        for href in hrefs:
            full = urljoin(r.url, href)
            if is_movie_url(full) and full not in movie_pages:
                movie_pages.add(full)
                found += 1

        print(f"[PAGE {page}] +{found} yeni film (cəmi: {len(movie_pages)})")

        if found == 0:
            empty_streak += 1
            if empty_streak >= 3:
                break
        else:
            empty_streak = 0

        # Növbəti səhifə linkini yoxla
        next_match = re.search(
            r'<a[^>]+href=["\']([^"\']*page/' + str(page + 1) + r'/?[^"\']*)["\']',
            html, re.I,
        )
        if not next_match and page > 1:
            # rel=next yoxla
            next_match = re.search(
                r'<a[^>]+rel=["\']next["\'][^>]+href=["\']([^"\']+)["\']',
                html, re.I,
            )
            if not next_match:
                break

        page += 1
        time.sleep(DELAY)

    return movie_pages


def extract_player(movie):
    """Film səhifəsindən player linklərini çıxar"""
    print(f"\n[FILM] {movie}")

    r = get(movie)
    if not r or r.status_code != 200:
        return None, []

    html = r.text
    title = get_movie_title(html, movie)
    players = set()

    # iframe / video / source / embed
    patterns = [
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        r'<video[^>]+src=["\']([^"\']+)["\']',
        r'<source[^>]+src=["\']([^"\']+)["\']',
        r'<embed[^>]+src=["\']([^"\']+)["\']',
        r'data-src=["\']([^"\']+)["\']',
        r'data-url=["\']([^"\']+)["\']',
        r'data-video=["\']([^"\']+)["\']',
        r'data-player=["\']([^"\']+)["\']',
        r'data-iframe=["\']([^"\']+)["\']',
        r'data-litespeed-src=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        for value in re.findall(pattern, html, re.I):
            full = urljoin(movie, value)
            if full.startswith("http"):
                players.add(full)

    # JS içində m3u8/mp4 axtar
    js_patterns = [
        r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
        r'["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
        r'["\'](https?://[^"\']+\.mpd[^"\']*)["\']',
        r'file\s*:\s*["\']([^"\']+)["\']',
        r'source\s*:\s*["\']([^"\']+)["\']',
        r'["\']([^"\']*embed[^"\']*)["\']',
    ]
    for pattern in js_patterns:
        for value in re.findall(pattern, html, re.I):
            full = urljoin(movie, value)
            if full.startswith("http"):
                players.add(full)

    # Ümumi URL-lər (keyword filter)
    keywords = ["m3u8", "mp4", "mpd", "player", "embed", "video", "stream", "iframe"]
    for url in re.findall(r'https?://[^"\'<>\s]+', html, re.I):
        low = url.lower()
        if any(k in low for k in keywords):
            players.add(url)

    # Yalnız media/embed linklərini saxla (reklam filtrləri)
    clean = set()
    for p in players:
        low = p.lower()
        # Reklam/analitika filtrləri
        if any(x in low for x in [
            "google", "doubleclick", "facebook", "twitter",
            "analytics", "googletag", "adsystem", "adservice",
        ]):
            continue
        clean.add(p)

    return title, sorted(clean)


def create_m3u(results):
    """M3U8 faylı yarat"""
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, player in results:
            f.write(f'#EXTINF:-1,{title}\n')
            f.write(player + "\n")


def main():
    print("=" * 70)
    print("FILMMAKINESI PLAYER SCRAPER v2")
    print("=" * 70)

    movies = discover_movies()

    print("\n" + "=" * 70)
    print(f"FILM SƏHİFƏLƏRİ: {len(movies)}")
    print("=" * 70)

    results = []
    for index, movie in enumerate(sorted(movies), 1):
        print(f"\n[{index}/{len(movies)}]")
        title, players = extract_player(movie)

        if not title:
            continue

        for player in players:
            print(f"[PLAYER] {player}")
            results.append((title, player))

        time.sleep(DELAY)

    # Duplicate URL-ləri sil
    unique = []
    seen = set()
    for title, player in results:
        if player in seen:
            continue
        seen.add(player)
        unique.append((title, player))

    create_m3u(unique)

    print("\n" + "=" * 70)
    print("M3U HAZIRDIR")
    print("=" * 70)
    print(f"FILMLƏR:       {len(movies)}")
    print(f"PLAYER URL:    {len(unique)}")
    print(f"FILE:          {OUTPUT}")
    print("=" * 70)


if __name__ == "__main__":
    main()
