import time
import random
from playwright.sync_api import sync_playwright


def fetch_page_content(url: str) -> str:
    
    # Start a headless browser, visit the URL, and return the rendered page HTML.
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()

        try:
            print(f"[Fetch] Visiting: {url}")

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Wait briefly for dynamic content.
            page.wait_for_timeout(3000)

            # Scroll to trigger lazy-loaded content if present.
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

            # Small random delay to reduce request pattern.
            time.sleep(random.uniform(1.0, 2.0))

            html_content = page.content()
            return html_content

        except Exception as e:
            print(f"[Error] Failed to fetch {url}: {e}")
            raise e

        finally:
            context.close()
            browser.close()


def fetch_page_with_retry(url: str, max_retries: int = 3, delay_seconds: int = 2) -> str:
    
    # Fetch a page with simple retry logic.
    # If fetching fails, retry a limited number of times before raising the final error.
    
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            return fetch_page_content(url)

        except Exception as e:
            last_error = e
            print(f"[Retry] Attempt {attempt}/{max_retries} failed for {url}: {e}")

            if attempt < max_retries:
                time.sleep(delay_seconds)

    raise last_error