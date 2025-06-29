import sys
import types
import unittest

# Provide a minimal mock for playwright to allow importing the crawler
mock_playwright = types.ModuleType("playwright.sync_api")
mock_playwright.sync_playwright = lambda *a, **kw: None
class TimeoutError(Exception):
    pass
mock_playwright.TimeoutError = TimeoutError
sys.modules.setdefault("playwright.sync_api", mock_playwright)

from otodombot.scraper.crawler import OtodomCrawler


class ParseFloorTest(unittest.TestCase):
    def setUp(self):
        self.crawler = OtodomCrawler()

    def test_parse_numeric_floor(self):
        html = "<div><p>Piętro:</p><p>4/9</p></div>"
        self.assertEqual(self.crawler.parse_floor(html), "4/9")

    def test_parse_parter_with_total(self):
        html = "<div><p>Piętro:</p><p>parter/5</p></div>"
        self.assertEqual(self.crawler.parse_floor(html), "parter/5")

    def test_parse_parter_only(self):
        html = "<div><p>Piętro:</p><p>parter</p></div>"
        self.assertEqual(self.crawler.parse_floor(html), "parter")

    def test_no_floor_info(self):
        html = "<div><p>Brak danych</p></div>"
        self.assertIsNone(self.crawler.parse_floor(html))


if __name__ == "__main__":
    unittest.main()
