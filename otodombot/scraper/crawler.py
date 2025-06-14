from typing import List, Optional
import logging
import re
from playwright.sync_api import sync_playwright

from ..config import SearchConditions


class OtodomCrawler:
    """Crawler for otodom.pl using Playwright."""

    BASE_URL = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa"

    def __init__(self, search: SearchConditions | None = None):
        self.search = search or SearchConditions()

    def build_url(self) -> str:
        params: list[str] = []
        if self.search.max_price:
            params.append(f"priceMax={self.search.max_price}")
        if self.search.rooms:
            params.append(f"roomsNumber={self.search.rooms}")
        if self.search.market:
            params.append(f"market={self.search.market.value}")
        if self.search.min_area:
            params.append(f"areaMin={self.search.min_area}")
        query = "&".join(params)
        url = self.BASE_URL + ("?" + query if query else "")
        logging.debug("Built search URL: %s", url)
        return url

    def fetch_listings(self) -> List[str]:
        """Fetch listing URLs from otodom."""
        url = self.build_url()
        logging.info("Fetching listings from %s", url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")
            links = page.eval_on_selector_all(
                "article a[data-cy='listing-item-link']",
                "elements => elements.map(el => el.href)"
            )
            browser.close()
        logging.info("Fetched %d listing links", len(links))
        return links

    def fetch_listing_details(self, url: str) -> str:
        """Placeholder for fetching a single listing page."""
        logging.debug("Fetching details for %s", url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
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
                    price = int(m.group(1))
                    logging.debug("Parsed price: %s", price)
                    return price
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
                    listing_id = int(m.group(1))
                    logging.debug("Parsed listing id: %s", listing_id)
                    return listing_id
                except ValueError:
                    continue
        return None
