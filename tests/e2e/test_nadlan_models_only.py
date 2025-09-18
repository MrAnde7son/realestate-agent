#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nadlan Models Only Tests

This test file tests only the Nadlan models without any external dependencies.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import only the models (no external dependencies)
from gov.nadlan.models import Deal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_deal_model_creation():
    """Test Deal model creation and validation."""
    logger.info("Testing Deal model creation...")
    
    # Test 1: Create Deal from dictionary
    deal_data = {
        'address': 'רוזוב 14, תל אביב-יפו',
        'dealDate': '2023-01-15',
        'dealAmount': 2500000,
        'rooms': '3',
        'floor': '2',
        'assetType': 'דירה',
        'yearBuilt': '2010',
        'area': 85.5,
        'parcelNum': '6638-68-5'
    }
    
    deal = Deal.from_item(deal_data)
    assert isinstance(deal, Deal), "Should create Deal object"
    assert deal.address == 'רוזוב 14, תל אביב-יפו', "Address should match"
    assert deal.deal_amount == 2500000, "Deal amount should match"
    assert deal.rooms == '3', "Rooms should match"
    assert deal.area == 85.5, "Area should match"
    assert deal.parcel_block == '6638', "Parcel block should be parsed"
    assert deal.parcel_parcel == '68', "Parcel number should be parsed"
    assert deal.parcel_sub_parcel == '5', "Sub-parcel should be parsed"
    
    logger.info("✅ Deal model creation test passed")


def test_deal_model_parsing():
    """Test Deal model data parsing functionality."""
    logger.info("Testing Deal model parsing...")
    
    # Test 1: Test number parsing
    assert Deal._num("₪2,500,000") == 2500000, "Should parse currency with commas"
    assert Deal._num("2,500,000") == 2500000, "Should parse numbers with commas"
    assert Deal._num("2500000") == 2500000, "Should parse plain numbers"
    assert Deal._num("85.5 מ²") == 85.5, "Should parse area with Hebrew symbol"
    assert Deal._num("") is None, "Should return None for empty string"
    assert Deal._num(None) is None, "Should return None for None"
    
    # Test 2: Test parcel number parsing
    block, parcel, sub_parcel = Deal._parse_parcel_num("6638-68-5")
    assert block == '6638', "Should parse block correctly"
    assert parcel == '68', "Should parse parcel correctly"
    assert sub_parcel == '5', "Should parse sub-parcel correctly"
    
    block, parcel, sub_parcel = Deal._parse_parcel_num("6638-68")
    assert block == '6638', "Should parse block with 2 parts"
    assert parcel == '68', "Should parse parcel with 2 parts"
    assert sub_parcel is None, "Should return None for missing sub-parcel"
    
    block, parcel, sub_parcel = Deal._parse_parcel_num("6638")
    assert block == '6638', "Should parse single part as block"
    assert parcel is None, "Should return None for missing parcel"
    assert sub_parcel is None, "Should return None for missing sub-parcel"
    
    logger.info("✅ Deal model parsing test passed")


def test_deal_model_conversion():
    """Test Deal model data conversion."""
    logger.info("Testing Deal model conversion...")
    
    deal_data = {
        'address': 'רוזוב 14, תל אביב-יפו',
        'dealDate': '2023-01-15',
        'dealAmount': 2500000,
        'rooms': '3',
        'floor': '2',
        'assetType': 'דירה',
        'yearBuilt': '2010',
        'area': 85.5,
        'parcelNum': '6638-68-5'
    }
    
    deal = Deal.from_item(deal_data)
    
    # Test to_dict conversion
    deal_dict = deal.to_dict()
    assert isinstance(deal_dict, dict), "Should return dictionary"
    assert deal_dict['address'] == 'רוזוב 14, תל אביב-יפו', "Address should be preserved"
    assert deal_dict['deal_amount'] == 2500000, "Deal amount should be preserved"
    assert deal_dict['parcel_block'] == '6638', "Parcel block should be preserved"
    
    logger.info("✅ Deal model conversion test passed")


