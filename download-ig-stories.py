import sys
import time
import logging
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from clrprint import clrprint
from rich.console import Console
from simulate_browsing import simulate_browsing         # <-- imported from separate file
from beta import generate_skewed_random    				# <-- imported from separate file

import time
import numpy as np

console = Console()

# === CONFIGURATION ===
USER_DATA_DIR = r"T:\bench\GoogleChromePortable64\Data\profile"
CHROME_EXECUTABLE = r"T:\bench\GoogleChromePortable64\App\Chrome-bin\chrome.exe"

# Base dir for gallery-dl
GDL_DIR = Path(r"C:\Programs\gallery-dl-v1.26.8")
COOKIES_FILE = GDL_DIR / "www.instagram.com_cookies.txt"
URLS_FILE = GDL_DIR / "instagram-stories.txt"

# Script that downloads a single story
SINGLE_DL_SCRIPT = Path(r"T:\bench\single_story.py")

EXTRA_SIMULATIONS = 5               # Number of extra browsing simulations after main loop
WAIT_TIME_MAX = 100                 # Max wait time between actions

CHROMIUM_LAUNCH_ARGS = [
    "--disable-background-networking",
    "--disable-extensions",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--mute-audio",
    # "--single-process",       # Debug only; unstable in production, so left disabled
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
    "--disk-cache-dir=T:\bench\GoogleChromePortable64\Cache",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Helpers ---
def set_title(text: str):
    sys.stdout.write(f"\33]0;{text}\a")
    sys.stdout.flush()

def save_cookies_netscape_format(cookies, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            domain = cookie["domain"]
            if not domain.startswith("."):
                domain = "." + domain
            domain_initial_dot = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expires = str(int(cookie.get("expires", 0))) if cookie.get("expires", 0) else "0"
            name = cookie["name"]
            value = cookie["value"]
            f.write("\t".join([
                domain,
                domain_initial_dot,
                path,
                secure,
                expires,
                name,
                value
            ]) + "\n")

# --- Main ---
def main():
    logging.info("Reading URLs from %s", URLS_FILE)
    urls = [u.strip() for u in URLS_FILE.read_text(encoding="utf-8").splitlines() if u.strip()]
    logging.info("Total URLs loaded: %d", len(urls))

    if not urls:
        logging.warning("No URLs found in instagram-stories.txt — exiting.")
        return

    logging.info("Launching persistent Chromium context...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=CHROME_EXECUTABLE,
            headless=True,
            viewport={"width": 1920, "height": 1080},
            args=CHROMIUM_LAUNCH_ARGS
        )
        logging.info("Browser launched successfully.")
        page = browser.new_page()

        for idx, url in enumerate(urls, start=1):
            set_title(f"IG Stories [{idx}/{len(urls)}] - {url}")
            clrprint(f"=== [{idx}/{len(urls)}] Processing URL: {url} ===", clr='g')

            # Full browsing simulation from external module
            time.sleep(1)  # Wait 2 seconds between each simulation
            simulate_browsing(page)
            time.sleep(2)  # Wait 2 seconds between each simulation

            # logging.info("Exporting cookies to %s", COOKIES_FILE)
            cookies = browser.cookies("https://www.instagram.com")
            save_cookies_netscape_format(cookies, COOKIES_FILE)
            # logging.info("Cookies export complete.")
            time.sleep(1)  # Wait 2 seconds between each simulation

            # logging.info("Invoking single_story.py for current URL...")
            subprocess.run([sys.executable, str(SINGLE_DL_SCRIPT), url], check=False)
            # logging.info("single_story.py finished for current URL.")

            clrprint(f"=== Finished [{idx}/{len(urls)}] ===", clr='y')
            
        # Extra browsing calls to mimic activity and maintain session
        for i in range(EXTRA_SIMULATIONS):
            # clrprint(f"=== [{i+1}/{EXTRA_SIMULATIONS}] Starting simulation ===", clr='g')
            console.print(f"[#00FFFF]=== {i+1} / {EXTRA_SIMULATIONS} Starting simulation ===[/#00FFFF]")

            # wait_time = np.random.beta(alpha, beta) * WAIT_TIME_MAX + 10
            wait_time = generate_skewed_random(base=5, skew=-0.5, max_value=WAIT_TIME_MAX, offset=10, as_int=False)
            
            clrprint(f"--- Waiting {wait_time:.0f} seconds before simulate ---", clr='c')
            time.sleep(wait_time)   # Wait 2 seconds between each simulation
            
            simulate_browsing(page)

            clrprint(f"=== {i+1} / {EXTRA_SIMULATIONS} Simulation complete ===", clr='y')

        logging.info("Closing browser context...")
        browser.close()
        logging.info("Browser closed. All URLs processed.")

if __name__ == "__main__":
    main()
