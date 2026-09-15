import re
import time
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = "https://www.hdfilmcehennemi.nl/"
MAX_PAGES = 100
OUTPUT = "films.m3u"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}


def same_domain(url):
    try:
        return urlparse(url).netloc == urlparse(BASE_URL).netloc
    except Exception:
        return False


def normalize(url):
    if not url:
        return ""

    url = url.strip()

    if url.startswith("//"):
        url = "https:" + url

    return url


def looks_like_movie(url):
    if not same_domain(url):
        return False

    path = urlparse(url).path.lower()

    if not path or path == "/":
        return False

    blocked = [
        "/kategori/",
        "/category/",
        "/tur/",
        "/genre/",
        "/oyuncu/",
        "/yonetmen/",
        "/iletisim",
        "/hakkimizda",
        "/giris",
        "/kayit",
        "/login",
        "/register",
        "/search",
        "/arama",
        "/wp-",
        "/tag/",
        "/page/",
    ]

    for x in blocked:
        if x in path:
            return False

    extensions = (
        ".css",
        ".js",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".webp",
        ".xml",
        ".json",
        ".txt",
    )

    if path.endswith(extensions):
        return False

    return True


def clean_url(url):
    url = normalize(url)

    if not url:
        return ""

    if url.startswith("javascript:"):
        return ""

    if url.startswith("data:"):
        return ""

    if url.startswith("#"):
        return ""

    return url


def extract_player_urls(page):
    found = set()

    # iframe
    for element in page.locator("iframe").all():
        try:
            value = element.get_attribute("src")
            value = clean_url(urljoin(page.url, value or ""))

            if value:
                found.add(value)
        except Exception:
            pass

    # video
    for element in page.locator("video").all():
        try:
            for attr in ["src", "data-src", "data-video", "data-url"]:
                value = element.get_attribute(attr)

                if value:
                    value = clean_url(urljoin(page.url, value))

                    if value:
                        found.add(value)
        except Exception:
            pass

    # source
    for element in page.locator("source").all():
        try:
            for attr in ["src", "data-src"]:
                value = element.get_attribute(attr)

                if value:
                    value = clean_url(urljoin(page.url, value))

                    if value:
                        found.add(value)
        except Exception:
            pass

    # embed
    for element in page.locator("embed").all():
        try:
            for attr in ["src", "data", "data-src"]:
                value = element.get_attribute(attr)

                if value:
                    value = clean_url(urljoin(page.url, value))

                    if value:
                        found.add(value)
        except Exception:
            pass

    # bütün data-* atributları
    try:
        elements = page.locator("[data-src], [data-url], [data-video], [data-player]")

        for element in elements.all():
            for attr in [
                "data-src",
                "data-url",
                "data-video",
                "data-player",
            ]:
                value = element.get_attribute(attr)

                if not value:
                    continue

                value = clean_url(urljoin(page.url, value))

                if value:
                    found.add(value)
    except Exception:
        pass

    # HTML içindən açıq URL-lər
    try:
        html = page.content()

        patterns = [
            r'https?://[^"\']+',
            r'//[^"\']+',
        ]

        for pattern in patterns:
            for match in re.findall(pattern, html):
                url = clean_url(match)

                if not url:
                    continue

                lower = url.lower()

                keywords = [
                    "m3u8",
                    "mp4",
                    "mpd",
                    "embed",
                    "player",
                    "video",
                    "stream",
                    "iframe",
                    "rapid",
                ]

                if any(x in lower for x in keywords):
                    found.add(url)

    except Exception:
        pass

    return sorted(found)


def get_movie_links(page, url):
    links = set()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        time.sleep(2)

        anchors = page.locator("a[href]").all()

        for anchor in anchors:
            try:
                href = anchor.get_attribute("href")

                if not href:
                    continue

                full = urljoin(page.url, href)
                full = full.split("#")[0]

                if looks_like_movie(full):
                    links.add(full)

            except Exception:
                pass

    except PlaywrightTimeoutError:
        print("[TIMEOUT]", url)

    except Exception as e:
        print("[ERROR]", url, e)

    return links


def main():

    print("=" * 70)
    print("HDFILMCEHENNEMI PLAYER SCRAPER")
    print("=" * 70)

    movie_pages = set()
    scanned = set()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={
                "width": 1366,
                "height": 768
            },
            locale="tr-TR"
        )

        page = context.new_page()

        print()
        print("[1] Sayt açılır...")
        print(BASE_URL)

        try:
            response = page.goto(
                BASE_URL,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if response:
                print(
                    "[HTTP]",
                    response.status,
                    response.url
                )

                if response.status == 451:
                    print()
                    print("!!! HTTP 451 !!!")
                    print(
                        "GitHub Actions runner sayt tərəfindən "
                        "məhdudlaşdırılıb."
                    )

                    browser.close()
                    return

        except Exception as e:
            print("[ERROR]", e)

        queue = [BASE_URL]

        print()
        print("[2] Film səhifələri axtarılır...")

        while queue and len(scanned) < MAX_PAGES:

            current = queue.pop(0)

            if current in scanned:
                continue

            scanned.add(current)

            print()
            print(
                f"[SCAN {len(scanned)}/{MAX_PAGES}]"
            )
            print(current)

            links = get_movie_links(page, current)

            for link in links:

                if link in scanned:
                    continue

                if looks_like_movie(link):
                    movie_pages.add(link)

            # ilk səviyyədən yeni səhifələr
            for link in list(movie_pages):

                if link not in scanned and link not in queue:
                    queue.append(link)

                if len(queue) >= MAX_PAGES:
                    break

            if len(movie_pages) >= MAX_PAGES:
                break

        print()
        print("=" * 70)
        print("FILM SƏHİFƏLƏRİ:", len(movie_pages))
        print("=" * 70)

        print()
        print("[3] Player URL-ləri çıxarılır...")

        results = []

        for index, movie_url in enumerate(
            sorted(movie_pages),
            start=1
        ):

            print()
            print(
                f"[FILM {index}/{len(movie_pages)}]"
            )
            print(movie_url)

            try:

                response = page.goto(
                    movie_url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                if response:
                    print(
                        "HTTP:",
                        response.status
                    )

                    if response.status == 451:
                        print(
                            "451 - səhifəyə giriş yoxdur."
                        )
                        continue

                time.sleep(2)

                player_urls = extract_player_urls(page)

                print(
                    "PLAYER URL:",
                    len(player_urls)
                )

                for player in player_urls:

                    print(
                        "  ->",
                        player
                    )

                    results.append(
                        (
                            movie_url,
                            player
                        )
                    )

            except PlaywrightTimeoutError:
                print("TIMEOUT")

            except Exception as e:
                print(
                    "ERROR:",
                    e
                )

        browser.close()

    # təkrarları sil
    unique = []
    seen = set()

    for movie_url, player_url in results:

        key = (
            movie_url,
            player_url
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(key)

    print()
    print("=" * 70)
    print("NƏTİCƏ")
    print("=" * 70)

    print("Film:", len(movie_pages))
    print("Player URL:", len(unique))

    # M3U
    print()
    print("[4] M3U yaradılır...")

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for movie_url, player_url in unique:

            title = movie_url.rstrip("/").split("/")[-1]

            title = title.replace(
                "-",
                " "
            )

            title = title.strip()

            if not title:
                title = "Film"

            f.write(
                f'#EXTINF:-1,{title}\n'
            )

            f.write(
                player_url + "\n"
            )

    print()
    print("=" * 70)
    print("M3U HAZIRDIR:", OUTPUT)
    print("TOTAL:", len(unique))
    print("=" * 70)


if __name__ == "__main__":
    main()