def test_deal_model_edge_cases():
    """Test Deal model edge cases and error handling."""
    logger.info("Testing Deal model edge cases...")
    
    # Test 1: Empty data
    empty_deal = Deal.from_item({})
    assert empty_deal.address is None, "Should handle empty address"
    assert empty_deal.deal_amount is None, "Should handle empty deal_amount"
    assert empty_deal.rooms is None, "Should handle empty rooms"
    
    # Test 2: Invalid data types
    invalid_data = {
        'address': 123,  # Should be string
        'dealAmount': 'invalid',  # Should be number
        'rooms': None,
        'area': 'not_a_number'
    }
    
    invalid_deal = Deal.from_item(invalid_data)
    assert invalid_deal.address == 123, "Should preserve invalid address as-is"
    assert invalid_deal.deal_amount is None, "Should handle invalid deal_amount"
    assert invalid_deal.rooms is None, "Should handle None rooms"
    assert invalid_deal.area is None, "Should handle invalid area"
    
    # Test 3: Partial data
    partial_data = {
        'address': 'רוזוב 14, תל אביב-יפו',
        'dealAmount': 2500000
    }
    
    partial_deal = Deal.from_item(partial_data)
    assert partial_deal.address == 'רוזוב 14, תל אביב-יפו', "Should handle partial data"
    assert partial_deal.deal_amount == 2500000, "Should handle partial data"
    assert partial_deal.rooms is None, "Should handle missing rooms"
    
    logger.info("✅ Deal model edge cases test passed")


def test_transaction_data_validation():
    """Test transaction data validation logic."""
    logger.info("Testing transaction data validation...")
    
    # Test 1: Valid transaction data
    valid_transaction = {
        'address': 'רוזוב 14, תל אביב-יפו',
        'dealAmount': 2500000,
        'dealDate': '2023-01-15',
        'rooms': '3',
        'area': 85.5
    }
    
    deal = Deal.from_item(valid_transaction)
    deal_dict = deal.to_dict()
    
    # Validate structure
    assert 'address' in deal_dict, "Should have address field"
    assert 'deal_amount' in deal_dict, "Should have deal_amount field"
    assert 'deal_date' in deal_dict, "Should have deal_date field"
    assert 'rooms' in deal_dict, "Should have rooms field"
    assert 'area' in deal_dict, "Should have area field"
    
    # Validate data types
    assert isinstance(deal_dict['address'], str), "Address should be string"
    assert isinstance(deal_dict['deal_amount'], (int, float)), "Deal amount should be numeric"
    assert isinstance(deal_dict['deal_date'], str), "Deal date should be string"
    assert isinstance(deal_dict['rooms'], str), "Rooms should be string"
    assert isinstance(deal_dict['area'], (int, float)), "Area should be numeric"
    
    logger.info("✅ Transaction data validation test passed")


def test_price_analysis_simulation():
    """Test price analysis simulation with mock data."""
    logger.info("Testing price analysis simulation...")
    
    # Create mock transaction data
    mock_transactions = [
        Deal.from_item({
            'address': 'רוזוב 14, תל אביב-יפו',
            'dealAmount': 2500000,
            'dealDate': '2023-01-15',
            'rooms': '3',
            'area': 85.5
        }),
        Deal.from_item({
            'address': 'רוזוב 16, תל אביב-יפו',
            'dealAmount': 2800000,
            'dealDate': '2023-02-20',
            'rooms': '4',
            'area': 95.0
        }),
        Deal.from_item({
            'address': 'רוזוב 18, תל אביב-יפו',
            'dealAmount': 2200000,
            'dealDate': '2023-03-10',
            'rooms': '3',
            'area': 80.0
        })
    ]
    
    # Extract prices
    prices = [deal.deal_amount for deal in mock_transactions if deal.deal_amount]
    
    # Calculate statistics
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    # Validate calculations
    assert len(prices) == 3, "Should have 3 prices"
    assert avg_price == 2500000, f"Average should be 2500000, got {avg_price}"
    assert min_price == 2200000, f"Minimum should be 2200000, got {min_price}"
    assert max_price == 2800000, f"Maximum should be 2800000, got {max_price}"
    assert price_range == 600000, f"Range should be 600000, got {price_range}"
    
    logger.info(f"📊 Price analysis simulation:")
    logger.info(f"   Average: ₪{avg_price:,.0f}")
    logger.info(f"   Minimum: ₪{min_price:,.0f}")
    logger.info(f"   Maximum: ₪{max_price:,.0f}")
    logger.info(f"   Range: ₪{price_range:,.0f}")
    
    logger.info("✅ Price analysis simulation test passed")


def main():
    """Run all Nadlan models tests."""
    logger.info("=" * 60)
    logger.info("RUNNING NADLAN MODELS TESTS")
    logger.info("=" * 60)

    # Run all tests
    test_deal_model_creation()
    test_deal_model_parsing()
    test_deal_model_conversion()
    test_deal_model_edge_cases()
    test_transaction_data_validation()
    test_price_analysis_simulation()

    logger.info("🎉 All Nadlan models tests completed successfully!")


if __name__ == "__main__":
    main()
