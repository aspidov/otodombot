from typing import List, Optional
import re
from playwright.sync_api import sync_playwright


class OtodomCrawler:
    """Crawler for otodom.pl using Playwright."""

    BASE_URL = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie"

    def fetch_listings(self) -> List[str]:
        """Fetch listing URLs from otodom."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(self.BASE_URL)
            page.wait_for_load_state("networkidle")
            links = page.eval_on_selector_all(
                "article a[data-cy='listing-item-link']",
                "elements => elements.map(el => el.href)"
            )
            browser.close()
        return links

    def fetch_listing_details(self, url: str) -> str:
        """Placeholder for fetching a single listing page."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        return html

    def parse_price(self, html: str) -> Optional[int]:
        """Extract listing price from HTML."""
        patterns = [
            r"\"price\"\s*:\s*\{[^}]*\"value\"\s*:\s*(\d+)",
            r"og:price:amount\" content=\"(\d+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, html)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        return None

    def parse_listing_id(self, html: str) -> Optional[int]:
        """Extract listing ID from HTML."""
        patterns = [
            r'"adId"\s*:\s*"?(\d+)',
            r'"advertId"\s*:\s*(\d+)',
            r'<meta property="og:url" content="[^"]*ID(\d+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, html)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        return None
