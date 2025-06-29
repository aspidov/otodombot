import pytest
from otodombot.scraper.crawler import OtodomCrawler


def test_parse_floor_basic():
    html = '<div><p>Piętro:</p><p>1/4</p></div>'
    crawler = OtodomCrawler()
    assert crawler.parse_floor(html) == '1/4'


def test_parse_floor_complex():
    html = (
        '<div data-sentry-element="ItemGridContainer">'
        '<p class="esen0m92 css-1airkmu">Piętro:</p>'
        '<p class="esen0m92 css-1airkmu">5/5</p>'
        '</div>'
    )
    crawler = OtodomCrawler()
    assert crawler.parse_floor(html) == '5/5'


def test_parse_floor_with_span():
    html = '<div><p>Piętro:</p><p><span>1</span>/4</p></div>'
    crawler = OtodomCrawler()
    assert crawler.parse_floor(html) == '1/4'
