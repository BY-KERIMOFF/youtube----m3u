import argparse
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

DEFAULT_OUTPUT_FILE = Path("live_channels.m3u8")
DEFAULT_SOURCE_FILE = Path("youtube_channels.json")


def extract_first_m3u8_from_page(page_url: str, preferred_keyword: str = "") -> str:
    request = Request(
        page_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="ignore")

    candidates = re.findall(r"https?://[^\"'\s]+\.m3u8[^\"'\s]*", html)
    if not candidates:
        return ""

    if preferred_keyword:
        for candidate in candidates:
            if preferred_keyword in candidate:
                return candidate

    return candidates[0]


def load_channels(source_file: Path) -> List[Dict[str, str]]:
    if not source_file.exists():
        raise FileNotFoundError(f"JSON faylı tapılmadı: {source_file}")

    data = json.loads(source_file.read_text(encoding="utf-8"))
    channels = data.get("channels", [])

    channel_list: List[Dict[str, str]] = []
    for item in channels:
        name = item.get("name", "")
        url = item.get("url", "")
        if not name or not url:
            continue
        extractor = item.get("extractor", "")
        preferred_keyword = item.get("preferred_keyword", "")
        channel_list.append(
            {
                "name": name,
                "url": url,
                "extractor": extractor,
                "preferred_keyword": preferred_keyword,
            }
        )

    return channel_list


def fetch_stream_url(url: str, cookie_file: Optional[Path]) -> str:
    cmd = ["yt-dlp", "-g", url]
    if cookie_file:
        cmd[1:1] = ["--cookies", str(cookie_file)]

    output = subprocess.check_output(cmd, text=True).strip()
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def resolve_stream_url(channel: Dict[str, str], cookie_file: Optional[Path]) -> str:
    url = channel["url"]
    extractor = channel.get("extractor", "")
    preferred_keyword = channel.get("preferred_keyword", "")

    if extractor == "web_m3u8":
        return extract_first_m3u8_from_page(url, preferred_keyword)

    if "youtube.com" in url or "youtu.be" in url:
        return fetch_stream_url(url, cookie_file)

    if ".m3u8" in url:
        return url

    return ""


def build_playlist(channels: List[Dict[str, str]], cookie_file: Optional[Path]) -> Tuple[str, int]:
    m3u8_content = "#EXTM3U\n"
    stream_count = 0

    for channel in channels:
        name = channel["name"]
        print(f"➡️  {name} üçün link çıxarılır...")
        try:
            stream_url = resolve_stream_url(channel, cookie_file)
            if not stream_url:
                raise RuntimeError("Boş stream URL qaytarıldı")

            print(f"✅ {name} link yeniləndi")
            m3u8_content += f"#EXTINF:-1,{name}\n{stream_url}\n"
            stream_count += 1
        except Exception as exc:
            print(f"❌ {name} üçün çıxarış mümkün olmadı: {exc}")

    return m3u8_content, stream_count


def write_playlist(output_file: Path, content: str) -> None:
    output_file.write_text(content, encoding="utf-8")


def run_once(output_file: Path, cookie_file: Optional[Path], channels: List[Dict[str, str]]) -> bool:
    content, stream_count = build_playlist(channels, cookie_file)

    if stream_count > 0:
        write_playlist(output_file, content)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[✓] {stream_count} stream link fayla yazıldı: {output_file} ({now})")
        return True

    print("[X] Heç bir stream çıxmadı. Fayl yenilənmədi.")
    return False


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("interval 0-dan böyük olmalıdır")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Canlı yayım linklərini json fayldan oxuyub m3u faylına çıxarır. "
            "--watch ilə periodik yeniləmə edib tokenlərin köhnəlməsini azaldır."
        )
    )
    parser.add_argument(
        "--source-json",
        default=str(DEFAULT_SOURCE_FILE),
        help="kanalların olduğu json faylı (default: youtube_channels.json)",
    )
    parser.add_argument(
        "--cookies",
        default="youtube_cookies.txt",
        help="yt-dlp üçün cookie faylı (mövcud deyilsə cookies istifadə olunmur)",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_FILE),
        help="çıxış m3u faylı",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="playlisti interval ilə daimi yenilə",
    )
    parser.add_argument(
        "--interval",
        type=positive_int,
        default=1800,
        help="--watch üçün yeniləmə intervalı (saniyə), default: 1800",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_file = Path(args.output)
    source_json = Path(args.source_json)
    cookie_path = Path(args.cookies)
    cookie_file = cookie_path if cookie_path.exists() else None

    if args.cookies and not cookie_file:
        print(f"⚠️ Cookie faylı tapılmadı: {cookie_path}. Cookies-siz davam edilir.")

    try:
        channels = load_channels(source_json)
    except Exception as exc:
        print(f"❌ JSON oxunmadı: {exc}")
        return 1

    if not channels:
        print("❌ JSON daxilində kanal tapılmadı.")
        return 1

    print(f"ℹ️ {len(channels)} kanal tapıldı ({source_json}).")

    if not args.watch:
        return 0 if run_once(output_file, cookie_file, channels) else 1

    print(f"🔄 Watch rejimi aktivdir. Hər {args.interval} saniyədə yenilənəcək.")
    try:
        while True:
            run_once(output_file, cookie_file, channels)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Dayandırıldı.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
