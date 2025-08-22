import json
import os
from bs4 import BeautifulSoup

from yad2.core import Yad2SearchParameters, RealEstateListing
from yad2.scrapers import Yad2Scraper


def test_build_search_url_and_from_url():
    params = Yad2SearchParameters(maxPrice=1000000, city=5000)
    scraper = Yad2Scraper(params)
    url = scraper.build_search_url(page=2)
    assert "maxPrice=1000000" in url
    assert "city=5000" in url
    assert "page=2" in url

    cloned = Yad2Scraper.from_url(url)
    original = {k: str(v) for k, v in scraper.search_params.get_active_parameters().items()}
    assert cloned.search_params.get_active_parameters() == original


def test_extract_listing_info():
    html = """
    <div class='card_cardBox__KLi9I'>
        <span data-testid='price'>1,234 ₪</span>
        <span class='item-data-content_heading__tphH4'>Main St</span>
        <span class='item-data-content_itemInfoLine__AeoPP'></span>
        <span class='item-data-content_itemInfoLine__AeoPP'>3 חדרים • קומה 2 • 80 מ"ר</span>
        <a href='/item/123'></a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    scraper = Yad2Scraper()
    listing = scraper.extract_listing_info(soup)
    assert listing.price == 1234
    assert listing.rooms == 3
    assert listing.size == 80
    assert listing.listing_id == "123"


def test_scrape_page_with_mocked_fetch(monkeypatch):
    html = """
    <div class='card_cardBox__KLi9I'>
      <a class='item-layout_itemLink__CZZ7w' href='/item/1'>
        <span data-testid='price'>1,000 ₪</span>
        <span class='item-data-content_heading__tphH4'>Addr</span>
        <span class='item-data-content_itemInfoLine__AeoPP'></span>
        <span class='item-data-content_itemInfoLine__AeoPP'>2 חדרים • קומה 1 • 50 מ"ר</span>
      </a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    scraper = Yad2Scraper()
    monkeypatch.setattr(scraper, "fetch_page", lambda url: soup)
    assets = scraper.scrape_page(1)
    assert len(assets) == 1
    assert assets[0].price == 1000


def test_scrape_all_pages_aggregates_results(monkeypatch):
    scraper = Yad2Scraper()

    def fake_scrape_page(page):
        if page > 2:
            return []
        l = RealEstateListing()
        l.title = f"Listing {page}"
        return [l]

    monkeypatch.setattr(scraper, "scrape_page", fake_scrape_page)
    monkeypatch.setattr("time.sleep", lambda x: None)
    assets = scraper.scrape_all_pages(max_pages=3, delay=0)
    assert len(assets) == 2
    assert scraper.assets == assets


def test_get_search_summary_and_save(tmp_path):
    params = Yad2SearchParameters(maxPrice=500)
    scraper = Yad2Scraper(params)
    listing = RealEstateListing()
    listing.title = "t"
    listing.price = 1
    scraper.assets = [listing]
    summary = scraper.get_search_summary()
    assert summary["parameters"]["maxPrice"] == 500

    filename = os.path.join(tmp_path, "out.json")
    out = scraper.save_to_json(filename)
    assert out == filename
    with open(out, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["total_assets"] == 1
