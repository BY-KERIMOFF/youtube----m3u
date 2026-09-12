# tv_channels.py
import os
import re
import time
import base64
import threading
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


CHANNELS = {
    "atvavrupa": {"name": "ATV Avrupa", "url": "https://www.atvavrupa.tv/canli-yayin"},
    "showmax": {"name": "Showmax", "url": "https://www.showmax.com.tr/"},
    "tv8int": {"name": "TV8 International", "url": "https://www.tv8.com.tr/tv8-international"},
}

FALLBACK_STREAMS = {
    "atvavrupa": [
        "https://trkvz-live.ercdn.net/atvavrupa/atvavrupa.m3u8",
        "https://trkvz-live.ercdn.net/atvavrupa/atvavrupa_576p.m3u8",
        "https://trn03.tulix.tv/gt-atvavrupa/playlist.m3u8",
        "https://tgn.bozztv.com/trn03/gt-atvavrupa/index.m3u8",
    ],
    "showmax": [
        "https://ciner-live.ercdn.net/showmax/playlist.m3u8",
        "https://ciner-live.ercdn.net/showmax/showmax.m3u8",
    ],
    "tv8int": [
        "https://tv8.daioncdn.net/tv8/tv8.m3u8",
        "https://tv8.daioncdn.net/tv8/tv8_720p.m3u8",
        "https://tv8.daioncdn.net/tv8/tv8_1080p.m3u8",
        "https://tv8.daioncdn.net/tv8/tv8_480p.m3u8",
    ],
}

REFERERS = {
    "atvavrupa": "https://www.atvavrupa.tv/",
    "showmax": "https://www.showmax.com.tr/",
    "tv8int": "https://www.tv8.com.tr/",
}

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
    for token in tokens[:100]:
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


def is_master_playlist(url):
    u = url.lower()
    if re.search(r"[/_-]\d{3,4}p\.m3u8", u):
        return False
    if re.search(r"_hd\.m3u8", u):
        return False
    if re.search(r"_sd\.m3u8", u):
        return False
    if re.search(r"_\d{3,4}\.m3u8", u):
        return False
    if re.search(r"[/_-]playlist\.m3u8", u):
        return True
    if re.search(r"[/_-]master\.m3u8", u):
        return True
    if re.search(r"[/_-]index\.m3u8", u):
        return True
    return False


def quality_from_url(url):
    u = url.lower()
    m = re.search(r"[/_-](\d{3,4})p\.m3u8", u)
    if m:
        return int(m.group(1))
    if "_hd" in u:
        return 720
    if "_sd" in u:
        return 480
    if "1080" in u:
        return 1080
    if "720" in u:
        return 720
    if "576" in u:
        return 576
    if "480" in u:
        return 480
    if "360" in u:
        return 360
    return 0


def score_stream(url):
    u = url.lower()
    score = 0
    if ".m3u8" in u:
        score += 50
    if is_master_playlist(url):
        score += 200
    q = quality_from_url(url)
    score += q // 10
    if re.search(r"[/_-]live", u) or "/live/" in u:
        score += 10
    if re.search(r"[/_-]stream", u):
        score += 10
    if "?st=" in u or "&st=" in u:
        score += 15
    if "&e=" in u or "?e=" in u:
        score += 10
    if "ercdn.net" in u:
        score += 20
    if "daioncdn.net" in u:
        score += 20
    remaining = token_remaining_seconds(url)
    if remaining is not None and remaining > 60:
        score += 30
    return score


