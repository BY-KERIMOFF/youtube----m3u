# ecanlitv_scanner.py
import os
import re
import time
import json
import base64
import threading
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


SITE_URL = "https://www.ecanlitvizle.live/canlitv"
BASE_URL = "https://www.ecanlitvizle.live"
OUTPUT_DIR = "tv2"

# Saytdan tapılan kanallar bura yazılacaq
CHANNELS = {}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

M3U8_REGEX = re.compile(
    r"""https?://[^\s"'<>\\]+?\.m3u8(?:\?[^\s"'<>\\]*)?""",
    re.IGNORECASE,
)

RELATIVE_M3U8_REGEX = re.compile(
    r"""["']([^"']+?\.m3u8(?:\?[^"']*)?)["']""",
    re.IGNORECASE,
)

_validate_cache = {}
_validate_lock = threading.Lock()


def normalize_url(url, base_url=None):
    if not url:
        return None
    url = str(url).strip()
    url = url.replace("\\/", "/").replace("\\u002F", "/").replace("&amp;", "&")
    if url.startswith("//"):
        url = "https:" + url
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)
    if not url.startswith(("http://", "https://")):
        return None
    return url


def decode_base64(value):
    try:
        value = value.strip()
        if len(value) < 20:
            return None
        value += "=" * (-len(value) % 4)
        decoded = base64.b64decode(value, validate=False).decode("utf-8", errors="ignore")
        if ".m3u8" in decoded.lower():
            return decoded
    except Exception:
        pass
    return None


def extract_m3u8(text, base_url):
    found = []
    if not text:
        return found
    for match in M3U8_REGEX.findall(text):
        url = normalize_url(match, base_url)
        if url and url not in found:
            found.append(url)
    for match in RELATIVE_M3U8_REGEX.findall(text):
        url = normalize_url(match, base_url)
        if url and url not in found:
            found.append(url)
    cleaned = text.replace("\\/", "/").replace("\\u002F", "/").replace("&amp;", "&")
    for match in M3U8_REGEX.findall(cleaned):
        url = normalize_url(match, base_url)
        if url and url not in found:
            found.append(url)
    tokens = re.findall(r"[A-Za-z0-9+/=_-]{40,}", text)
    for token in tokens[:200]:
        decoded = decode_base64(token)
        if not decoded:
            continue
        for match in M3U8_REGEX.findall(decoded):
            url = normalize_url(match, base_url)
            if url and url not in found:
                found.append(url)
    return found


def unique_urls(urls):
    result = []
    seen = set()
    for url in urls:
        if not url:
            continue
        url = url.strip()
        if url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[əçğıöşü]", lambda m: {
        "ə": "e", "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"
    }.get(m.group(0), m.group(0)), text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or "channel"


def token_expired(url):
    try:
        query = parse_qs(urlparse(url).query)
        if "e" not in query:
            return False
        expires = int(query["e"][0])
        if expires > 10 ** 12:
            expires = expires // 1000
        now = int(time.time())
        return expires <= now + 30
    except Exception:
        return False


def token_remaining_seconds(url):
    try:
        query = parse_qs(urlparse(url).query)
        if "e" not in query:
            return None
        expires = int(query["e"][0])
        if expires > 10 ** 12:
            expires = expires // 1000
        return expires - int(time.time())
    except Exception:
        return None


