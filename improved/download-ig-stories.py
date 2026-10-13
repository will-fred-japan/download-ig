"""Improved download-ig-stories.py

This version adds:
- CLI configuration (paths, headless, simulations)
- Better error handling and logging
- Randomized wait times using generate_skewed_random
- Safer subprocess invocation and per-URL error isolation
- Ensures browser context is always closed
- Minor cleanups (removed duplicate imports, clearer messages)

Drop this file into a new folder `improved/` in the repository.
"""

import sys
import time
import logging
import subprocess
import argparse
from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright
from clrprint import clrprint
from rich.console import Console

from simulate_browsing import simulate_browsing
from beta import generate_skewed_random

console = Console()

# Default configuration (kept as constants but overrideable via CLI)
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
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("download-ig-stories")


def set_title(text: str) -> None:
    try:
        sys.stdout.write(f"\33]0;{text}\a")
        sys.stdout.flush()
    except Exception:
        # Non-fatal; ignore if terminal doesn't support titles
        pass


def save_cookies_netscape_format(cookies: List[dict], filename: Path) -> None:
    """Save cookies to a Netscape-format cookie file used by some tools (gallery-dl, wget, etc.)."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            # Keep domain exactly as returned; the leading dot is used to indicate domain-wide cookies
            domain = cookie.get("domain", "")
            domain_initial_dot = "TRUE" if domain.startswith('.') else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expires = str(int(cookie.get("expires", 0))) if cookie.get("expires") else "0"
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            # Write a single tab-separated line per cookie
            f.write("\t".join([
                domain,
                domain_initial_dot,
                path,
                secure,
                expires,
                name,
                value
            ]) + "\n")


def read_urls(urls_file: Path) -> List[str]:
    if not urls_file.exists():
        logger.warning("URLs file %s does not exist.", urls_file)
        return []
    text = urls_file.read_text(encoding="utf-8")
    urls = [u.strip() for u in text.splitlines() if u.strip()]
    return urls


def run_single_download(script: Path, url: str) -> int:
    """Run the single story downloader script for one URL. Returns subprocess return code."""
    try:
        # Use sys.executable to ensure same Python interpreter
        result = subprocess.run([sys.executable, str(script), url], check=False)
        return result.returncode
    except FileNotFoundError:
        logger.exception("Download script not found: %s", script)
        return -1
    except Exception:
        logger.exception("Error running download script for URL: %s", url)
        return -1


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Download Instagram stories with simulated browsing to keep session alive")
    parser.add_argument("--urls-file", type=Path, default=DEFAULT_URLS_FILE, help="Path to file with list of story URLs")
    parser.add_argument("--cookies-file", type=Path, default=DEFAULT_COOKIES_FILE, help="Path to write cookies (Netscape format)")
    parser.add_argument("--single-script", type=Path, default=DEFAULT_SINGLE_DL_SCRIPT, help="Path to single_story.py script")
    parser.add_argument("--user-data-dir", type=Path, default=DEFAULT_USER_DATA_DIR, help="Chrome user data dir for persistent context")
    parser.add_argument("--chrome-exe", type=Path, default=DEFAULT_CHROME_EXECUTABLE, help="Chrome / Chromium executable path")
    parser.add_argument("--extra-simulations", type=int, default=DEFAULT_EXTRA_SIMULATIONS)
    parser.add_argument("--wait-max", type=int, default=DEFAULT_WAIT_TIME_MAX)
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (default: headful). Note: original script used headless=True")

    args = parser.parse_args(argv)

    urls = read_urls(args.urls_file)
    logger.info("Loaded %d URLs from %s", len(urls), args.urls_file)

    if not urls:
        logger.warning("No URLs to process; exiting.")
        return 0

    logger.info("Launching persistent Chromium context using user data dir: %s", args.user_data_dir)

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(args.user_data_dir),
                executable_path=str(args.chrome_exe),
                headless=args.headless,
                viewport={"width": 1920, "height": 1080},
                args=CHROMIUM_LAUNCH_ARGS
            )
            logger.info("Browser launched.")
            page = browser.new_page()

            for idx, url in enumerate(urls, start=1):
                set_title(f"IG Stories [{idx}/{len(urls)}] - {url}")
                clrprint(f"=== [{idx}/{len(urls)}] Processing URL: {url} ===", clr='g')

                # Simulate browsing to keep the session fresh
                try:
                    # Small deterministic pause before simulation
                    time.sleep(1)
                    simulate_browsing(page)
                    time.sleep(1)
                except Exception:
                    logger.exception("simulate_browsing() failed for URL: %s", url)

                # Export cookies for gallery-dl or other tools
                try:
                    cookies = browser.cookies("https://www.instagram.com")
                    save_cookies_netscape_format(cookies, args.cookies_file)
                except Exception:
                    logger.exception("Failed to export cookies for URL: %s", url)

                # Invoke the single-story downloader for this URL
                try:
                    rc = run_single_download(args.single_script, url)
                    if rc != 0:
                        logger.warning("single_story.py returned non-zero exit code %d for URL: %s", rc, url)
                except Exception:
                    logger.exception("Error while running single_story for URL: %s", url)

                clrprint(f"=== Finished [{idx}/{len(urls)}] ===", clr='y')

            # Extra browsing calls to mimic activity and maintain session
            for i in range(args.extra_simulations):
                console.print(f"[#00FFFF]=== {i+1} / {args.extra_simulations} Starting simulation ===[/#00FFFF]")

                wait_time = generate_skewed_random(base=5, skew=-0.5, max_value=args.wait_max, offset=10, as_int=False)
                clrprint(f"--- Waiting {wait_time:.0f} seconds before simulate ---", clr='c')
                time.sleep(wait_time)

                try:
                    simulate_browsing(page)
                except Exception:
                    logger.exception("simulate_browsing() failed during extra simulation #%d", i+1)

                clrprint(f"=== {i+1} / {args.extra_simulations} Simulation complete ===", clr='y')

            logger.info("All done; closing browser context.")
            browser.close()

    except Exception:
        logger.exception("Failed to start or run browser loop")
        # Ensure the browser is closed if partially opened
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
