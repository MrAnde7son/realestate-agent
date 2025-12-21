#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to recalculate PPM and price model for assets using existing data.

This script recalculates the price model without running the entire enrichment
pipeline. It uses existing listings and transactions from the database.

Usage:
    # Recalculate for a specific asset
    python db/recalculate_price_model.py --asset-id 165
    
    # Recalculate for all assets
    python db/recalculate_price_model.py --all
    
    # Recalculate for assets with outdated price_per_sqm (where price/area != price_per_sqm)
    python db/recalculate_price_model.py --fix-outdated
"""

import os
import sys
import argparse

# Setup Django environment - must be done before importing Django modules
# Change to project root directory to ensure proper module resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_django_path = os.path.join(project_root, 'backend-django')

# Add backend-django to Python path
if backend_django_path not in sys.path:
    sys.path.insert(0, backend_django_path)

# Change working directory to backend-django for proper Django setup
os.chdir(backend_django_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')

# Now setup Django
import django
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure your virtual environment is activated:")
    print("   source venv/bin/activate  # or: . venv/bin/activate")
    print("2. Install Django dependencies:")
    print("   cd backend-django")
    print("   pip install -r requirements.txt")
    print("3. Then run the script from project root:")
    print("   python db/recalculate_price_model.py --asset-id 165")
    print(f"\nCurrent Python: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    sys.exit(1)

from core.models import Asset
from orchestration.pipeline.asset_enrichment import recalculate_price_model


def _safe_numeric(value):
    """Helper to safely convert value to float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def recalculate_single_asset(asset_id: int, verbose: bool = False) -> bool:
    """Recalculate price model for a single asset."""
    try:
        if verbose:
            print(f"Recalculating price model for asset {asset_id}...")
        
        result = recalculate_price_model(asset_id)
        
        if result.get('success'):
            if verbose:
                metrics = result.get('metrics', {})
                print(f"✓ Asset {asset_id}: Success")
                print(f"  Model Price: {metrics.get('model_price', 'N/A')}")
                print(f"  Base PPM: {metrics.get('avg_price_per_sqm', 'N/A')}")
                print(f"  Adjusted PPM: {metrics.get('adjusted_price_per_sqm', 'N/A')}")
                print(f"  Price per sqm: {metrics.get('price_per_sqm', 'N/A')}")
                print(f"  Confidence: {metrics.get('confidence_pct', 'N/A')}%")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"✗ Asset {asset_id}: Failed - {error}")
            return False
            
    except Exception as e:
        print(f"✗ Asset {asset_id}: Error - {str(e)}")
        return False


def find_outdated_assets() -> list:
    """Find assets where price_per_sqm doesn't match price/total_area."""
    outdated = []
    
    assets = Asset.objects.filter(
        price__isnull=False,
        price__gt=0
    ).exclude(
        total_area__isnull=True
    ).exclude(
        total_area=0
    )
    
    for asset in assets:
        price = _safe_numeric(asset.price)
        total_area = _safe_numeric(asset.total_area) or _safe_numeric(asset.area)
        stored_ppm = _safe_numeric(asset.price_per_sqm)
        
        if price and total_area and total_area > 0:
            expected_ppm = int(price / total_area)
            
            # Consider outdated if difference is more than 1%
            if stored_ppm is None or abs(stored_ppm - expected_ppm) > (expected_ppm * 0.01):
                outdated.append({
                    'id': asset.id,
                    'address': asset.address or 'N/A',
                    'price': price,
                    'total_area': total_area,
                    'stored_ppm': stored_ppm,
                    'expected_ppm': expected_ppm,
                })
    
    return outdated


def main():
    parser = argparse.ArgumentParser(
        description='Recalculate PPM and price model for assets'
    )
    parser.add_argument(
        '--asset-id',
        type=int,
        help='Recalculate for a specific asset ID'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Recalculate for all assets'
    )
    parser.add_argument(
        '--fix-outdated',
        action='store_true',
        help='Recalculate only for assets with outdated price_per_sqm'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be recalculated without actually doing it'
    )
    
    args = parser.parse_args()
    
    if not any([args.asset_id, args.all, args.fix_outdated]):
        parser.print_help()
        sys.exit(1)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made\n")
    
    success_count = 0
    fail_count = 0
    
    if args.asset_id:
        # Recalculate single asset
        if args.dry_run:
            print(f"Would recalculate asset {args.asset_id}")
        else:
            if recalculate_single_asset(args.asset_id, args.verbose):
                success_count = 1
            else:
                fail_count = 1
    
    elif args.fix_outdated:
        # Find and fix outdated assets
        print("Finding assets with outdated price_per_sqm...")
        outdated = find_outdated_assets()
        
        if not outdated:
            print("No outdated assets found.")
            return
        
        print(f"Found {len(outdated)} assets with outdated price_per_sqm\n")
        
        if args.verbose:
            print("Outdated assets:")
            for asset_info in outdated[:10]:  # Show first 10
                print(f"  Asset {asset_info['id']}: {asset_info['address']}")
                print(f"    Price: {asset_info['price']:,}, Area: {asset_info['total_area']}")
                print(f"    Stored PPM: {asset_info['stored_ppm']}, Expected: {asset_info['expected_ppm']}")
            if len(outdated) > 10:
                print(f"  ... and {len(outdated) - 10} more\n")
        
        if args.dry_run:
            print(f"Would recalculate {len(outdated)} assets")
        else:
            for asset_info in outdated:
                if recalculate_single_asset(asset_info['id'], args.verbose):
                    success_count += 1
                else:
                    fail_count += 1
                
                # Show progress every 10 assets
                if (success_count + fail_count) % 10 == 0:
                    print(f"Progress: {success_count + fail_count}/{len(outdated)}")
    
    elif args.all:
        # Recalculate all assets
        assets = Asset.objects.all()
        total = assets.count()
        
        print(f"Recalculating price model for {total} assets...\n")
        
        if args.dry_run:
            print(f"Would recalculate {total} assets")
        else:
            for i, asset in enumerate(assets, 1):
                if args.verbose or i % 10 == 0:
                    print(f"Processing asset {asset.id} ({i}/{total})...")
                
                if recalculate_single_asset(asset.id, args.verbose):
                    success_count += 1
                else:
                    fail_count += 1
                
                # Show progress every 10 assets
                if i % 10 == 0:
                    print(f"Progress: {i}/{total} (Success: {success_count}, Failed: {fail_count})")
    
    # Summary
    if not args.dry_run:
        print(f"\n{'='*50}")
        print(f"Summary:")
        print(f"  Success: {success_count}")
        print(f"  Failed: {fail_count}")
        print(f"  Total: {success_count + fail_count}")
        print(f"{'='*50}")
    
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()