def validate_stream(url, page=None, use_cache=True, referer=None):
    if not url:
        return False
    cache_key = url
    if use_cache:
        with _validate_lock:
            if cache_key in _validate_cache:
                return _validate_cache[cache_key]
    if token_expired(url):
        print(f"      [EXPIRED] {url}")
        if use_cache:
            with _validate_lock:
                _validate_cache[cache_key] = False
        return False
    print("")
    print(f"      [TEST] {url}")
    if not page:
        if use_cache:
            with _validate_lock:
                _validate_cache[cache_key] = False
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
        print(f"      [HTTP] {status}")
        if status >= 400:
            print(f"      [X] HTTP {status}")
            result = False
        else:
            try:
                body = response.text()
            except Exception as e:
                print(f"      [TEXT ERROR] {str(e)[:200]}")
                body = ""
            body = body[:50000]
            if "#EXTM3U" in body:
                print("      [OK] #EXTM3U tapildi")
                result = True
            elif "#EXT-X-" in body:
                print("      [OK] HLS playlist tapildi")
                result = True
            else:
                try:
                    content_type = response.headers.get("content-type", "").lower()
                except Exception:
                    content_type = ""
                if "mpegurl" in content_type or "vnd.apple.mpegurl" in content_type:
                    print("      [OK] HLS content-type")
                    result = True
                else:
                    print("      [X] HLS playlist tesdiqlenmedi")
                    result = False
    except Exception as e:
        print(f"      [ERR] {str(e)[:250]}")
        result = False
    if use_cache:
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
                    "quality": quality_from_url(variant_url) or (resolution_score // 1000 if resolution_score else 0),
                })
            break
    return variants


