#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Nadlan.gov.il Integration Tests

This test file provides basic integration tests that don't require
Selenium browser automation, focusing on API and data structure validation.
"""

import logging
import os
import sys
from pathlib import Path
import pytest
import time
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import components
from gov.nadlan.models import Deal
from orchestration.collectors.gov_collector import GovCollector

# Test data
TEST_ADDRESS = "רוזוב 14 תל אביב"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestNadlanSimple:
    """Simple integration tests for Nadlan functionality."""

    def test_deal_model_creation(self):
        """Test Deal model creation and validation."""
        logger.info("Testing Deal model creation...")
        
        # Test 1: Create Deal from dictionary
        deal_data = {
            'address': 'רוזוב 14, תל אביב-יפו',
            'deal_date': '2023-01-15',
            'deal_amount': 2500000,
            'rooms': '3',
            'floor': '2',
            'asset_type': 'דירה',
            'year_built': '2010',
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

    def test_deal_model_parsing(self):
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

    def test_deal_model_conversion(self):
        """Test Deal model data conversion."""
        logger.info("Testing Deal model conversion...")
        
        deal_data = {
            'address': 'רוזוב 14, תל אביב-יפו',
            'deal_date': '2023-01-15',
            'deal_amount': 2500000,
            'rooms': '3',
            'floor': '2',
            'asset_type': 'דירה',
            'year_built': '2010',
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

    def test_gov_collector_initialization(self):
        """Test GovCollector initialization."""
        logger.info("Testing GovCollector initialization...")
        
        # Test 1: Default initialization
        collector = GovCollector()
        assert collector is not None, "Should create GovCollector instance"
        assert collector.deals_client is not None, "Should have deals client"
        assert collector.decisive_client is not None, "Should have decisive client"
        
        # Test 2: Parameter validation
        assert collector.validate_parameters(block="1234", parcel="56", address=TEST_ADDRESS) is True, "Should validate correct parameters"
        assert collector.validate_parameters(block="1234", parcel="56") is False, "Should reject missing address"
        assert collector.validate_parameters(block="1234") is False, "Should reject missing parcel and address"
        assert collector.validate_parameters() is False, "Should reject empty parameters"
        
        logger.info("✅ GovCollector initialization test passed")

    def test_gov_collector_data_structure(self):
        """Test GovCollector data structure methods."""
        logger.info("Testing GovCollector data structure...")
        
        collector = GovCollector()
        
        # Test 1: Test collect method structure
        result = collector.collect(block="1234", parcel="56", address=TEST_ADDRESS)
        assert isinstance(result, dict), "Should return dictionary"
        assert "decisive" in result, "Should have decisive key"
        assert "transactions" in result, "Should have transactions key"
        assert isinstance(result["decisive"], list), "Decisive should be list"
        assert isinstance(result["transactions"], list), "Transactions should be list"
        
        logger.info("✅ GovCollector data structure test passed")

    def test_deal_model_edge_cases(self):
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
            'deal_amount': 'invalid',  # Should be number
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
            'deal_amount': 2500000
        }
        
        partial_deal = Deal.from_item(partial_data)
        assert partial_deal.address == 'רוזוב 14, תל אביב-יפו', "Should handle partial data"
        assert partial_deal.deal_amount == 2500000, "Should handle partial data"
        assert partial_deal.rooms is None, "Should handle missing rooms"
        
        logger.info("✅ Deal model edge cases test passed")

    def test_transaction_data_validation(self):
        """Test transaction data validation logic."""
        logger.info("Testing transaction data validation...")
        
        # Test 1: Valid transaction data
        valid_transaction = {
            'address': 'רוזוב 14, תל אביב-יפו',
            'deal_amount': 2500000,
            'deal_date': '2023-01-15',
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


def main():
    """Run the simple Nadlan tests directly."""
    logger.info("=" * 60)
    logger.info("RUNNING SIMPLE NADLAN INTEGRATION TESTS")
    logger.info("=" * 60)

    test_instance = TestNadlanSimple()
    
    # Run all tests
    test_instance.test_deal_model_creation()
    test_instance.test_deal_model_parsing()
    test_instance.test_deal_model_conversion()
    test_instance.test_gov_collector_initialization()
    test_instance.test_gov_collector_data_structure()
    test_instance.test_deal_model_edge_cases()
    test_instance.test_transaction_data_validation()

    logger.info("🎉 All simple Nadlan tests completed successfully!")


if __name__ == "__main__":
    main()
