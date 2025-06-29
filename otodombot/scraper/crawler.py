from typing import List, Optional
import logging
import re
import urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from ..config import SearchConditions


class OtodomCrawler:
    """Crawler for otodom.pl using Playwright."""

    DEFAULT_BASE_URL = (
        "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie,rynek-wtorny/warszawa"
    )
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        search: SearchConditions | None = None,
        headless: bool = True,
        wait_timeout: int = 30000,
        base_url: str | None = None,
    ):
        self.search = search or SearchConditions()
        self.headless = headless
        # Maximum time to wait for page elements to load, in milliseconds.
        self.wait_timeout = wait_timeout
        self.base_url = base_url or self.DEFAULT_BASE_URL

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

    def build_url(self, sort_by: str = "DEFAULT", page=1) -> str:
        params: list[str] = []
        if self.search.max_price:
            params.append(f"priceMax={self.search.max_price}")
        if self.search.rooms:
            room_map = {
                1: "ONE",
                2: "TWO",
                3: "THREE",
                4: "FOUR",
                5: "FIVE",
            }
            enum_values = []
            for r in self.search.rooms:
                if r >= 5:
                    enum_values.append("FIVE_MORE" if r > 5 else room_map.get(5))
                else:
                    enum_values.append(room_map.get(r, str(r)))
            rooms_param = urllib.parse.quote(f"[{','.join(enum_values)}]")
            params.append(f"roomsNumber={rooms_param}")
        if self.search.min_area:
            params.append(f"areaMin={self.search.min_area}")
        sort = sort_by.upper() if sort_by else "DEFAULT"
        if self.search.build_year_min:
            params.append(f"buildYearMin={self.search.build_year_min}")
        if sort == "LATEST":
            params.append("by=LATEST&direction=DESC")
        else:
            params.append("by=DEFAULT&direction=DESC")
        params.append("page=" + str(page))
        query = "&".join(params)
        url = self.base_url + ("?" + query if query else "")
        logging.debug("Built search URL: %s", url)
        return url

    def fetch_listings(self, max_pages: int = 3, sort_by: str = "DEFAULT") -> List[str]:
        """Fetch listing URLs from otodom following pagination.

        Parameters
        ----------
        max_pages : int, optional
            Number of result pages to crawl in a single session. Defaults
            to ``3`` so that multiple pages are processed without the
            caller needing to pass an argument.
        sort_by : str, optional
            Sorting to use for fetching listings. Supported values are
            ``"DEFAULT"`` and ``"LATEST"``. Defaults to ``"DEFAULT"``.
        """
        all_links: list[str] = []
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=self.headless)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=self.USER_AGENT,
                locale="pl-PL",
            )
            page = context.new_page()
            for page_num in range(1, max_pages + 1):
                current_url = self.build_url(sort_by=sort_by, page=page_num)
                logging.info("Fetching listings from %s", current_url)
                page.goto(current_url, wait_until="domcontentloaded")
                self.accept_cookies(page)
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    page.wait_for_timeout(500)
                except Exception as exc:
                    logging.debug("Error scrolling listing page: %s", exc)
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(500)
                except Exception as exc:
                    logging.debug("Error scrolling listing page: %s", exc)
                try:
                    logging.debug("Waiting for listings to load on %s", current_url)
                    page.wait_for_selector(
                        "article a",
                        timeout=self.wait_timeout,
                    )
                except PlaywrightTimeoutError:
                    logging.warning(
                        "Timeout waiting for listings on %s; proceeding anyway",
                        current_url,
                    )
                links = page.eval_on_selector_all(
                    "article a",
                    "elements => elements.map(el => el.href)",
                )
                links = list(set(links)) # remove duplicates
                logging.info("Found %d links on page %s", len(links), page_num)
                all_links.extend(links)
            context.close()
            browser.close()
        logging.info("Fetched %d listing links", len(all_links))
        return all_links

    def fetch_listing_details(self, url: str) -> str:
        """Placeholder for fetching a single listing page."""
        logging.debug("Fetching details for %s", url)
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=self.headless)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=self.USER_AGENT,
                locale="pl-PL",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            self.accept_cookies(page)
            try:
                logging.debug("Waiting for listing page %s to load", url)
                page.wait_for_load_state("domcontentloaded", timeout=self.wait_timeout)
            except PlaywrightTimeoutError:
                logging.warning(
                    "Timeout waiting for listing %s; proceeding anyway",
                    url,
                )
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
            except Exception as exc:
                logging.debug("Error scrolling listing page: %s", exc)
            html = page.content()
            context.close()
            browser.close()
        return html

    def parse_price(self, html: str) -> Optional[int]:
        """Extract listing price from HTML."""
        patterns = [
            r"\"price\"\s*:\s*\{[^}]*\"value\"\s*:\s*(\d+)",
            r"og:price:amount\" content=\"(\d+)",
            r"data-cy=\"adPageHeaderPrice\"[^>]*>([^<]+)<",
        ]
        for pattern in patterns:
            m = re.search(pattern, html)
            if m:
                raw = m.group(1)
                digits = re.sub(r"\D", "", raw)
                if not digits:
                    continue
                try:
                    price = int(digits)
                    logging.debug("Parsed price: %s", price)
                    return price
                except ValueError:
                    continue
        return None

    def parse_listing_id(self, html: str) -> Optional[int]:
        """Extract listing ID from HTML."""
        patterns = [
            r"<title>.*?(\d{5,}).*?</title>",
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


    def parse_title(self, html: str) -> str:
        """Extract the listing title from HTML."""
        patterns = [
            r"<h1[^>]*>(.*?)</h1>",
            r'property="og:title" content="([^"]+)"',
            r"<title>(.*?)</title>",
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.DOTALL)
            if m:
                text = re.sub("<[^<]+?>", "", m.group(1)).strip()
                if text:
                    logging.debug("Parsed title: %s", text)
                    return text
        return ""

    def parse_floor(self, html: str) -> Optional[str]:
        """Extract floor information from the listing HTML."""
        pattern = (
            r"<p[^>]*>\s*Pi\u0119tro:\s*</p>\s*<p[^>]*>([^<]+)</p>"
        )
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if m:
            floor = m.group(1).strip()
            logging.debug("Parsed floor: %s", floor)
            return floor
        return None

    def parse_photos(self, html: str) -> List[str]:
        """Extract photo URLs from HTML."""
        urls: list[str] = []

        # Try to parse image data from the embedded Next.js JSON first
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if m:
            try:
                import json

                data = json.loads(m.group(1))
                images = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("ad", {})
                    .get("images", [])
                )
                for item in images:
                    if not isinstance(item, dict):
                        continue
                    for key in ("large", "medium", "small", "thumbnail"):
                        url = item.get(key)
                        if url:
                            urls.append(url)
                            break
            except Exception as exc:  # pragma: no cover - best effort
                logging.debug("Failed to parse __NEXT_DATA__ images: %s", exc)

        # Fallback to extracting from <img> tags if JSON was missing
        patterns = [
            r'<img[^>]+src="([^"]+\.(?:jpg|jpeg|png|webp))"',
            r'"image"\s*:\s*\{"url"\s*:\s*"([^"]+)"',
        ]
        for pattern in patterns:
            urls.extend(re.findall(pattern, html))

        # remove duplicates while preserving order and keep only CDN images
        seen = set()
        unique_urls = []
        for url in urls:
            if "olxcdn" not in url:
                continue
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)

        logging.debug("Parsed %d photo urls", len(unique_urls))
        return unique_urls