def fetch_master_playlist(url, page, referer=None):
    if not url:
        return None
    if token_expired(url):
        print("      [MASTER] Token vaxti bitib")
        return None
    try:
        headers = {
            "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,application/octet-stream,*/*",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = referer.rstrip("/")
        response = page.request.get(url, timeout=20000, fail_on_status_code=False, headers=headers)
        if response.status >= 400:
            return None
        body = response.text()
        if "#EXTM3U" not in body:
            return None
        return body
    except Exception as e:
        print(f"      [MASTER ERROR] {str(e)[:200]}")
        return None


def collect_all_variants(master_url, page, referer=None):
    print("")
    print(f"      [MASTER] {master_url}")
    body = fetch_master_playlist(master_url, page, referer=referer)
    if not body:
        print("      [MASTER] Alinmadi")
        return []
    variants = parse_master_playlist(body, master_url)
    if not variants:
        print("      [MASTER] Variant yoxdur (bu artiq media playlist-dir)")
        return []
    print(f"      [MASTER] {len(variants)} variant tapildi")
    valid = []
    for v in variants:
        if token_expired(v["url"]):
            print(f"      [VARIANT] [EXPIRED] {v['url']}")
            continue
        print(f"      [VARIANT] {v['resolution'] or v['quality']}p - {v['url']}")
        if validate_stream(v["url"], page, referer=referer):
            v["valid"] = True
            valid.append(v)
            print(f"      [VARIANT] [OK] {v['resolution'] or v['quality']}p")
        else:
            print(f"      [VARIANT] [X] {v['resolution'] or v['quality']}p islemir")
    valid.sort(key=lambda x: (x["resolution_score"], x["bandwidth"]), reverse=True)
    return valid


def scan_page(page, page_url):
    found = []
    def add(url, source):
        url = normalize_url(url, page_url)
        if not url:
            return
        if ".m3u8" not in url.lower():
            return
        if url not in found:
            found.append(url)
            print(f"      [M3U8] {source}: {url}")
    try:
        performance_urls = page.evaluate(
            "() => performance.getEntriesByType('resource').map(x => x.name)"
        )
        for url in performance_urls:
            if ".m3u8" in url.lower():
                add(url, "PERFORMANCE")
    except Exception as e:
        print(f"      [PERFORMANCE ERROR] {str(e)[:150]}")
    try:
        html = page.content()
        for url in extract_m3u8(html, page_url):
            add(url, "HTML")
    except Exception as e:
        print(f"      [HTML ERROR] {str(e)[:150]}")
    try:
        frames = page.frames
        print(f"      [INFO] Frame sayi: {len(frames)}")
        for frame in frames:
            try:
                frame_url = frame.url
                if not frame_url or frame_url == "about:blank":
                    continue
                print(f"      [FRAME] {frame_url}")
                frame_html = frame.content()
                for url in extract_m3u8(frame_html, frame_url):
                    add(url, "IFRAME")
                try:
                    entries = frame.evaluate(
                        "() => performance.getEntriesByType('resource').map(x => x.name)"
                    )
                    for url in entries:
                        if ".m3u8" in url.lower():
                            add(url, "FRAME-PERFORMANCE")
                except Exception as e:
                    print(f"      [FRAME-EVAL ERROR] {str(e)[:120]}")
            except Exception as e:
                print(f"      [FRAME SKIP] {str(e)[:120]}")
                continue
    except Exception as e:
        print(f"      [FRAME ERROR] {str(e)[:150]}")
    return unique_urls(found)


def pick_best_master(candidates, page, referer=None):
    if not candidates:
        return None
    masters = [u for u in candidates if is_master_playlist(u)]
    others = [u for u in candidates if not is_master_playlist(u)]
    def sort_key(u):
        rem = token_remaining_seconds(u)
        if rem is None:
            return (0, 0)
        return (1, rem)
    masters.sort(key=sort_key, reverse=True)
    others.sort(key=sort_key, reverse=True)
    for candidate in masters + others:
        print("")
        print(f"      [CHECK] {candidate}")
        if validate_stream(candidate, page, referer=referer):
            print("")
            print("      [SUCCESS]")
            print(f"      {candidate}")
            return candidate
    return None


def build_quality_playlist(channel_id, channel, variants, master_url):
    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for v in variants:
        bw = v.get("bandwidth") or 0
        res = v.get("resolution") or ""
        if not res:
            q = v.get("quality") or 0
            if q >= 720:
                res = "1280x720"
            elif q >= 576:
                res = "1024x576"
            elif q >= 480:
                res = "854x480"
            elif q >= 360:
                res = "640x360"
            else:
                res = "640x360"
        if bw <= 0:
            bw = 1000000
        lines.append(
            f'#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={bw},CODECS="",RESOLUTION={res}'
        )
        lines.append(v["url"])
    return "\n".join(lines) + "\n"


def browser_find_stream(page, channel_id, channel):
    name = channel["name"]
    page_url = channel["url"]
    referer = REFERERS.get(channel_id, page_url)
    print("")
    print("=" * 70)
    print(f"[BROWSER] {name}")
    print(f"[URL] {page_url}")
    print("=" * 70)
    candidates = []
    network_urls = []
    def capture_response(response):
        try:
            url = response.url
            if ".m3u8" in url.lower() and url not in network_urls:
                network_urls.append(url)
                print(f"      [NETWORK] {url}")
        except Exception:
            pass
    page.on("response", capture_response)
    try:
        print("      [OPEN] Sayt acilir...")
        page.goto(page_url, wait_until="domcontentloaded", timeout=40000)
        try:
            print(f"      [TITLE] {page.title()}")
        except Exception:
            pass
    except PlaywrightTimeoutError:
        print("      [WARN] Sayt timeout oldu.")
    except Exception as e:
        print(f"      [OPEN ERROR] {str(e)[:250]}")
    print("      [WAIT] Player gozlenilir...")
    for i in range(10):
        try:
            page.wait_for_timeout(4000)
        except Exception:
            pass
        print(f"      [WAIT] {(i + 1) * 4} saniye...")
    try:
        page.evaluate(
            """
            () => {
                document.querySelectorAll('video').forEach(v => {
                    try {
                        v.muted = true;
                        v.autoplay = true;
                        const p = v.play();
                        if (p) p.catch(() => {});
                    } catch(e) {}
                });
            }
            """
        )
        page.wait_for_timeout(4000)
    except Exception:
        pass
    candidates.extend(network_urls)
    try:
        candidates.extend(scan_page(page, page_url))
    except Exception as e:
        print(f"      [SCAN ERROR] {str(e)[:200]}")
    try:
        entries = page.evaluate(
            "() => performance.getEntriesByType('resource').map(x => x.name)"
        )
        for url in entries:
            if ".m3u8" in url.lower():
                candidates.append(url)
    except Exception:
        pass
    candidates = unique_urls(candidates)
    candidates = [x for x in candidates if not token_expired(x)]
    candidates.sort(key=score_stream, reverse=True)
    print("")
    print(f"      [FOUND] {len(candidates)} aktual URL")
    best_master = pick_best_master(candidates, page, referer=referer)
    try:
        page.remove_listener("response", capture_response)
    except Exception:
        pass
    if not best_master:
        return None, []
    variants = collect_all_variants(best_master, page, referer=referer)
    if not variants:
        return best_master, []
    return best_master, variants


def fallback_find(request_context, channel_id):
    urls = FALLBACK_STREAMS.get(channel_id, [])
    if not urls:
        return None, []
    print("")
    print(f"[FALLBACK] {channel_id}")
    print("-" * 70)
    def sort_key(u):
        rem = token_remaining_seconds(u)
        if rem is None:
            return (0, 0)
        return (1, rem)
    sorted_urls = sorted(urls, key=sort_key, reverse=True)
    for url in sorted_urls:
        if token_expired(url):
            print(f"   [EXPIRED] {url}")
            continue
        print(f"   [TRY] {url}")
        try:
            response = request_context.get(url, timeout=20000, fail_on_status_code=False)
            print(f"   [STATUS] {response.status}")
            if response.status >= 400:
                continue
            try:
                body = response.text()
            except Exception:
                body = ""
            if "#EXTM3U" in body or "#EXT-X-" in body:
                print("   [OK] Fallback isleyir")
                variants = parse_master_playlist(body, url)
                valid = []
                for v in variants:
                    try:
                        r = request_context.get(v["url"], timeout=15000, fail_on_status_code=False)
                        if r.status < 400:
                            v["valid"] = True
                            valid.append(v)
                    except Exception:
                        pass
                if valid:
                    valid.sort(key=lambda x: (x["resolution_score"], x["bandwidth"]), reverse=True)
                return url, valid
            try:
                content_type = response.headers.get("content-type", "").lower()
            except Exception:
                content_type = ""
            if "mpegurl" in content_type or "vnd.apple.mpegurl" in content_type:
                print("   [OK] HLS Content-Type")
                return url, []
        except Exception as e:
            print(f"   [ERROR] {str(e)[:200]}")
    return None, []


def prepare_folders():
    os.makedirs("tv2", exist_ok=True)
    for f in os.listdir("tv2"):
        if f.endswith(".m3u") or f.endswith(".m3u8") or f.endswith(".error.txt") or f in ("links.txt", "github_links.txt"):
            try:
                os.remove(os.path.join("tv2", f))
            except Exception:
                pass
    print("[CLEAN] tv2/ kohne fayllar silindi")
    os.makedirs("tv2", exist_ok=True)


def write_m3u(channel_id, channel, stream_url):
    path = os.path.join("tv2", f"{channel_id}.m3u")
    content = (
        "#EXTM3U\n"
        f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel["name"]}" '
        f'group-title="Turkiye",{channel["name"]}\n'
        f"{stream_url}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[WRITE] {path}")