def validate_stream(url, page=None, referer=None):
    if not url:
        return False
    cache_key = url
    with _validate_lock:
        if cache_key in _validate_cache:
            return _validate_cache[cache_key]
    if token_expired(url):
        print(f"      [EXPIRED] {url}")
        with _validate_lock:
            _validate_cache[cache_key] = False
        return False
    if not page:
        return False
    result = False
    try:
        headers = {
            "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,application/octet-stream,*/*",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = referer.rstrip("/")
        response = page.request.get(url, timeout=20000, fail_on_status_code=False, headers=headers)
        status = response.status
        if status < 400:
            try:
                body = response.text()[:50000]
            except Exception:
                body = ""
            if "#EXTM3U" in body or "#EXT-X-" in body:
                result = True
            else:
                try:
                    content_type = response.headers.get("content-type", "").lower()
                except Exception:
                    content_type = ""
                if "mpegurl" in content_type or "vnd.apple.mpegurl" in content_type:
                    result = True
    except Exception:
        result = False
    with _validate_lock:
        _validate_cache[cache_key] = result
    return result


def parse_master_playlist(body, base_url):
    if not body or "#EXTM3U" not in body:
        return []
    if "#EXT-X-STREAM-INF" not in body:
        return []
    variants = []
    lines = body.splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith("#EXT-X-STREAM-INF"):
            continue
        info = line.upper()
        bandwidth = 0
        resolution = None
        resolution_score = 0
        bw_match = re.search(r"BANDWIDTH=(\d+)", info)
        if bw_match:
            bandwidth = int(bw_match.group(1))
        res_match = re.search(r"RESOLUTION=(\d+)X(\d+)", info)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))
            resolution = f"{width}x{height}"
            resolution_score = width * height
        for next_line in lines[i + 1:]:
            next_line = next_line.strip()
            if not next_line or next_line.startswith("#"):
                continue
            variant_url = normalize_url(next_line, base_url)
            if variant_url:
                variants.append({
                    "url": variant_url,
                    "bandwidth": bandwidth,
                    "resolution": resolution,
                    "resolution_score": resolution_score,
                })
            break
    return variants


