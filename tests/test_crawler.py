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
        html = (
            '<div data-sentry-element="ItemGridContainer" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="css-1xw0jqp esen0m91">'
            '<p data-sentry-element="Item" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="esen0m92 css-1airkmu">Piętro:</p>'
            '<p class="esen0m92 css-1airkmu">4/9</p>'
            '</div>'
        )
        self.assertEqual(self.crawler.parse_floor(html), "4/9")

    def test_parse_parter_with_total(self):
        html = (
            '<div data-sentry-element="ItemGridContainer" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="css-1xw0jqp esen0m91">'
            '<p data-sentry-element="Item" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="esen0m92 css-1airkmu">Piętro:</p>'
            '<p class="esen0m92 css-1airkmu">parter/5</p>'
            '</div>'
        )
        self.assertEqual(self.crawler.parse_floor(html), "parter/5")

    def test_parse_parter_only(self):
        html = (
            '<div data-sentry-element="ItemGridContainer" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="css-1xw0jqp esen0m91">'
            '<p data-sentry-element="Item" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="esen0m92 css-1airkmu">Piętro:</p>'
            '<p class="esen0m92 css-1airkmu">parter</p>'
            '</div>'
        )
        self.assertEqual(self.crawler.parse_floor(html), "parter")

    def test_no_floor_info(self):
        html = (
            '<div data-sentry-element="ItemGridContainer" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="css-1xw0jqp esen0m91">'
            '<p data-sentry-element="Item" '
            'data-sentry-source-file="AdDetailItem.tsx" '
            'class="esen0m92 css-1airkmu">Powierzchnia:</p>'
            '<p class="esen0m92 css-1airkmu">76&nbsp;m²</p>'
            '</div>'
        )
        self.assertIsNone(self.crawler.parse_floor(html))


if __name__ == "__main__":
    unittest.main()