def write_quality_playlist(channel_id, channel, variants):
    if not variants:
        return None
    path = os.path.join("tv2", f"{channel_id}_all.m3u8")
    content = build_quality_playlist(channel_id, channel, variants, None)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[WRITE] {path}")
    return path


def write_error(channel_id, channel):
    path = os.path.join("tv2", f"{channel_id}.error.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            f"Kanal: {channel['name']}\n"
            f"URL: {channel['url']}\n"
            f"Status: M3U8 tapilmadi\n"
            f"Vaxt: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        )
    print(f"[ERROR FILE] {path}")


def write_all_m3u(results):
    for cid, ch in CHANNELS.items():
        data = results.get(cid)
        if not data:
            continue
        master = data.get("master")
        variants = data.get("variants") or []
        if master:
            write_m3u(cid, ch, master)
        if variants:
            write_quality_playlist(cid, ch, variants)
    all_path = os.path.join("tv2", "all.m3u")
    lines = ["#EXTM3U"]
    for cid, ch in CHANNELS.items():
        data = results.get(cid)
        if not data:
            continue
        master = data.get("master")
        if not master:
            continue
        lines.append(
            f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{ch["name"]}" '
            f'group-title="Turkiye",{ch["name"]}'
        )
        lines.append(master)
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[WRITE] {all_path}")
    links_path = os.path.join("tv2", "links.txt")
    with open(links_path, "w", encoding="utf-8") as f:
        for cid, ch in CHANNELS.items():
            data = results.get(cid)
            if not data:
                continue
            master = data.get("master")
            if not master:
                continue
            f.write(f"# {ch['name']}\n{master}\n\n")
    print(f"[WRITE] {links_path}")
    repo = os.environ.get("GITHUB_REPOSITORY", "USERNAME/REPO")
    base = f"https://raw.githubusercontent.com/{repo}/main/tv2"
    github_links_path = os.path.join("tv2", "github_links.txt")
    with open(github_links_path, "w", encoding="utf-8") as f:
        f.write("# BUTUN KANALLAR (TEK playlist)\n")
        f.write(f"{base}/all.m3u\n\n")
        f.write("# AYRI-AYRI KANALLAR\n")
        for cid, ch in CHANNELS.items():
            data = results.get(cid)
            if not data:
                continue
            master = data.get("master")
            if not master:
                continue
            f.write(f"# {ch['name']}\n{base}/{cid}.m3u\n")
            if data.get("variants"):
                f.write(f"# {ch['name']} - BUTUN KEYFIYYETLER\n{base}/{cid}_all.m3u8\n\n")
            else:
                f.write("\n")
    print(f"[WRITE] {github_links_path}")


def main():
    print("")
    print("=" * 70)
    print("TURK TV LIVE M3U AUTO SCANNER")
    print("Playwright + Chromium + Full Quality Variants")
    print("=" * 70)
    print("")
    print("[STEP 1] Kohne fayllar silinir...")
    prepare_folders()
    _validate_cache.clear()
    success = 0
    failed = 0
    results = {}
    print("")
    print("[STEP 2] Kanallar scan edilir...")
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
        request_context = p.request.new_context(
            ignore_https_errors=True,
            extra_http_headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,application/octet-stream,*/*",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            },
        )
        try:
            for cid, ch in CHANNELS.items():
                referer = REFERERS.get(cid, ch["url"])
                page = context.new_page()
                master = None
                variants = []
                try:
                    master, variants = browser_find_stream(page, cid, ch)
                except Exception as e:
                    print(f"[BROWSER CRASH] {ch['name']}: {str(e)[:200]}")
                    master, variants = None, []
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass
                if not master:
                    print("")
                    print(f"[BROWSER X] {ch['name']} tapilmadi")
                    try:
                        request_context.dispose()
                    except Exception:
                        pass
                    request_context = p.request.new_context(
                        ignore_https_errors=True,
                        extra_http_headers={
                            "User-Agent": USER_AGENT,
                            "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,application/octet-stream,*/*",
                            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                            "Referer": referer,
                            "Origin": referer.rstrip("/"),
                        },
                    )
                    try:
                        master, variants = fallback_find(request_context, cid)
                    except Exception as e:
                        print(f"[FALLBACK CRASH] {ch['name']}: {str(e)[:200]}")
                        master, variants = None, []
                results[cid] = {"master": master, "variants": variants}
        finally:
            try:
                request_context.dispose()
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
    print("[STEP 3] Neticeler yazilir...")
    write_all_m3u(results)
    for cid, ch in CHANNELS.items():
        data = results.get(cid)
        master = data.get("master") if data else None
        variants = data.get("variants") if data else []
        if master:
            success += 1
            q_count = len(variants)
            print(f"[OK] {ch['name']} ({q_count} keyfiyyet)")
        else:
            write_error(cid, ch)
            failed += 1
            print(f"[FAILED] {ch['name']}")
        print("")
    print("")
    print("=" * 70)
    print("NETICE")
    print("=" * 70)
    print(f"[OK] Ugurlu: {success}")
    print(f"[X] Tapilmadi: {failed}")
    print(f"[TOTAL] {len(CHANNELS)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
