from collections.abc import Iterable


class DynamicPageCrawler:
    """Optional Playwright/Selenium entrypoint for company sites that need rendering.

    The project intentionally keeps dynamic crawling opt-in. Do not bypass logins,
    CAPTCHAs, robots.txt, terms of service, or anti-abuse controls.
    """

    def fetch_with_playwright(self, url: str, wait_for_selectors: Iterable[str] | None = None) -> str:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="InternMatchBot/0.1")
            page.goto(url, wait_until="networkidle", timeout=30_000)
            for selector in wait_for_selectors or []:
                page.wait_for_selector(selector, timeout=10_000)
            content = page.content()
            browser.close()
            return content
