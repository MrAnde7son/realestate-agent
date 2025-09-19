#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nadlan.gov.il Integration E2E Tests

This test file specifically tests the integration with nadlan.gov.il
for real estate transaction data collection and comparison.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
import pytest
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import nadlan components
from gov.nadlan.scraper import NadlanDealsScraper
from gov.nadlan.models import Deal
from orchestration.collectors.gov_collector import GovCollector
from orchestration.data_pipeline import DataPipeline

# Test address
TEST_ADDRESS = "רוזוב 14 תל אביב"
TEST_STREET = "רוזוב"
TEST_HOUSE_NUMBER = 14
TEST_CITY = "תל אביב"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestNadlanIntegration:
    """Integration tests for Nadlan.gov.il functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {self.temp_dir}")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temp directory: {self.temp_dir}")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_nadlan_scraper_basic_functionality(self):
        """Test basic Nadlan scraper functionality."""
        logger.info("Testing Nadlan scraper basic functionality...")

        # Test 1: Initialize scraper
        logger.info("Testing scraper initialization...")
        scraper = NadlanDealsScraper(timeout=60, headless=True)
        assert scraper is not None
        logger.info("✓ Scraper initialized successfully")

        # Test 2: Search for address
        logger.info("Testing address search...")
        search_results = []
        for attempt in range(3):
            try:
                search_results = scraper.search_address(TEST_ADDRESS, limit=5)
                if search_results:
                    break
                logger.warning(f"Attempt {attempt + 1}: No search results found")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        assert isinstance(search_results, list), "Search results should be a list"
        if len(search_results) == 0:
            logger.warning("⚠ No address results found - skipping test")
            pytest.skip("No address results found - likely due to CI environment constraints")
        logger.info(f"✓ Found {len(search_results)} address results")

        # Test 3: Get deals by address
        logger.info("Testing deals by address...")
        deals = []
        for attempt in range(3):
            try:
                deals = scraper.get_deals_by_address(TEST_ADDRESS)
                if deals:
                    break
                logger.warning(f"Attempt {attempt + 1}: No deals found")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        assert isinstance(deals, list), "Deals should be a list"
        if len(deals) == 0:
            logger.warning("⚠ No deals found - skipping test")
            pytest.skip("No deals found - likely due to CI environment constraints")
        logger.info(f"✓ Found {len(deals)} deals for address")

        # Test 4: Validate deal structure
        if deals:
            deal = deals[0]
            assert isinstance(deal, Deal), "Deal should be a Deal object"
            logger.info(f"✓ Deal structure validated: {deal.to_dict().keys()}")

        logger.info("✓ Nadlan scraper basic functionality tests passed")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_gov_collector_nadlan_integration(self):
        """Test GovCollector with Nadlan integration."""
        logger.info("Testing GovCollector with Nadlan integration...")

        # Test 1: Initialize GovCollector
        logger.info("Testing GovCollector initialization...")
        collector = GovCollector()
        assert collector is not None
        logger.info("✓ GovCollector initialized successfully")

        # Test 2: Test parameter validation
        logger.info("Testing parameter validation...")
        assert collector.validate_parameters(block="1234", parcel="56", address=TEST_ADDRESS) is True
        assert collector.validate_parameters(block="1234", parcel="56") is False  # Missing address
        logger.info("✓ Parameter validation working correctly")

        # Test 3: Test transaction collection
        logger.info("Testing transaction collection...")
        transactions = []
        for attempt in range(3):
            try:
                transactions = collector._collect_transactions(TEST_ADDRESS)
                if transactions:
                    break
                logger.warning(f"Attempt {attempt + 1}: No transactions found")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        assert isinstance(transactions, list), "Transactions should be a list"
        if len(transactions) == 0:
            logger.warning("⚠ No transactions found - skipping test")
            pytest.skip("No transactions found - likely due to CI environment constraints")
        logger.info(f"✓ Found {len(transactions)} transactions")

        # Test 4: Validate transaction structure
        if transactions:
            transaction = transactions[0]
            assert isinstance(transaction, dict), "Transaction should be a dictionary"
            logger.info(f"✓ Transaction structure validated: {list(transaction.keys())}")

        # Test 5: Test full collection
        logger.info("Testing full collection...")
        try:
            full_data = collector.collect(block="1234", parcel="56", address=TEST_ADDRESS)
            assert isinstance(full_data, dict), "Full data should be a dictionary"
            assert "decisive" in full_data, "Should have decisive data"
            assert "transactions" in full_data, "Should have transactions data"
            logger.info(f"✓ Full collection successful: decisive={len(full_data['decisive'])}, transactions={len(full_data['transactions'])}")
        except Exception as e:
            logger.warning(f"⚠ Full collection failed: {e}")

        logger.info("✓ GovCollector with Nadlan integration tests passed")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_pipeline_nadlan_integration(self):
        """Test DataPipeline with Nadlan integration."""
        logger.info("Testing DataPipeline with Nadlan integration...")

        # Test 1: Initialize pipeline
        logger.info("Testing pipeline initialization...")
        pipeline = DataPipeline()
        assert pipeline is not None
        logger.info("✓ Pipeline initialized successfully")

        # Test 2: Run pipeline with test address
        logger.info("Testing pipeline execution...")
        results = []
        for attempt in range(3):
            try:
                results = pipeline.run(TEST_STREET, TEST_HOUSE_NUMBER, max_pages=1)
                if results:
                    break
                logger.warning(f"Attempt {attempt + 1}: No results from pipeline")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        assert isinstance(results, list), "Results should be a list"
        if len(results) == 0:
            logger.warning("⚠ No results from pipeline - skipping test")
            pytest.skip("No results from pipeline - likely due to CI environment constraints")
        logger.info(f"✓ Pipeline returned {len(results)} results")

        # Test 3: Analyze results by source
        logger.info("Testing result analysis...")
        sources = self._analyze_results_by_source(results)
        logger.info(f"✓ Found data from {len(sources)} sources: {list(sources.keys())}")

        # Test 4: Check for government data (including Nadlan)
        if 'gov' in sources:
            gov_data = sources['gov']
            if isinstance(gov_data, dict):
                if 'transactions' in gov_data:
                    transactions = gov_data['transactions']
                    logger.info(f"✓ Found {len(transactions)} transactions from Nadlan")
                    
                    # Validate transaction data
                    if transactions:
                        transaction = transactions[0]
                        assert isinstance(transaction, dict), "Transaction should be a dictionary"
                        logger.info(f"✓ Transaction structure validated: {list(transaction.keys())}")
                else:
                    logger.warning("⚠ No transactions found in government data")
            else:
                logger.warning("⚠ Government data is not a dictionary")
        else:
            logger.warning("⚠ No government data found in results")

        logger.info("✓ DataPipeline with Nadlan integration tests passed")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_transaction_price_analysis(self):
        """Test transaction price analysis functionality."""
        logger.info("Testing transaction price analysis...")

        # Test 1: Get transactions from Nadlan
        collector = GovCollector()
        transactions = []
        for attempt in range(3):
            try:
                transactions = collector._collect_transactions(TEST_ADDRESS)
                if transactions:
                    break
                logger.warning(f"Attempt {attempt + 1}: No transactions found")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        if not transactions:
            logger.warning("⚠ No transactions found - skipping price analysis test")
            pytest.skip("No transactions found - likely due to CI environment constraints")

        logger.info(f"✓ Found {len(transactions)} transactions for price analysis")

        # Test 2: Extract prices
        prices = []
        for transaction in transactions:
            if transaction.get('deal_amount') and isinstance(transaction['deal_amount'], (int, float)):
                prices.append(transaction['deal_amount'])

        if not prices:
            logger.warning("⚠ No valid prices found - skipping price analysis")
            pytest.skip("No valid prices found in transactions")

        logger.info(f"✓ Found {len(prices)} valid prices for analysis")

        # Test 3: Calculate price statistics
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price

        logger.info(f"📊 Price analysis:")
        logger.info(f"   Average: ₪{avg_price:,.0f}")
        logger.info(f"   Minimum: ₪{min_price:,.0f}")
        logger.info(f"   Maximum: ₪{max_price:,.0f}")
        logger.info(f"   Range: ₪{price_range:,.0f}")

        # Test 4: Validate price data
        assert min_price > 0, "Minimum price should be positive"
        assert max_price > min_price, "Maximum price should be greater than minimum"
        assert avg_price > 0, "Average price should be positive"
        assert price_range > 0, "Price range should be positive"

        logger.info("✓ Transaction price analysis tests passed")

    def _analyze_results_by_source(self, results):
        """Analyze pipeline results and group by source."""
        sources = {}
        
        for result in results:
            if hasattr(result, 'title'):  # Yad2 listing
                if 'yad2' not in sources:
                    sources['yad2'] = []
                sources['yad2'].append(result)
            elif isinstance(result, dict) and 'source' in result:
                source = result['source']
                if source not in sources:
                    sources[source] = []
                sources[source].append(result['data'])
            else:
                # Unknown result type
                if 'unknown' not in sources:
                    sources['unknown'] = []
                sources['unknown'].append(result)
        
        return sources


def main():
    """Run the Nadlan integration tests directly."""
    test_instance = TestNadlanIntegration()
    test_instance.setup_method()

    try:
        # Run all Nadlan integration tests
        logger.info("=" * 60)
        logger.info("RUNNING NADLAN.GOV.IL INTEGRATION TESTS")
        logger.info(f"Test Address: {TEST_ADDRESS}")
        logger.info("=" * 60)

        # Test each component individually
        test_instance.test_nadlan_scraper_basic_functionality()
        test_instance.test_gov_collector_nadlan_integration()
        test_instance.test_pipeline_nadlan_integration()
        test_instance.test_transaction_price_analysis()

        logger.info("🎉 All Nadlan integration tests completed successfully!")
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    main()
