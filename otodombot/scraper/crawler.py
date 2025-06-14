from typing import List, Optional
import logging
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from ..config import SearchConditions


class OtodomCrawler:
    """Crawler for otodom.pl using Playwright."""

    BASE_URL = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa"

    def __init__(self, search: SearchConditions | None = None):
        self.search = search or SearchConditions()

    def accept_cookies(self, page) -> None:
        """Attempt to accept cookie banners if present."""
        selectors = [
            "button:has-text('Akcept')",
            "button:has-text('Accept')",
            "button:has-text('Zgadzam')",
        ]
        for sel in selectors:
            try:
                page.click(sel, timeout=2000)
                logging.debug("Clicked cookie banner using selector %s", sel)
                return
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

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

    def fetch_listings(self, max_pages: int = 1) -> List[str]:
        """Fetch listing URLs from otodom following pagination."""
        url = self.build_url()
        logging.info("Fetching listings from %s", url)
        all_links: list[str] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            current_url = url
            for _ in range(max_pages):
                page.goto(current_url)
                self.accept_cookies(page)
                page.wait_for_load_state("networkidle")
                links = page.eval_on_selector_all(
                    "article a[data-cy='listing-item-link']",
                    "elements => elements.map(el => el.href)"
                )
                all_links.extend(links)
                next_link = page.query_selector("a[rel='next']")
                next_url = next_link.get_attribute("href") if next_link else None
                if not next_url:
                    break
                current_url = next_url
            context.close()
            browser.close()
        logging.info("Fetched %d listing links", len(all_links))
        return all_links

    def fetch_listing_details(self, url: str) -> str:
        """Placeholder for fetching a single listing page."""
        logging.debug("Fetching details for %s", url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url)
            self.accept_cookies(page)
            page.wait_for_load_state("networkidle")
            html = page.content()
            context.close()
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

    def parse_description(self, html: str) -> str:
        """Extract listing description from HTML."""
        patterns = [
            r"<div[^>]*data-cy=\"adPageAdDescription\"[^>]*>(.*?)</div>",
            r'<meta property="og:description" content="([^"]+)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.DOTALL)
            if m:
                text = re.sub("<[^<]+?>", "", m.group(1)).strip()
                if text:
                    logging.debug("Parsed description: %s", text[:30])
                    return text
        return ""

    def parse_address(self, html: str) -> str:
        """Extract address or location string from HTML."""
        patterns = [
            r'"address"\s*:\s*"([^"]+)"',
            r'<span[^>]*data-testid=\"address-link\"[^>]*>(.*?)</span>',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.DOTALL)
            if m:
                text = re.sub("<[^<]+?>", "", m.group(1)).strip()
                if text:
                    logging.debug("Parsed address: %s", text)
                    return text
        return ""
