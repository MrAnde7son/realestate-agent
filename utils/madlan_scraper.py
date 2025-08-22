import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import urllib.parse


@dataclass
class MadlanListingData:
    """Data class to represent a Madlan property listing"""
    price: Optional[str]
    address: Optional[str]
    neighborhood: Optional[str]
    rooms: Optional[str]
    floor: Optional[str]
    area_sqm: Optional[str]
    property_type: Optional[str]
    url: str
    description: str
    features: List[str]
    additional_details: Dict[str, str]


class MadlanConfig:
    """Configuration class for Madlan scraper"""
    
    def __init__(self):
        # The URL provided by the user (Ramat HaChayal Tel Aviv area)
        self.base_url = "https://www.madlan.co.il/for-sale/%D7%A9%D7%9B%D7%95%D7%A0%D7%94-%D7%A8%D7%9E%D7%AA-%D7%94%D7%97%D7%99%D7%99%D7%9C-%D7%AA%D7%9C-%D7%90%D7%91%D7%99%D7%91-%D7%99%D7%A4%D7%95-%D7%99%D7%A9%D7%A8%D7%90%D7%9C"
        self.filters = "filters=_0-11500000____villa%2Ccottage%2CdualCottage%2Cland______0-100000_______search-filter-top-bar&tracking_search_source=filter_apply&marketplace=residential"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        self.delay_between_pages = 8  # seconds
        self.delay_between_assets = 2  # seconds


