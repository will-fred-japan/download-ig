import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright
from clrprint import clrprint
from rich.console import Console

from simulate_browsing import simulate_browsing
from beta import generate_skewed_random

console = Console()

DEFAULT_USER_DATA_DIR = Path(r"T:\bench\GoogleChromePortable64\Data\profile")
DEFAULT_CHROME_EXECUTABLE = Path(r"T:\bench\GoogleChromePortable64\App\Chrome-bin\chrome.exe")
DEFAULT_GDL_DIR = Path(r"C:\Programs\gallery-dl-v1.26.8")
DEFAULT_COOKIES_FILE = DEFAULT_GDL_DIR / "www.instagram.com_cookies.txt"
DEFAULT_URLS_FILE = DEFAULT_GDL_DIR / "instagram-stories.txt"
DEFAULT_SINGLE_DL_SCRIPT = Path(r"T:\bench\single_story.py")
DEFAULT_EXTRA_SIMULATIONS = 5
DEFAULT_WAIT_TIME_MAX = 100

CHROMIUM_LAUNCH_ARGS = [
    "--disable-background-networking",
    "--disable-extensions",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--mute-audio",
    "--disable-plugins",
    "--disable-popup-blocking",
    "--disable-translate",
    "--disable-sync",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-accelerated-2d-canvas",
    "--disable-infobars",
    "--disable-devtools",
    "--disable-breakpad",
    "--device-scale-factor=1",
    "--disk-cache-size=200100100",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("download-ig-stories")


def set_title(text: str) -> None:
    try:
        sys.stdout.write(f"\33]0;{text}\a")
        sys.stdout.flush()
    except Exception:
        pass


def save_cookies_netscape_format(cookies: List[dict], filename: Path) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as handle:
        handle.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            domain = cookie.get("domain", "")
            if not domain.startswith("."):
                domain = "." + domain
            domain_initial_dot = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expires = str(int(cookie.get("expires", 0))) if cookie.get("expires") else "0"
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            handle.write("\t".join([
                domain,
                domain_initial_dot,
                path,
                secure,
                expires,
                name,
                value,
            ]) + "\n")


def read_urls(urls_file: Path) -> List[str]:
    if not urls_file.exists():
        logger.warning("URLs file %s does not exist.", urls_file)
        return []
    text = urls_file.read_text(encoding="utf-8")
    return [u.strip() for u in text.splitlines() if u.strip()]


def run_single_download(script: Path, url: str) -> int:
    try:
        result = subprocess.run([sys.executable, str(script), url], check=False)
        return result.returncode
    except FileNotFoundError:
        logger.exception("Download script not found: %s", script)
        return -1
    except Exception:
        logger.exception("Error running download script for URL: %s", url)
        return -1


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Download Instagram stories with a persistent browser session and simulated browsing."
    )
    parser.add_argument("--urls-file", type=Path, default=DEFAULT_URLS_FILE)
    parser.add_argument("--cookies-file", type=Path, default=DEFAULT_COOKIES_FILE)
    parser.add_argument("--single-script", type=Path, default=DEFAULT_SINGLE_DL_SCRIPT)
    parser.add_argument("--user-data-dir", type=Path, default=DEFAULT_USER_DATA_DIR)
    parser.add_argument("--chrome-exe", type=Path, default=DEFAULT_CHROME_EXECUTABLE)
    parser.add_argument("--extra-simulations", type=int, default=DEFAULT_EXTRA_SIMULATIONS)
    parser.add_argument("--wait-max", type=int, default=DEFAULT_WAIT_TIME_MAX)
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode (default: enabled)")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run browser in visible mode")
    args = parser.parse_args(argv)

    urls = read_urls(args.urls_file)
    logger.info("Loaded %d URLs from %s", len(urls), args.urls_file)

    if not urls:
        logger.warning("No URLs found; exiting.")
        return 0

    browser = None
    try:
        logger.info("Launching persistent Chromium context...")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch_persistent_context(
                user_data_dir=str(args.user_data_dir),
                executable_path=str(args.chrome_exe),
                headless=args.headless,
                viewport={"width": 1920, "height": 1080},
                args=CHROMIUM_LAUNCH_ARGS,
            )
            logger.info("Browser launched successfully.")
            page = browser.new_page()

            for idx, url in enumerate(urls, start=1):
                set_title(f"IG Stories [{idx}/{len(urls)}] - {url}")
                clrprint(f"=== [{idx}/{len(urls)}] Processing URL: {url} ===", clr='g')

                try:
                    time.sleep(1)
                    simulate_browsing(page)
                    time.sleep(1)
                except Exception:
                    logger.exception("simulate_browsing() failed for URL: %s", url)

                try:
                    cookies = browser.cookies("https://www.instagram.com")
                    save_cookies_netscape_format(cookies, args.cookies_file)
                except Exception:
                    logger.exception("Cookie export failed for URL: %s", url)

                rc = run_single_download(args.single_script, url)
                if rc != 0:
                    logger.warning("single_story.py exited with code %d for URL: %s", rc, url)

                clrprint(f"=== Finished [{idx}/{len(urls)}] ===", clr='y')

            for i in range(args.extra_simulations):
                console.print(f"[#00FFFF]=== {i + 1} / {args.extra_simulations} Starting simulation ===[/#00FFFF]")
                wait_time = generate_skewed_random(base=5, skew=-0.5, max_value=args.wait_max, offset=10, as_int=False)
                clrprint(f"--- Waiting {wait_time:.0f} seconds before simulate ---", clr='c')
                time.sleep(wait_time)

                try:
                    simulate_browsing(page)
                except Exception:
                    logger.exception("Extra simulation %d failed.", i + 1)

                clrprint(f"=== {i + 1} / {args.extra_simulations} Simulation complete ===", clr='y')

            logger.info("Closing browser context...")
            browser.close()
            logger.info("Browser closed. All URLs processed.")
    except Exception:
        logger.exception("Main execution failed.")
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