def collect_channels_from_site(page):
    """Saytdan bütün kanal adlarını və linklərini toplayır."""
    channels = {}
    print("")
    print("[SCAN] Sayt açılır: " + SITE_URL)
    try:
        page.goto(SITE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
    except PlaywrightTimeoutError:
        print("[WARN] Sayt timeout oldu.")
    except Exception as e:
        print(f"[OPEN ERROR] {str(e)[:250]}")

    # Kanal linklərini tap
    try:
        links = page.evaluate(
            """
            () => {
                const result = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href || '';
                    const text = (a.innerText || a.textContent || '').trim();
                    if (href && text && text.length > 1 && text.length < 60) {
                        result.push({href, text});
                    }
                });
                return result;
            }
            """
        )
        print(f"[SCAN] {len(links)} link tapıldı")
        for item in links:
            href = item.get("href", "")
            text = item.get("text", "").strip()
            if not href or not text:
                continue
            # Yalnız kanal səhifələrini götür
            if "/canlitv/" in href or "/kanal/" in href or "/izle/" in href:
                if href.startswith("/"):
                    href = BASE_URL + href
                if href not in channels:
                    channels[href] = text
                    print(f"  [KANAL] {text} -> {href}")
    except Exception as e:
        print(f"[LINK ERROR] {str(e)[:250]}")

    # Kanal kartlarını tap (data atributları ilə)
    try:
        cards = page.evaluate(
            """
            () => {
                const result = [];
                document.querySelectorAll('[data-channel], [data-id], [data-name], [data-url]').forEach(el => {
                    result.push({
                        name: el.getAttribute('data-name') || el.getAttribute('data-channel') || '',
                        url: el.getAttribute('data-url') || el.getAttribute('data-src') || '',
                        id: el.getAttribute('data-id') || ''
                    });
                });
                return result;
            }
            """
        )
        for c in cards:
            name = c.get("name", "").strip()
            url = c.get("url", "").strip()
            if name and url:
                full = normalize_url(url, BASE_URL)
                if full:
                    channels[full] = name
                    print(f"  [CARD] {name} -> {full}")
    except Exception as e:
        print(f"[CARD ERROR] {str(e)[:250]}")

    return channels


def scan_channel_page(page, channel_url, channel_name):
    """Bir kanal səhifəsindən m3u8 linklərini toplayır."""
    print("")
    print("-" * 70)
    print(f"[CHANNEL] {channel_name}")
    print(f"[URL] {channel_url}")
    print("-" * 70)
    candidates = []
    network_urls = []

    def capture_response(response):
        try:
            url = response.url
            if ".m3u8" in url.lower() and url not in network_urls:
                network_urls.append(url)
                print(f"  [NETWORK] {url}")
        except Exception:
            pass

    page.on("response", capture_response)

    try:
        page.goto(channel_url, wait_until="domcontentloaded", timeout=40000)
    except PlaywrightTimeoutError:
        print("  [WARN] Timeout")
    except Exception as e:
        print(f"  [OPEN ERROR] {str(e)[:200]}")

    # Player-in yüklənməsini gözlə
    for i in range(6):
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass

    # Videoları işə sal
    try:
        page.evaluate(
            """
            () => {
                document.querySelectorAll('video, iframe').forEach(v => {
                    try {
                        if (v.tagName === 'VIDEO') {
                            v.muted = true;
                            v.autoplay = true;
                            const p = v.play();
                            if (p) p.catch(() => {});
                        }
                    } catch(e) {}
                });
            }
            """
        )
        page.wait_for_timeout(3000)
    except Exception:
        pass

    # Şəbəkə trafiyindən topla
    candidates.extend(network_urls)

    # HTML-dən topla
    try:
        html = page.content()
        for url in extract_m3u8(html, channel_url):
            candidates.append(url)
    except Exception:
        pass

    # Performance entries
    try:
        entries = page.evaluate(
            "() => performance.getEntriesByType('resource').map(x => x.name)"
        )
        for url in entries:
            if ".m3u8" in url.lower():
                candidates.append(url)
    except Exception:
        pass

    # Frame-lərdən topla
    try:
        for frame in page.frames:
            try:
                frame_url = frame.url
                if not frame_url or frame_url == "about:blank":
                    continue
                frame_html = frame.content()
                for url in extract_m3u8(frame_html, frame_url):
                    candidates.append(url)
                try:
                    entries = frame.evaluate(
                        "() => performance.getEntriesByType('resource').map(x => x.name)"
                    )
                    for url in entries:
                        if ".m3u8" in url.lower():
                            candidates.append(url)
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass

    try:
        page.remove_listener("response", capture_response)
    except Exception:
        pass

    candidates = unique_urls(candidates)
    candidates = [x for x in candidates if not token_expired(x)]
    candidates.sort(key=lambda u: (
        1 if "playlist" in u or "master" in u or "index" in u else 0,
        token_remaining_seconds(u) or 0,
    ), reverse=True)

    print(f"  [FOUND] {len(candidates)} m3u8 linki")
    for c in candidates[:10]:
        rem = token_remaining_seconds(c)
        rem_txt = f" ({rem}s)" if rem else ""
        print(f"    - {c}{rem_txt}")

    return candidates


def check_and_refresh_stream(url, page, referer=None):
    """Linki yoxlayır, vaxtı keçibsə None qaytarır."""
    if not url:
        return None
    if token_expired(url):
        print(f"    [EXPIRED] {url}")
        return None
    if validate_stream(url, page, referer=referer):
        return url
    return None


def fetch_master_variants(master_url, page, referer=None):
    """Master playlist-dən bütün variantları götürür."""
    try:
        headers = {
            "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,application/octet-stream,*/*",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = referer.rstrip("/")
        response = page.request.get(master_url, timeout=20000, fail_on_status_code=False, headers=headers)
        if response.status >= 400:
            return []
        body = response.text()
        return parse_master_playlist(body, master_url)
    except Exception:
        return []


def build_quality_playlist(variants):
    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for v in variants:
        bw = v.get("bandwidth") or 1000000
        res = v.get("resolution") or "640x360"
        lines.append(
            f'#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={bw},CODECS="",RESOLUTION={res}'
        )
        lines.append(v["url"])
    return "\n".join(lines) + "\n"


def prepare_output():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".m3u") or f.endswith(".m3u8") or f.endswith(".error.txt") or f in ("links.txt", "github_links.txt", "channels.json"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except Exception:
                pass
    print(f"[CLEAN] {OUTPUT_DIR}/ təmizləndi")


def write_m3u(slug, name, stream_url):
    path = os.path.join(OUTPUT_DIR, f"{slug}.m3u")
    content = (
        "#EXTM3U\n"
        f'#EXTINF:-1 tvg-id="{slug}" tvg-name="{name}" '
        f'group-title="Turkiye",{name}\n'
        f"{stream_url}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[WRITE] {path}")


def write_quality_playlist(slug, variants):
    if not variants:
        return None
    path = os.path.join(OUTPUT_DIR, f"{slug}_all.m3u8")
    content = build_quality_playlist(variants)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[WRITE] {path}")
    return path


def write_all_m3u(results):
    all_path = os.path.join(OUTPUT_DIR, "all.m3u")
    lines = ["#EXTM3U"]
    for slug, data in results.items():
        name = data.get("name", slug)
        master = data.get("master")
        if not master:
            continue
        lines.append(
            f'#EXTINF:-1 tvg-id="{slug}" tvg-name="{name}" '
            f'group-title="Turkiye",{name}'
        )
        lines.append(master)
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[WRITE] {all_path}")

    links_path = os.path.join(OUTPUT_DIR, "links.txt")
    with open(links_path, "w", encoding="utf-8") as f:
        for slug, data in results.items():
            master = data.get("master")
            if not master:
                continue
            f.write(f"# {data.get('name', slug)}\n{master}\n\n")
    print(f"[WRITE] {links_path}")

    repo = os.environ.get("GITHUB_REPOSITORY", "USERNAME/REPO")
    base = f"https://raw.githubusercontent.com/{repo}/main/{OUTPUT_DIR}"
    github_links_path = os.path.join(OUTPUT_DIR, "github_links.txt")
    with open(github_links_path, "w", encoding="utf-8") as f:
        f.write("# BUTUN KANALLAR (TEK playlist)\n")
        f.write(f"{base}/all.m3u\n\n")
        f.write("# AYRI-AYRI KANALLAR\n")
        for slug, data in results.items():
            master = data.get("master")
            if not master:
                continue
            f.write(f"# {data.get('name', slug)}\n{base}/{slug}.m3u\n")
            if data.get("variants"):
                f.write(f"# {data.get('name', slug)} - BUTUN KEYFIYYETLER\n{base}/{slug}_all.m3u8\n\n")
            else:
                f.write("\n")
    print(f"[WRITE] {github_links_path}")

    json_path = os.path.join(OUTPUT_DIR, "channels.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[WRITE] {json_path}")


def write_error(slug, name, url):
    path = os.path.join(OUTPUT_DIR, f"{slug}.error.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            f"Kanal: {name}\n"
            f"URL: {url}\n"
            f"Status: M3U8 tapilmadi\n"
            f"Vaxt: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        )
    print(f"[ERROR FILE] {path}")


def main():
    print("")
    print("=" * 70)
    print("ECANLITVIZLE.LIVE SCANNER")
    print("Playwright + Chromium + Full Quality Variants")
    print("=" * 70)

    print("")
    print("[STEP 1] Çıxış qovluğu hazırlanır...")
    prepare_output()
    _validate_cache.clear()

    results = {}
    success = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--autoplay-policy=no-user-gesture-required",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            extra_http_headers={
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            },
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        page = context.new_page()

        # 1. Saytdan kanalları topla
        print("")
        print("[STEP 2] Saytdan kanallar toplanır...")
        channels = collect_channels_from_site(page)
        print("")
        print(f"[INFO] Cəmi {len(channels)} kanal tapıldı")

        # 2. Hər kanal üçün m3u8 linklərini topla
        print("")
        print("[STEP 3] Hər kanal üçün m3u8 linkləri toplanır...")
        channel_page = context.new_page()
        for channel_url, channel_name in channels.items():
            slug = slugify(channel_name)
            try:
                candidates = scan_channel_page(channel_page, channel_url, channel_name)
            except Exception as e:
                print(f"[CHANNEL CRASH] {channel_name}: {str(e)[:200]}")
                candidates = []

            master = None
            variants = []
            for c in candidates:
                if check_and_refresh_stream(c, channel_page, referer=channel_url):
                    master = c
                    variants = fetch_master_variants(c, channel_page, referer=channel_url)
                    break

            if master:
                results[slug] = {
                    "name": channel_name,
                    "url": channel_url,
                    "master": master,
                    "variants": variants,
                }
                write_m3u(slug, channel_name, master)
                if variants:
                    write_quality_playlist(slug, variants)
                success += 1
                print(f"  [OK] {channel_name} ({len(variants)} keyfiyyət)")
            else:
                write_error(slug, channel_name, channel_url)
                failed += 1
                print(f"  [FAILED] {channel_name}")

        try:
            channel_page.close()
        except Exception:
            pass
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass

    print("")
    print("[STEP 4] Nəticələr yazılır...")
    write_all_m3u(results)

    print("")
    print("=" * 70)
    print("NƏTİCƏ")
    print("=" * 70)
    print(f"[OK] Uğurlu: {success}")
    print(f"[X] Tapılmadı: {failed}")
    print(f"[TOTAL] {len(results) + failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
