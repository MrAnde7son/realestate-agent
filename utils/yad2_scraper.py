import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ListingData:
    """Data class to represent a property listing"""
    price: Optional[str]
    address: Optional[str]
    address_description: str
    bedroom: Optional[str]
    floor: Optional[str]
    sqm: Optional[str]
    url: str
    description_text: str
    details: Dict[str, str]
    features: List[str]


class Yad2Config:
    """Configuration class for Yad2 scraper"""
    
    def __init__(self):
        self.base_url = "https://www.yad2.co.il/realestate/forsale?maxPrice=10500000&property=5%2C33%2C39&topArea=2&area=1&city=5000&neighborhood=203"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)... Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        self.delay_between_pages = 10  # seconds


class Yad2Parser:
    """Class responsible for parsing HTML content from Yad2"""
    
    @staticmethod
    def extract_item_details(soup: BeautifulSoup) -> Dict[str, str]:
        """Extract detailed information from property page"""
        details = {}
        labels = soup.select("dd.item-detail_label__FnhAu")
        values = soup.select("dt.item-detail_value__QHPml")
        
        for label, value in zip(labels, values):
            key = label.text.strip()
            val = value.text.strip()
            details[key] = val
        return details

    @staticmethod
    def extract_features(soup: BeautifulSoup) -> List[str]:
        """Extract property features from page"""
        features = []
        for li in soup.select('[data-testid="in-property-item"]'):
            feature = li.select_one('span.in-property-item_text__aLvx0')
            if feature:
                features.append(feature.text.strip())
        return features

    @staticmethod
    def parse_listing_card(card) -> Dict[str, Optional[str]]:
        """Parse individual listing card from search results"""
        price = card.select_one('[data-testid="price"]')
        title = card.select_one("span.item-data-content_heading__tphH4")
        desc_lines = card.select("span.item-data-content_itemInfoLine__AeoPP")
        
        # Parse property details
        values = desc_lines[1].text.strip().split(' • ') if len(desc_lines) > 1 else []
        bedroom = values[0] if len(values) >= 1 else None
        floor = values[1] if len(values) >= 2 else None
        sqm = values[2] if len(values) >= 3 else None

        # Handle cases where sqm might be missing
        if not sqm:
            sqm = floor
            floor = bedroom
            bedroom = None

        return {
            "price": price.text.strip() if price else None,
            "address": title.text.strip() if title else None,
            "address_description": desc_lines[0].text.strip() if len(desc_lines) > 0 else "",
            "bedroom": bedroom.strip() if bedroom else None,
            "floor": floor.strip() if floor else None,
            "sqm": sqm.strip() if sqm else None,
        }


class Yad2Scraper:
    """Main scraper class for Yad2 real estate listings"""
    
    def __init__(self, config: Yad2Config):
        self.config = config
        self.session = requests.Session()
        self.parser = Yad2Parser()
        self.listings: List[ListingData] = []

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse page content"""
        try:
            response = self.session.get(url, headers=self.config.headers)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            else:
                print(f"Failed to fetch page: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None

    def scrape_listing_details(self, item_url: str) -> Dict[str, any]:
        """Scrape detailed information from individual listing page"""
        soup = self.get_page_content(item_url)
        if not soup:
            return {"description_text": "", "details": {}, "features": []}

        description_elem = soup.select_one("p.description_description__9t6rz")
        description = description_elem.text.strip() if description_elem else ""
        
        details = self.parser.extract_item_details(soup)
        features = self.parser.extract_features(soup)

        return {
            "description_text": description,
            "details": details,
            "features": features
        }

    def process_listing(self, item) -> Optional[ListingData]:
        """Process a single listing item"""
        card = item.find_parent("div", class_="card_cardBox__KLi9I")
        if not card:
            return None

        # Parse basic info from card
        basic_info = self.parser.parse_listing_card(card)
        if not basic_info["price"] or not basic_info["address"]:
            return None

        # Get detailed information
        item_url = 'https://www.yad2.co.il/' + item["href"]
        details = self.scrape_listing_details(item_url)

        return ListingData(
            price=basic_info["price"],
            address=basic_info["address"],
            address_description=basic_info["address_description"],
            bedroom=basic_info["bedroom"],
            floor=basic_info["floor"],
            sqm=basic_info["sqm"],
            url=item_url,
            description_text=details["description_text"],
            details=details["details"],
            features=details["features"]
        )

    def scrape_listings(self) -> List[ListingData]:
        """Main method to scrape all listings"""
        page = 1
        
        while True:
            print(f"Scraping page {page}...")
            url = f"{self.config.base_url}&page={page}"
            
            soup = self.get_page_content(url)
            if not soup:
                break

            items = soup.select("a.item-layout_itemLink__CZZ7w")
            if not items:
                print(f"No more items found on page {page}")
                break

            for item in items:
                listing = self.process_listing(item)
                if listing:
                    self.listings.append(listing)
                    print(f"Processed listing: {listing.address}")

            page += 1
            time.sleep(self.config.delay_between_pages)

        print(f"Total listings found: {len(self.listings)}")
        return self.listings

    def save_to_csv(self, filename: str = "yad2_listings.csv"):
        """Save listings to CSV file"""
        if not self.listings:
            print("No listings to save")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'price', 'address', 'address_description', 'bedroom', 
                'floor', 'sqm', 'url', 'description_text'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for listing in self.listings:
                writer.writerow({
                    'price': listing.price,
                    'address': listing.address,
                    'address_description': listing.address_description,
                    'bedroom': listing.bedroom,
                    'floor': listing.floor,
                    'sqm': listing.sqm,
                    'url': listing.url,
                    'description_text': listing.description_text
                })
        
        print(f"Saved {len(self.listings)} listings to {filename}")


def main():
    """Main function to run the scraper"""
    config = Yad2Config()
    scraper = Yad2Scraper(config)
    
    try:
        listings = scraper.scrape_listings()
        scraper.save_to_csv()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
