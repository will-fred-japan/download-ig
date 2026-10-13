# 2025-10-04 14:58:49
# ig acc language need english, for buttons lookup

import time
import random
import logging
import numpy as np
from beta import generate_skewed_random             # <-- imported from separate file

# --- Log Formatting Constants ---
# 256-color light grey (250 = soft light grey/silver, 252 = even brighter)
GREY_COLOR = "\033[38;5;245m"
RESET_COLOR = "\033[0m"

# --- Module-specific logger (isolated from parent scripts) ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f"{GREY_COLOR}%(asctime)s [%(levelname)s] %(message)s{RESET_COLOR}",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Stop logs from bubbling up to the root logger to avoid duplicate prints
logger.propagate = False

# === Browsing behaviour constants ===
REPEAT_RANGE = 3                    # Cycle count range
SCROLL_RANGE = 6                    # Scrolls per cycle
WAIT_TIME_MAX = 35                  # Max wait time between actions
MAX_SCROLLS_TRY = 3                 # Max scroll attempts before giving up
ARTICLES_COUNT = 0                  # Number of articles to interact with
SCROLL_AMOUNT_PIXEL = (500, 1000)   # Scroll distance range

CONNECTION_MAX_RETRIES = 3          # Max retry attempts for navigation
CONNECTION_RETRY_DELAY = 3                    

def wait_for_article(page, scrolls=MAX_SCROLLS_TRY):
    """Scroll until at least ARTICLES_COUNT+1 articles are found or max scrolls reached."""
    for attempt in range(scrolls):
        try:
            page.wait_for_selector("article", timeout=5000)
            articles = page.locator("article")
            if articles.count() > ARTICLES_COUNT:
                # logger.info(f"Found articles after {attempt + 1} scroll(s).")
                return articles
        except:
            pass
        logger.info(f"No articles yet. Scrolling... ({attempt + 1}/{scrolls})")
        scroll_amount = random.randint(*SCROLL_AMOUNT_PIXEL)
        page.mouse.wheel(0, scroll_amount)
        time.sleep(5)
    logger.warning("No articles found after scrolling.")
    return None

def simulate_browsing(page):
    """
    Simulate Instagram browsing: scroll feed, like, bookmark.
    Uses the existing Playwright page object from the main script.
    Retries navigation on transient failures.
    """
    url = "https://www.instagram.com/"

    for attempt in range(1, CONNECTION_MAX_RETRIES + 1):
        try:
            logger.info(f"[Attempt {attempt} / {CONNECTION_MAX_RETRIES}] Navigating to Instagram feed...")
            page.goto(url, timeout=20000)
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < CONNECTION_MAX_RETRIES:
                time.sleep(CONNECTION_RETRY_DELAY)
            else:
                logger.error(f"All {CONNECTION_MAX_RETRIES} attempts failed for {url}")
                return  # Early exit if navigation fails

    page.set_default_timeout(5000)
    page.set_default_navigation_timeout(5000)

    articles = wait_for_article(page)
    if not articles:
        logger.warning("No articles found — skipping interaction.")
        return

    repeat_count = generate_skewed_random(base=2, skew=-0.25, max_value=REPEAT_RANGE, offset=1, as_int=True)
    # logger.info(f"Total cycles: {repeat_count}")

    for cycle in range(repeat_count):
        available = articles.count()
        index = min(cycle, available - 1)

        # Decide action: 1=like only, 2=bookmark only, 3=both
        action = random.choice([1, 2, 3])

        # Log the chosen action
        action_map = {1: "Like only", 2: "Bookmark only", 3: "Both"}
        # logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Action chosen: {action_map[action]}")

        like_failed = False
        bookmark_failed = False

        # --- Like ---
        if action in (1, 3):
            try:
                like_button = articles.nth(index).locator("svg[aria-label='Like'], svg[aria-label='Unlike']")
                label = like_button.get_attribute("aria-label")
                if label == "Like":
                    like_button.click(timeout=5000)
                    logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Article #{index + 1} Liked")
                else:
                    logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Already liked")
            except Exception as e:
                like_failed = True
                logger.warning(f"[Cycle {cycle + 1} / {repeat_count}] Like failed: {type(e).__name__} - {e}")

        # --- Bookmark ---
        if action in (2, 3):
            try:
                bookmark_button = articles.nth(index).locator("svg[aria-label='Save'], svg[aria-label='Unsave']")
                label = bookmark_button.get_attribute("aria-label")
                if label == "Save":
                    bookmark_button.click(timeout=5000)
                    logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Article #{index + 1} Bookmarked")
                else:
                    logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Already bookmarked")
            except Exception as e:
                bookmark_failed = True
                logger.warning(f"[Cycle {cycle + 1} / {repeat_count}] Bookmark failed: {type(e).__name__} - {str(e).splitlines()[0]}")

        # --- Dual failure handling ---
        if (action in (1, 3) and like_failed) and (action in (2, 3) and bookmark_failed):
            try:
                html = articles.nth(index).inner_html()
                logger.warning(f"[Cycle {cycle + 1} / {repeat_count}] Dumping article HTML due to dual failure:\n{html}")
            except Exception as e:
                logger.error(f"[Cycle {cycle + 1} / {repeat_count}] Failed to retrieve article HTML: {type(e).__name__} - {e}")

        # Scroll further
        # scrolls = random.randint(*SCROLL_RANGE)
        # scrolls = generate_skewed_random(base=2, skew=-0.25, max_value=SCROLL_RANGE, offset=2, as_int=True)
        scrolls = generate_skewed_random(base=5, skew=-0.75, max_value=SCROLL_RANGE, offset=2, as_int=True, max_streak=2)

        for i in range(1, scrolls + 1):
            scroll_amount = random.randint(*SCROLL_AMOUNT_PIXEL)
            page.mouse.wheel(0, scroll_amount)

            # wait_time = np.random.beta(alpha, beta) * WAIT_TIME_MAX + 1
            
            wait_time = generate_skewed_random(base=5, skew=-0.75, max_value=WAIT_TIME_MAX, offset=2, as_int=False)

            # logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Scrolling down {i} / {scrolls} ... waiting {wait_time:.0f} seconds")
            logger.info(f"[Cycle {cycle + 1} / {repeat_count}] Scrolling down {i} / {scrolls} ... waiting {wait_time:>2.0f} seconds")

            time.sleep(wait_time)