import time
import random
from playwright.sync_api import sync_playwright


def fetch_page_content(url: str) -> str:
    """
    Start a headless browser, visit URL, and return the full page HTML source.
    """
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

            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Let dynamic content load
            page.wait_for_timeout(3000)

            # Scroll down to trigger lazy-loaded product listings
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

            html_content = page.content()
            return html_content

        except Exception as e:
            print(f"[Error] Failed to fetch {url}: {e}")
            raise e

        finally:
            context.close()
            browser.close()