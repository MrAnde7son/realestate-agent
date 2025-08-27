# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import logging
from typing import List

from .exceptions import NadlanError
from .models import Deal
from .scraper import NadlanDealsScraper


def write_csv(path: str, deals: List[Deal]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["address", "deal_date", "deal_amount", "rooms", "floor", "asset_type", "year_built", "area"])
        for d in deals:
            w.writerow([d.address, d.deal_date, d.deal_amount, d.rooms, d.floor, d.asset_type, d.year_built, d.area])

def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    ap = argparse.ArgumentParser(description="Fetch Israeli real‑estate deals from nadlan.gov.il")
    
    # Main command groups
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-q", "--query", help="Search for address/neighborhood (e.g., 'רמת החייל')")
    g.add_argument("-n", "--neigh-id", help="Neighborhood id (e.g., 65210036)")
    g.add_argument("-i", "--info", help="Get neighborhood info for ID")
    g.add_argument("-s", "--search", help="Search addresses using autocomplete API")
    
    # Options
    ap.add_argument("--limit", type=int, default=0, help="Limit rows")
    ap.add_argument("--csv", help="Write output CSV")
    ap.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    
    # Browser options
    ap.add_argument("--headed", action="store_true", help="Show browser window (debug)")
    
    args = ap.parse_args(argv)

    try:
        # Use browser-based scraper (recommended)
        scraper = NadlanDealsScraper(timeout=args.timeout, headless=not args.headed)
        
        if args.info:
            info = scraper.get_neighborhood_info(args.info)
            print(json.dumps(info, ensure_ascii=False, indent=2))
        elif args.search:
            # Search for addresses using autocomplete
            results = scraper.search_address(args.search, limit=args.limit if args.limit > 0 else 10)
            if not results:
                print("No addresses found for the given query.")
                return 0
            print(json.dumps(results, ensure_ascii=False, indent=2))
        elif args.neigh_id:
            deals = scraper.get_deals_by_neighborhood_id(args.neigh_id)
            if not deals:
                print("No deals were found for the given input.")
                return 0
            
            # Apply limit if specified
            if args.limit > 0:
                deals = deals[:args.limit]
            
            if args.csv:
                write_csv(args.csv, deals)
                print(f"Saved CSV: {args.csv}")
            else:
                deals_dict = [deal.to_dict() for deal in deals]
                print(json.dumps(deals_dict, ensure_ascii=False, indent=2))
        else:
            # Query mode - search for address then get deals
            deals = scraper.get_deals_by_address(args.query)
            if not deals:
                print("No deals were found for the given input.")
                return 0
            
            # Apply limit if specified
            if args.limit > 0:
                deals = deals[:args.limit]
            
            if args.csv:
                write_csv(args.csv, deals)
                print(f"Saved CSV: {args.csv}")
            else:
                deals_dict = [deal.to_dict() for deal in deals]
                print(json.dumps(deals_dict, ensure_ascii=False, indent=2))
        
        return 0
        
    except NadlanError as e:
        logging.error("Error: %s", e)
        return 2
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())