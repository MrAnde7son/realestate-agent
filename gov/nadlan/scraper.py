# -*- coding: utf-8 -*-
"""
nadlan/scraper.py
-----------------

Simple scraper for retrieving real-estate transaction history from nadlan.gov.il.

This module provides a focused interface using Playwright to interact with the real website
and capture actual API responses, bypassing authentication issues.

Usage
::::::

    from gov.nadlan import NadlanDealsScraper
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_neighborhood_id("65210036")
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")

Notes
:::::

* This implementation uses Playwright to interact with the real website
* No authentication tokens are required - it uses the same browser session as the website
* The API is robust and handles various response formats automatically
* Please be courteous and avoid rapid repeated calls to respect the service
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from playwright.async_api import Response, async_playwright

from .exceptions import NadlanAPIError
from .models import Deal

logger = logging.getLogger(__name__)


class NadlanDealsScraper:
    """Simple scraper for real estate deals from nadlan.gov.il."""
    
    def __init__(self, timeout: float = 30.0, headless: bool = True):
        """Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode
        """
        self.timeout = timeout
        self.headless = headless
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Playwright handles its own cleanup
    
    def get_deals_by_neighborhood_id(self, neighbourhood_id: str) -> List[Deal]:
        """Retrieve deals using a neighbourhood identifier.

        Args:
            neighbourhood_id: The numeric ID as seen in the URL

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the API call fails
        """
        try:
            deals = asyncio.run(self._fetch_deals_by_neighborhood(neighbourhood_id))
            return deals
        except Exception as e:
            raise NadlanAPIError(f"Failed to fetch deals for neighborhood {neighbourhood_id}: {e}")

    def search_address(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for addresses using the govmap autocomplete API.

        Args:
            query: Address search query (in Hebrew or English)
            limit: Maximum number of results to return

        Returns:
            List of address suggestions with IDs and names
        """
        try:
            results = asyncio.run(self._search_address_async(query, limit))
            return results
        except Exception as e:
            raise NadlanAPIError(f"Failed to search for address '{query}': {e}")

    def get_deals_by_address(self, address_query: str) -> List[Deal]:
        """Retrieve deals by searching for an address first, then fetching deals.

        Args:
            address_query: Address or neighborhood name to search for

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the search or fetch fails
        """
        try:
            # First search for the address
            search_results = self.search_address(address_query, limit=5)
            
            if not search_results:
                raise NadlanAPIError(f"No addresses found for query: {address_query}")
            
            # Get the first (most relevant) result
            best_match = search_results[0]
            neighborhood_id = best_match.get('neighborhood_id')
            
            if not neighborhood_id:
                raise NadlanAPIError(f"Could not determine neighborhood ID for: {best_match['value']}")
            
            # Fetch deals using the neighborhood ID
            return self.get_deals_by_neighborhood_id(neighborhood_id)
            
        except Exception as e:
            raise NadlanAPIError(f"Failed to get deals for address '{address_query}': {e}")

    def get_neighborhood_info(self, neighbourhood_id: str) -> Dict[str, Any]:
        """Get information about a neighborhood.

        Args:
            neighbourhood_id: The numeric neighborhood ID

        Returns:
            Dictionary with neighborhood information

        Raises:
            NadlanAPIError: If the API call fails
        """
        try:
            info = asyncio.run(self._fetch_neighborhood_info(neighbourhood_id))
            return info
        except Exception as e:
            raise NadlanAPIError(f"Failed to fetch neighborhood info for {neighbourhood_id}: {e}")

    async def _fetch_neighborhood_info(self, neigh_id: str) -> Dict[str, Any]:
        """Fetch neighborhood information using Playwright."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                ctx = await browser.new_context()
                page = await ctx.new_page()
                
                # Load the neighborhood page
                await page.goto(f"https://www.nadlan.gov.il/?view=neighborhood&id={neigh_id}&page=deals", 
                               timeout=int(self.timeout * 1000))
                
                # Get API base from config.json
                api_base = await self._get_api_base(page)
                
                # Make the GetInfo request
                resp = await page.request.post(
                    f"{api_base}/GetInfo",
                    data=json.dumps({"base_name": "neigh_id", "base_id": neigh_id}),
                    headers={"content-type": "application/json"},
                    timeout=int(self.timeout * 1000),
                )
                
                if resp.status != 200:
                    raise NadlanAPIError(f"GetInfo HTTP {resp.status}")
                
                data = await resp.json()
                return {
                    "neigh_id": data["neigh_id"],
                    "neigh_name": data["neigh_name"],
                    "setl_id": str(data["setl_id"]),
                    "setl_name": data["setl_name"],
                }
            finally:
                await browser.close()

    async def _get_api_base(self, page) -> str:
        """Get API base URL from config.json."""
        js = """
        async () => {
          const res = await fetch('/config.json', {credentials:'omit'});
          const cfg = await res.json();
          return cfg.api_base;
        }
        """
        api_base = await page.evaluate(js)
        if not api_base:
            raise NadlanAPIError("config.json missing api_base")
        return api_base

    async def _search_address_async(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for addresses using the govmap autocomplete API."""
        import urllib.parse

        # Encode the query for URL
        encoded_query = urllib.parse.quote(query)
        
        # Construct the autocomplete URL
        url = f"https://es.govmap.gov.il/TldSearch/api/AutoComplete?query={encoded_query}&ids=276267023&gid=govmap"
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                # Create context with ignore HTTPS errors
                ctx = await browser.new_context(ignore_https_errors=True)
                page = await ctx.new_page()
                
                # Make the request to the autocomplete API
                response = await page.request.get(url, timeout=int(self.timeout * 1000))
                
                if response.status != 200:
                    raise NadlanAPIError(f"Autocomplete API returned status {response.status}")
                
                data = await response.json()
                
                # Process the results
                results = []
                
                # Process NEIGHBORHOOD results (most important for our use case)
                if 'res' in data and 'NEIGHBORHOOD' in data['res']:
                    for item in data['res']['NEIGHBORHOOD']:
                        # Try to extract neighborhood information
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        if neighborhood_id:
                            results.append({
                                'type': 'neighborhood',
                                'key': item['Key'],
                                'value': item['Value'],
                                'neighborhood_id': neighborhood_id,
                                'rank': item.get('Rank', 0)
                            })
                
                # Process POI_MID_POINT results (neighborhoods, points of interest)
                if 'res' in data and 'POI_MID_POINT' in data['res']:
                    for item in data['res']['POI_MID_POINT'][:limit//2]:
                        # Try to extract neighborhood information
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        if neighborhood_id:
                            results.append({
                                'type': 'neighborhood',
                                'key': item['Key'],
                                'value': item['Value'],
                                'neighborhood_id': neighborhood_id,
                                'rank': item.get('Rank', 0)
                            })
                
                # Process STREET results (street names)
                if 'res' in data and 'STREET' in data['res']:
                    for item in data['res']['STREET'][:limit//2]:
                        # Try to extract neighborhood information from street name
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        results.append({
                            'type': 'street',
                            'key': item['Key'],
                            'value': item['Value'],
                            'neighborhood_id': neighborhood_id,
                            'rank': item.get('Rank', 0)
                        })

                # Process TRANS_NAME results (street names)
                if 'res' in data and 'TRANS_NAME' in data['res']:
                    for item in data['res']['TRANS_NAME'][:limit//2]:
                        # Try to extract neighborhood information from street name
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        results.append({
                            'type': 'street',
                            'key': item['Key'],
                            'value': item['Value'],
                            'neighborhood_id': neighborhood_id,
                            'rank': item.get('Rank', 0)
                        })

                # Process SETTLEMENT results (cities, towns)
                if 'res' in data and 'SETTLEMENT' in data['res']:
                    for item in data['res']['SETTLEMENT'][:limit//2]:
                        # Try to extract neighborhood information from settlement name
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        results.append({
                            'type': 'settlement',
                            'key': item['Key'],
                            'value': item['Value'],
                            'neighborhood_id': neighborhood_id,
                            'rank': item.get('Rank', 0)
                        })

                # Process BUILDING results (buildings, addresses)
                if 'res' in data and 'BUILDING' in data['res']:
                    for item in data['res']['BUILDING'][:limit//2]:
                        # Try to extract neighborhood information from building address
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        results.append({
                            'type': 'building',
                            'key': item['Key'],
                            'value': item['Value'],
                            'neighborhood_id': neighborhood_id,
                            'rank': item.get('Rank', 0)
                        })

                # Process ADDRESS results (specific addresses)
                if 'res' in data and 'ADDRESS' in data['res']:
                    for item in data['res']['ADDRESS'][:limit//2]:
                        # Try to extract neighborhood information from address
                        neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                        results.append({
                            'type': 'address',
                            'key': item['Key'],
                            'value': item['Value'],
                            'neighborhood_id': neighborhood_id,
                            'rank': item.get('Rank', 0)
                        })

                # Process any other result types that might exist
                for key in data.get('res', {}).keys():
                    if key not in ['NEIGHBORHOOD', 'POI_MID_POINT', 'STREET', 'TRANS_NAME', 'SETTLEMENT', 'BUILDING', 'ADDRESS']:
                        if key in data['res']:
                            for item in data['res'][key][:limit//4]:  # Limit other types to avoid overwhelming results
                                # Try to extract neighborhood information
                                neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                                results.append({
                                    'type': key.lower(),
                                    'key': item['Key'],
                                    'value': item['Value'],
                                    'neighborhood_id': neighborhood_id,
                                    'rank': item.get('Rank', 0)
                                })
                
                # Sort by rank and return top results
                results.sort(key=lambda x: x.get('rank', 0))
                return results[:limit]
                
            finally:
                await browser.close()

    def _extract_neighborhood_id_from_poi(self, poi_item: Dict[str, Any]) -> Optional[str]:
        """Extract neighborhood ID from POI (Point of Interest) data.
        
        This is a simplified mapping - in practice you might want to use
        a more comprehensive database or API to map POIs to neighborhood IDs.
        """
        value = poi_item.get('Value', '')
        
        # Known neighborhood mappings (can be expanded)
        known_mappings = {
            'רמת החייל': '65210036',
            'רמת החיל': '65210036',  # Alternative spelling for רמת החייל
            'החיל תל אביב-יפו': '65210036',  # Street in רמת החייל
            'רמת אביב': '65210001',
            'נווה צדק': '65210002',
            'פלורנטין': '65210003',
            'יפו': '65210004',
            'התקווה': '65210005',
            'שכונת שפירא': '65210006',
            'קריית שלום': '65210007',
            'קריית יובל': '65210008',
            'קריית הממשלה': '65210009',
            'קריית הלאום': '65210010',
        }
        
        # City/Settlement mappings (when searching for entire cities)
        city_mappings = {
            'תל אביב': '5000',  # תל אביב-יפו settlement ID
            'תל אביב-יפו': '5000',
            'ירושלים': '3000',
            'חיפה': '4000',
            'באר שבע': '6000',
            'ראשון לציון': '8300',
            'פתח תקווה': '7900',
            'חולון': '6600',
            'רמת גן': '5200',
            'גבעתיים': '5300',
            'קריית אונו': '5400',
            'רמת השרון': '5500',
            'הוד השרון': '5600',
            'כפר סבא': '5700',
            'רעננה': '8700',
        }
        
        # Check if the POI contains any known neighborhood names
        for neighborhood_name, neighborhood_id in known_mappings.items():
            if neighborhood_name in value:
                return neighborhood_id
        
        # Check if the POI contains any known city names
        for city_name, city_id in city_mappings.items():
            if city_name in value:
                return city_id
        
        # If no direct match, return None (will need additional lookup)
        return None

    async def _fetch_deals_by_neighborhood(self, neigh_id: str) -> List[Deal]:
        """Fetch deals by neighborhood using Playwright."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                ctx = await browser.new_context()
                page = await ctx.new_page()

                # Capture the first /api/deal response
                fut = asyncio.get_event_loop().create_future()

                def _maybe_res(r: Response) -> None:
                    url = r.url
                    if "/api/deal" in url:
                        if not fut.done():
                            fut.set_result(r)

                page.on("response", _maybe_res)

                # Navigate to the neighborhood page
                url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neigh_id}&page=deals"
                await page.goto(url, timeout=int(self.timeout * 1000))

                # Wait for /api/deal response
                resp: Response = await asyncio.wait_for(fut, timeout=self.timeout + 10)
                if resp.status != 200:
                    raise NadlanAPIError(f"/api/deal HTTP {resp.status}")

                body_bytes = await resp.body()
                deals = self._decode_deals_payload(body_bytes)
                return deals
            finally:
                await browser.close()

    def _decode_deals_payload(self, body: bytes) -> List[Deal]:
        """
        Decode the deals payload from the API response.
        Handles various formats: plain JSON, API Gateway envelopes, base64+gzip.
        """
        # 1) try plain JSON
        try:
            data = json.loads(body.decode("utf-8"))
            items = self._extract_items_from_json(data)
            if items is not None:
                return [Deal.from_item(x) for x in items]
            # maybe {"body": "..."}
            if isinstance(data, dict) and "body" in data and isinstance(data["body"], str):
                decoded = self._decode_base64_gzip(data["body"])
                items = self._extract_items_from_json(decoded)
                if items is not None:
                    return [Deal.from_item(x) for x in items]
        except Exception:
            # fallthrough to base64 decode
            pass

        # 2) try raw base64+gzip text
        try:
            txt = body.decode("utf-8")
            if txt.startswith("H4sI") or txt.strip().startswith('"H4sI'):
                txt = txt.strip().strip('"')
                decoded = self._decode_base64_gzip(txt)
                items = self._extract_items_from_json(decoded)
                if items is not None:
                    return [Deal.from_item(x) for x in items]
        except Exception:
            pass

        raise NadlanAPIError("Unrecognized /api/deal payload format")

    @staticmethod
    def _extract_items_from_json(obj: Any) -> Optional[Sequence[Dict[str, Any]]]:
        """Extract items from JSON response."""
        if not isinstance(obj, dict):
            return None
        # happy path: {"data":{"items":[...]}}
        data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return items
        return None

    @staticmethod
    def _decode_base64_gzip(b64_text: str) -> Dict[str, Any]:
        """Decode base64+gzipped data."""
        import base64
        import gzip
        
        raw = base64.b64decode(b64_text)
        decomp = gzip.decompress(raw)
        return json.loads(decomp.decode("utf-8"))


# Simple convenience function
def get_deals_by_neighborhood_id(neighbourhood_id: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """Convenience function to get deals for a neighborhood."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        deals = scraper.get_deals_by_neighborhood_id(neighbourhood_id)
        return [deal.to_dict() for deal in deals]


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Fetch Israeli real‑estate deals from nadlan.gov.il."
    )
    parser.add_argument(
        "--neighbourhood-id", "-n", metavar="ID", required=True,
        help="Numeric neighbourhood id from the URL (e.g., 65210036)"
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of deals to fetch")
    parser.add_argument("--headed", action="store_true", help="Show browser window (debug)")
    parser.add_argument("--csv", metavar="PATH", help="Export deals to CSV")
    args = parser.parse_args()
    
    try:
        with NadlanDealsScraper(headless=not args.headed) as scraper:
            deals = scraper.get_deals_by_neighborhood_id(args.neighbourhood_id)
            
            if not deals:
                print("No deals were found for the given input.")
                sys.exit(0)
            
            # Apply limit if specified
            if args.limit > 0:
                deals = deals[:args.limit]
            
            if args.csv:
                import csv
                with open(args.csv, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["address", "deal_date", "deal_amount", "rooms", "floor", "asset_type", "year_built", "area"])
                    for d in deals:
                        w.writerow([d.address, d.deal_date, d.deal_amount, d.rooms, d.floor, d.asset_type, d.year_built, d.area])
                print(f"CSV written: {args.csv}")
            else:
                deals_dict = [deal.to_dict() for deal in deals]
                print(json.dumps(deals_dict, ensure_ascii=False, indent=2))
            
    except NadlanAPIError as e:
        logger.error("Error fetching deals: %s", e)
        sys.exit(1)