class MadlanParser:
    """Class responsible for parsing HTML content from Madlan"""
    
    @staticmethod
    def extract_listing_card_info(card) -> Dict[str, Optional[str]]:
        """Extract basic information from listing card"""
        try:
            # Price extraction - using Madlan specific selectors
            price_elem = (card.select_one('[data-auto="property-price"]') or
                         card.select_one('.css-hqth87') or
                         card.select_one('[class*="price"]') or
                         card.select_one('.price'))
            price = price_elem.get_text(strip=True) if price_elem else None
            
            # Address extraction - Madlan specific
            address_elem = (card.select_one('[data-auto="property-address"]') or
                           card.select_one('.css-n4p85g') or
                           card.select_one('[class*="address"]') or
                           card.select_one('h2') or
                           card.select_one('h3'))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Rooms extraction - Madlan specific
            rooms_elem = (card.select_one('[data-auto="property-rooms"]') or
                         card.select_one('.css-q8j3hw') or
                         card.select_one('[class*="room"]') or
                         card.select_one('[class*="חד"]'))
            rooms = rooms_elem.get_text(strip=True) if rooms_elem else None
            
            # Floor extraction - Madlan specific
            floor_elem = (card.select_one('[data-auto="property-floor"]') or
                         card.select_one('[class*="floor"]') or
                         card.select_one('[class*="קומה"]'))
            floor = floor_elem.get_text(strip=True) if floor_elem else None
            
            # Area extraction - Madlan specific
            area_elem = (card.select_one('[data-auto="property-size"]') or
                        card.select_one('[class*="size"]') or
                        card.select_one('[class*="area"]') or
                        card.select_one('[class*="מ"]'))
            area = area_elem.get_text(strip=True) if area_elem else None
            
            # Try to extract property type from address if it contains type info
            prop_type = None
            if address:
                # Look for property type keywords in Hebrew
                if any(word in address for word in ['קוטג\'', 'קוטג', 'וילה', 'דירה', 'פנטהאוז', 'דופלקס']):
                    prop_type = address.split(',')[0].strip() if ',' in address else None
            
            return {
                "price": price,
                "address": address,
                "rooms": rooms,
                "area_sqm": area,
                "floor": floor,
                "property_type": prop_type
            }
        except Exception as e:
            print(f"Error extracting card info: {e}")
            return {}

    @staticmethod
    def extract_detailed_info(soup: BeautifulSoup) -> Dict[str, any]:
        """Extract detailed information from individual listing page"""
        try:
            # Description
            description_elem = (soup.select_one('[data-testid="description"]') or
                              soup.select_one('.description') or
                              soup.select_one('[class*="description"]') or
                              soup.select_one('p'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Features
            features = []
            feature_elements = (soup.select('[data-testid="feature"]') or
                              soup.select('.feature') or
                              soup.select('[class*="feature"]') or
                              soup.select('li'))
            for elem in feature_elements:
                feature_text = elem.get_text(strip=True)
                if feature_text and len(feature_text) < 100:  # Filter out very long text
                    features.append(feature_text)
            
            # Additional details
            details = {}
            detail_labels = soup.select('[class*="label"], [class*="key"], dt')
            detail_values = soup.select('[class*="value"], dd')
            
            if len(detail_labels) == len(detail_values):
                for label, value in zip(detail_labels, detail_values):
                    key = label.get_text(strip=True)
                    val = value.get_text(strip=True)
                    if key and val:
                        details[key] = val
            
            return {
                "description": description,
                "features": features,
                "additional_details": details
            }
        except Exception as e:
            print(f"Error extracting detailed info: {e}")
            return {"description": "", "features": [], "additional_details": {}}


class MadlanScraper:
    """Main scraper class for Madlan real estate assets"""
    
    def __init__(self, config: MadlanConfig):
        self.config = config
        self.session = requests.Session()
        self.parser = MadlanParser()
        self.assets: List[MadlanListingData] = []

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse page content"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, headers=self.config.headers, timeout=30)
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            else:
                print(f"Failed to fetch page: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching page: {e}")
            return None
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None

    def find_listing_cards(self, soup: BeautifulSoup) -> List:
        """Find all listing cards on the page using multiple possible selectors"""
        # Based on the actual Madlan HTML structure
        possible_selectors = [
            '[data-auto="listed-bulletin"]',  # Main Madlan card selector
            '.css-u1nut8',  # Specific class from the example
            '[data-auto-bulletin-type="bulletin"]',
            'div[data-auto="listed-bulletin"]',
            '.e10ue70711',  # Another class from the card
            '[class*="listed-bulletin"]',
            '[data-testid="listing-card"]',
            '.listing-card',
            '.property-card',
            '[class*="listing"]',
            '[class*="property"]',
            '[class*="card"]',
            'article',
            '.item'
        ]
        
        for selector in possible_selectors:
            cards = soup.select(selector)
            if cards and len(cards) > 0:  # Found cards
                print(f"Found {len(cards)} assets using selector: {selector}")
                # Debug: print structure of first card if in debug mode
                self._debug_card_structure(cards[0] if cards else None)
                return cards
        
        print("No listing cards found with standard selectors")
        print("Available elements on page:")
        # Debug: show what elements are available
        for tag in ['div', 'article', 'section']:
            elements = soup.find_all(tag, limit=10)
            if elements:
                print(f"Found {len(elements)} {tag} elements")
                for i, elem in enumerate(elements[:3]):
                    classes = elem.get('class', [])
                    data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                    print(f"  {tag}[{i}]: classes={classes}, data={data_attrs}")
        
        return []
    
    def _debug_card_structure(self, card):
        """Debug helper to understand card structure"""
        if not card:
            return
        
        print("=== DEBUG: Card Structure ===")
        print(f"Card classes: {card.get('class', [])}")
        print(f"Card data attributes: {[k for k in card.attrs.keys() if k.startswith('data-')]}")
        
        # Look for price elements
        price_candidates = card.find_all(attrs={'data-auto': True})
        print(f"Elements with data-auto: {[(elem.name, elem.get('data-auto')) for elem in price_candidates[:5]]}")
        
        # Look for text content that might be price, address, etc.
        text_elements = [elem for elem in card.find_all(string=True) if elem.strip()]
        print(f"Text content samples: {[text.strip() for text in text_elements[:10] if len(text.strip()) > 2]}")
        print("=== END DEBUG ===\n")

    def extract_listing_url(self, card, base_domain="https://www.madlan.co.il") -> Optional[str]:
        """Extract the URL for individual listing from card"""
        # For Madlan, look for the specific clickable link
        link_elem = (card.select_one('[data-auto="listed-bulletin-clickable"]') or
                    card.select_one('a[href]') or
                    card.find('a') or
                    card.find_parent('a'))
        
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            if href.startswith('/'):
                return base_domain + href
            elif href.startswith('http'):
                return href
        return None

    def scrape_listing_details(self, listing_url: str) -> Dict[str, any]:
        """Scrape detailed information from individual listing page"""
        soup = self.get_page_content(listing_url)
        if not soup:
            return {"description": "", "features": [], "additional_details": {}}
        
        time.sleep(self.config.delay_between_assets)
        return self.parser.extract_detailed_info(soup)

    def process_listing(self, card) -> Optional[MadlanListingData]:
        """Process a single listing card"""
        try:
            # Extract basic info from card
            basic_info = self.parser.extract_listing_card_info(card)
            
            # Get listing URL
            listing_url = self.extract_listing_url(card)
            if not listing_url:
                print("Could not extract listing URL")
                return None
            
            # Get detailed information
            detailed_info = self.scrape_listing_details(listing_url)
            
            return MadlanListingData(
                price=basic_info.get("price"),
                address=basic_info.get("address"),
                neighborhood="רמת החייל תל אביב יפו",  # From the URL
                rooms=basic_info.get("rooms"),
                floor=basic_info.get("floor"),
                area_sqm=basic_info.get("area_sqm"),
                property_type=basic_info.get("property_type"),
                url=listing_url,
                description=detailed_info.get("description", ""),
                features=detailed_info.get("features", []),
                additional_details=detailed_info.get("additional_details", {})
            )
            
        except Exception as e:
            print(f"Error processing listing: {e}")
            return None

    def scrape_assets(self) -> List[MadlanListingData]:
        """Main method to scrape all assets"""
        page = 1
        
        while True:
            print(f"Scraping page {page}...")
            
            # Construct URL with page parameter
            if page == 1:
                url = f"{self.config.base_url}?{self.config.filters}"
            else:
                url = f"{self.config.base_url}?{self.config.filters}&page={page}"
            
            soup = self.get_page_content(url)
            if not soup:
                print(f"Failed to get page {page}")
                break
            
            # Find listing cards
            cards = self.find_listing_cards(soup)
            if not cards:
                print(f"No more assets found on page {page}")
                break
            
            print(f"Processing {len(cards)} assets from page {page}")
            
            # Process each listing
            page_listing_count = 0
            for card in cards:
                listing = self.process_listing(card)
                if listing:
                    self.assets.append(listing)
                    page_listing_count += 1
                    print(f"Processed listing: {listing.address}")
            
            if page_listing_count == 0:
                print("No valid assets found on this page")
                break
            
            page += 1
            time.sleep(self.config.delay_between_pages)
            
            # Safety limit to prevent infinite loops
            if page > 50:
                print("Reached page limit (50)")
                break

        print(f"Total assets found: {len(self.assets)}")
        return self.assets

    def save_to_csv(self, filename: str = "madlan_assets.csv"):
        """Save assets to CSV file"""
        if not self.assets:
            print("No assets to save")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'price', 'address', 'neighborhood', 'rooms', 'floor', 
                'area_sqm', 'property_type', 'url', 'description', 'features'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for listing in self.assets:
                # Convert features list to string
                features_str = '; '.join(listing.features) if listing.features else ""
                
                writer.writerow({
                    'price': listing.price,
                    'address': listing.address,
                    'neighborhood': listing.neighborhood,
                    'rooms': listing.rooms,
                    'floor': listing.floor,
                    'area_sqm': listing.area_sqm,
                    'property_type': listing.property_type,
                    'url': listing.url,
                    'description': listing.description,
                    'features': features_str
                })
        
        print(f"Saved {len(self.assets)} assets to {filename}")

    def save_detailed_csv(self, filename: str = "madlan_assets_detailed.csv"):
        """Save assets with all additional details to CSV"""
        if not self.assets:
            print("No assets to save")
            return

        # Collect all possible detail keys
        all_detail_keys = set()
        for listing in self.assets:
            all_detail_keys.update(listing.additional_details.keys())

        fieldnames = [
            'price', 'address', 'neighborhood', 'rooms', 'floor', 
            'area_sqm', 'property_type', 'url', 'description', 'features'
        ] + list(all_detail_keys)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for listing in self.assets:
                row_data = {
                    'price': listing.price,
                    'address': listing.address,
                    'neighborhood': listing.neighborhood,
                    'rooms': listing.rooms,
                    'floor': listing.floor,
                    'area_sqm': listing.area_sqm,
                    'property_type': listing.property_type,
                    'url': listing.url,
                    'description': listing.description,
                    'features': '; '.join(listing.features) if listing.features else ""
                }
                
                # Add additional details
                for key in all_detail_keys:
                    row_data[key] = listing.additional_details.get(key, "")
                
                writer.writerow(row_data)
        
        print(f"Saved {len(self.assets)} detailed assets to {filename}")


def main():
    """Main function to run the Madlan scraper"""
    print("Starting Madlan scraper for Ramat HaChayal, Tel Aviv...")
    
    config = MadlanConfig()
    scraper = MadlanScraper(config)
    
    try:
        assets = scraper.scrape_assets()
        if assets:
            scraper.save_to_csv()
            scraper.save_detailed_csv()
            print(f"\nScraping completed successfully!")
            print(f"Found {len(assets)} assets")
            print(f"Files saved:")
            print("- madlan_assets.csv (basic info)")
            print("- madlan_assets_detailed.csv (with all details)")
        else:
            print("No assets were found. This might be due to:")
            print("1. Website structure changes")
            print("2. Anti-scraping measures")
            print("3. Network issues")
            print("4. No assets available in the specified area")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        if scraper.assets:
            scraper.save_to_csv()
            print(f"Saved {len(scraper.assets)} assets before interruption")
    except Exception as e:
        print(f"An error occurred: {e}")
        if scraper.assets:
            scraper.save_to_csv()
            print(f"Saved {len(scraper.assets)} assets before error")


if __name__ == "__main__":
    main() 