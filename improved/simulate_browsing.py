import logging
import random
import time
from typing import Optional

from beta import generate_skewed_random

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.propagate = False

REPEAT_RANGE = 3
SCROLL_RANGE = 6
WAIT_TIME_MAX = 35
MAX_SCROLLS_TRY = 3
ARTICLES_COUNT = 0
SCROLL_AMOUNT_PIXEL = (500, 1000)
CONNECTION_MAX_RETRIES = 3
CONNECTION_RETRY_DELAY = 3


def wait_for_article(page, scrolls: int = MAX_SCROLLS_TRY, timeout_ms: int = 5000):
    """Scroll until at least one article is visible or the scroll budget is exhausted."""
    for attempt in range(scrolls):
        try:
            page.wait_for_selector("article", timeout=timeout_ms)
            articles = page.locator("article")
            if articles.count() > ARTICLES_COUNT:
                return articles
        except Exception:
            pass

        logger.info("No articles yet. Scrolling... (%s/%s)", attempt + 1, scrolls)
        page.mouse.wheel(0, random.randint(*SCROLL_AMOUNT_PIXEL))
        time.sleep(5)

    logger.warning("No articles found after scrolling.")
    return None


def safe_click(locator, timeout_ms: int = 5000, label: str = "element"):
    """Best-effort click with a readable fallback for failures."""
    try:
        locator.click(timeout=timeout_ms)
        return True
    except Exception as exc:
        logger.warning("%s click failed: %s", label, exc)
        return False


def simulate_browsing(page, url: str = "https://www.instagram.com/", max_attempts: int = CONNECTION_MAX_RETRIES):
    """
    Simulate Instagram browsing: navigate, wait for articles, react to a few posts, and scroll.
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info("[Attempt %s/%s] Navigating to Instagram feed...", attempt, max_attempts)
            page.goto(url, timeout=20000)
            break
        except Exception as exc:  # pragma: no cover - browser dependent
            last_error = exc
            logger.warning("Attempt %s failed: %s", attempt, exc)
            if attempt < max_attempts:
                time.sleep(CONNECTION_RETRY_DELAY)
    else:
        logger.error("All %s attempts failed for %s", max_attempts, url)
        return

    page.set_default_timeout(5000)
    page.set_default_navigation_timeout(5000)

    articles = wait_for_article(page)
    if not articles:
        logger.warning("No articles found — skipping interaction.")
        return

    repeat_count = generate_skewed_random(base=2, skew=-0.25, max_value=REPEAT_RANGE, offset=1, as_int=True)

    for cycle in range(repeat_count):
        available = articles.count()
        index = min(cycle, max(available - 1, 0))
        action = random.choice([1, 2, 3])
        action_map = {1: "Like only", 2: "Bookmark only", 3: "Both"}
        logger.info("[Cycle %s/%s] Action chosen: %s", cycle + 1, repeat_count, action_map[action])

        like_failed = False
        bookmark_failed = False
        article = articles.nth(index)

        if action in (1, 3):
            try:
                like_button = article.locator("svg[aria-label='Like'], svg[aria-label='Unlike']")
                if like_button.count():
                    label = like_button.first.get_attribute("aria-label")
                    if label == "Like":
                        safe_click(like_button.first, label="like")
                        logger.info("[Cycle %s/%s] Article #%s liked", cycle + 1, repeat_count, index + 1)
                    else:
                        logger.info("[Cycle %s/%s] Already liked", cycle + 1, repeat_count)
                else:
                    logger.warning("[Cycle %s/%s] Like control not found for article #%s", cycle + 1, repeat_count, index + 1)
                    like_failed = True
            except Exception as exc:
                like_failed = True
                logger.warning("[Cycle %s/%s] Like failed: %s", cycle + 1, repeat_count, exc)

        if action in (2, 3):
            try:
                bookmark_button = article.locator("svg[aria-label='Save'], svg[aria-label='Unsave']")
                if bookmark_button.count():
                    label = bookmark_button.first.get_attribute("aria-label")
                    if label == "Save":
                        safe_click(bookmark_button.first, label="bookmark")
                        logger.info("[Cycle %s/%s] Article #%s bookmarked", cycle + 1, repeat_count, index + 1)
                    else:
                        logger.info("[Cycle %s/%s] Already bookmarked", cycle + 1, repeat_count)
                else:
                    logger.warning("[Cycle %s/%s] Bookmark control not found for article #%s", cycle + 1, repeat_count, index + 1)
                    bookmark_failed = True
            except Exception as exc:
                bookmark_failed = True
                logger.warning("[Cycle %s/%s] Bookmark failed: %s", cycle + 1, repeat_count, exc)

        if like_failed and bookmark_failed:
            try:
                html = article.inner_html()
                logger.warning("[Cycle %s/%s] Dumping article HTML due to dual failure:\n%s", cycle + 1, repeat_count, html)
            except Exception as exc:
                logger.error("[Cycle %s/%s] Failed to retrieve article HTML: %s", cycle + 1, repeat_count, exc)

        scrolls = generate_skewed_random(base=5, skew=-0.75, max_value=SCROLL_RANGE, offset=2, as_int=True, max_streak=2)
        for n in range(1, scrolls + 1):
            scroll_amount = random.randint(*SCROLL_AMOUNT_PIXEL)
            page.mouse.wheel(0, scroll_amount)
            wait_time = generate_skewed_random(base=5, skew=-0.75, max_value=WAIT_TIME_MAX, offset=2, as_int=False)
            logger.info("[Cycle %s/%s] Scrolling down %s/%s ... waiting %2.0f seconds", cycle + 1, repeat_count, n, scrolls, wait_time)
            time.sleep(wait_time)

    logger.info("Browsing simulation complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("This module is intended to be imported; run from the main downloader script instead.")
