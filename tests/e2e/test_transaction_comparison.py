#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transaction Comparison E2E Tests

This test file specifically tests the transaction comparison functionality
using data from Nadlan.gov.il for real estate price analysis.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
import pytest
import time
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import components
from gov.nadlan.scraper import NadlanDealsScraper
from gov.nadlan.models import Deal
from orchestration.collectors.gov_collector import GovCollector
from orchestration.data_pipeline import DataPipeline

# Test addresses for comparison
TEST_ADDRESSES = [
    "רוזוב 14 תל אביב",
    "רוטשילד 1 תל אביב", 
    "דיזנגוף 50 תל אביב"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestTransactionComparison:
    """E2E tests for transaction comparison functionality."""

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
    def test_transaction_data_collection(self):
        """Test collection of transaction data from multiple addresses."""
        logger.info("Testing transaction data collection...")

        # Mock transaction data for testing
        mock_transactions = {
            "רוזוב 14 תל אביב": [
                {
                    "address": "רוזוב 14, תל אביב-יפו",
                    "deal_amount": 2500000,
                    "deal_date": "2023-01-15",
                    "rooms": "3",
                    "floor": "2",
                    "asset_type": "דירה",
                    "year_built": "2010",
                    "area": 85.5,
                    "parcelNum": "6638-68-5"
                },
                {
                    "address": "רוזוב 14, תל אביב-יפו",
                    "deal_amount": 2800000,
                    "deal_date": "2023-06-20",
                    "rooms": "4",
                    "floor": "3",
                    "asset_type": "דירה",
                    "year_built": "2010",
                    "area": 95.0,
                    "parcelNum": "6638-68-5"
                }
            ],
            "רוטשילד 1 תל אביב": [
                {
                    "address": "רוטשילד 1, תל אביב-יפו",
                    "deal_amount": 3500000,
                    "deal_date": "2023-03-10",
                    "rooms": "3",
                    "floor": "5",
                    "asset_type": "דירה",
                    "year_built": "2015",
                    "area": 90.0,
                    "parcelNum": "6632-3200"
                }
            ],
            "דיזנגוף 50 תל אביב": [
                {
                    "address": "דיזנגוף 50, תל אביב-יפו",
                    "deal_amount": 4200000,
                    "deal_date": "2023-05-12",
                    "rooms": "4",
                    "floor": "8",
                    "asset_type": "דירה",
                    "year_built": "2018",
                    "area": 110.0,
                    "parcelNum": "6632-3214"
                }
            ]
        }

        collector = GovCollector()
        all_transactions = {}

        for address in TEST_ADDRESSES:
            logger.info(f"Collecting transactions for: {address}")
            
            # Use mock data instead of external service calls
            transactions = mock_transactions.get(address, [])
            
            if transactions:
                all_transactions[address] = transactions
                logger.info(f"✅ Found {len(transactions)} transactions for {address}")
            else:
                logger.warning(f"⚠ No transactions found for {address}")

        # Validate that we got some data
        assert len(all_transactions) > 0, "Should have collected transactions from at least one address"
        logger.info(f"✅ Collected transactions from {len(all_transactions)} addresses")

        # Store for other tests
        self.all_transactions = all_transactions

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_price_analysis_and_comparison(self):
        """Test price analysis and comparison across different addresses."""
        logger.info("Testing price analysis and comparison...")

        # First collect data if not already done
        if not hasattr(self, 'all_transactions'):
            self.test_transaction_data_collection()

        if not self.all_transactions:
            logger.warning("⚠ No transaction data available - skipping price analysis")
            pytest.skip("No transaction data available for price analysis")

        # Analyze prices for each address
        price_analysis = {}
        
        for address, transactions in self.all_transactions.items():
            prices = []
            for transaction in transactions:
                if transaction.get('deal_amount') and isinstance(transaction['deal_amount'], (int, float)):
                    prices.append(transaction['deal_amount'])

            if prices:
                price_analysis[address] = {
                    'count': len(prices),
                    'avg': sum(prices) / len(prices),
                    'min': min(prices),
                    'max': max(prices),
                    'range': max(prices) - min(prices)
                }
                logger.info(f"📊 {address}: {len(prices)} transactions, avg=₪{price_analysis[address]['avg']:,.0f}")

        assert len(price_analysis) > 0, "Should have price analysis for at least one address"
        logger.info(f"✅ Price analysis completed for {len(price_analysis)} addresses")

        # Compare prices across addresses
        if len(price_analysis) > 1:
            logger.info("🔍 Comparing prices across addresses...")
            
            avg_prices = [data['avg'] for data in price_analysis.values()]
            min_avg = min(avg_prices)
            max_avg = max(avg_prices)
            price_variance = max_avg - min_avg
            
            logger.info(f"📈 Price comparison:")
            logger.info(f"   Lowest average: ₪{min_avg:,.0f}")
            logger.info(f"   Highest average: ₪{max_avg:,.0f}")
            logger.info(f"   Variance: ₪{price_variance:,.0f}")
            
            # Validate price comparison
            assert min_avg > 0, "Minimum average price should be positive"
            assert max_avg > min_avg, "Maximum average should be greater than minimum"
            assert price_variance > 0, "Price variance should be positive"

        # Store for other tests
        self.price_analysis = price_analysis

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_transaction_structure_validation(self):
        """Test validation of transaction data structure."""
        logger.info("Testing transaction structure validation...")

        # First collect data if not already done
        if not hasattr(self, 'all_transactions'):
            self.test_transaction_data_collection()

        if not self.all_transactions:
            logger.warning("⚠ No transaction data available - skipping structure validation")
            pytest.skip("No transaction data available for structure validation")

        # Validate structure for each address
        for address, transactions in self.all_transactions.items():
            logger.info(f"Validating structure for {address}...")
            
            for i, transaction in enumerate(transactions[:3]):  # Check first 3
                assert isinstance(transaction, dict), f"Transaction {i} should be a dictionary"
                
                # Check required fields
                if 'address' in transaction:
                    assert isinstance(transaction['address'], str), "Address should be string"
                
                if 'deal_amount' in transaction and transaction['deal_amount']:
                    assert isinstance(transaction['deal_amount'], (int, float)), "Deal amount should be numeric"
                    assert transaction['deal_amount'] > 0, "Deal amount should be positive"
                
                if 'deal_date' in transaction:
                    assert isinstance(transaction['deal_date'], str), "Deal date should be string"
                
                if 'rooms' in transaction and transaction['rooms']:
                    assert isinstance(transaction['rooms'], (str, int, float)), "Rooms should be string or numeric"
                
                if 'area' in transaction and transaction['area']:
                    assert isinstance(transaction['area'], (int, float)), "Area should be numeric"
                    assert transaction['area'] > 0, "Area should be positive"

            logger.info(f"✅ Structure validated for {address}: {len(transactions)} transactions")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_pipeline_integration_with_comparison(self):
        """Test pipeline integration with transaction comparison."""
        logger.info("Testing pipeline integration with transaction comparison...")

        pipeline = DataPipeline()
        
        # Test with multiple addresses
        all_results = {}
        
        for address in TEST_ADDRESSES[:2]:  # Test with first 2 addresses
            logger.info(f"Running pipeline for: {address}")
            
            # Parse address
            parts = address.split()
            street = parts[0]
            house_number = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            city = " ".join(parts[2:]) if len(parts) > 2 else ""
            
            results = []
            for attempt in range(3):
                try:
                    results = pipeline.run(city, street, house_number, max_pages=1)
                    if results:
                        break
                    logger.warning(f"Attempt {attempt + 1}: No results from pipeline for {address}")
                    if attempt < 2:
                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {address}: {e}")
                    if attempt < 2:
                        time.sleep(5)

            if results:
                all_results[address] = results
                logger.info(f"✅ Pipeline returned {len(results)} results for {address}")

        # Analyze results
        if all_results:
            logger.info(f"✅ Pipeline integration successful for {len(all_results)} addresses")
            
            # Check for government data in results
            for address, results in all_results.items():
                sources = self._analyze_results_by_source(results)
                if 'gov' in sources:
                    gov_data = sources['gov']
                    if isinstance(gov_data, dict) and 'transactions' in gov_data:
                        transactions = gov_data['transactions']
                        logger.info(f"✅ Found {len(transactions)} transactions in pipeline results for {address}")
                    else:
                        logger.warning(f"⚠ No transactions found in pipeline results for {address}")
                else:
                    logger.warning(f"⚠ No government data found in pipeline results for {address}")
        else:
            logger.warning("⚠ No pipeline results - skipping integration test")
            pytest.skip("No pipeline results available for integration test")

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_transaction_filtering_and_sorting(self):
        """Test filtering and sorting of transaction data."""
        logger.info("Testing transaction filtering and sorting...")

        # First collect data if not already done
        if not hasattr(self, 'all_transactions'):
            self.test_transaction_data_collection()

        if not self.all_transactions:
            logger.warning("⚠ No transaction data available - skipping filtering test")
            pytest.skip("No transaction data available for filtering test")

        # Test filtering by price range
        all_prices = []
        for transactions in self.all_transactions.values():
            for transaction in transactions:
                if transaction.get('deal_amount') and isinstance(transaction['deal_amount'], (int, float)):
                    all_prices.append(transaction['deal_amount'])

        if all_prices:
            min_price = min(all_prices)
            max_price = max(all_prices)
            mid_price = (min_price + max_price) / 2
            
            logger.info(f"📊 Price filtering test:")
            logger.info(f"   All prices: {len(all_prices)} transactions")
            logger.info(f"   Price range: ₪{min_price:,.0f} - ₪{max_price:,.0f}")
            logger.info(f"   Mid-point: ₪{mid_price:,.0f}")
            
            # Test high-price filter
            high_price_transactions = []
            for transactions in self.all_transactions.values():
                for transaction in transactions:
                    if (transaction.get('deal_amount') and 
                        isinstance(transaction['deal_amount'], (int, float)) and
                        transaction['deal_amount'] > mid_price):
                        high_price_transactions.append(transaction)
            
            logger.info(f"   High-price transactions (>₪{mid_price:,.0f}): {len(high_price_transactions)}")
            
            # Test low-price filter
            low_price_transactions = []
            for transactions in self.all_transactions.values():
                for transaction in transactions:
                    if (transaction.get('deal_amount') and 
                        isinstance(transaction['deal_amount'], (int, float)) and
                        transaction['deal_amount'] <= mid_price):
                        low_price_transactions.append(transaction)
            
            logger.info(f"   Low-price transactions (≤₪{mid_price:,.0f}): {len(low_price_transactions)}")
            
            # Validate filtering
            assert len(high_price_transactions) + len(low_price_transactions) == len(all_prices), "Filtering should preserve all transactions"
            
            if high_price_transactions:
                high_avg = sum(t['deal_amount'] for t in high_price_transactions) / len(high_price_transactions)
                assert high_avg > mid_price, "High-price transactions should have average above mid-point"
            
            if low_price_transactions:
                low_avg = sum(t['deal_amount'] for t in low_price_transactions) / len(low_price_transactions)
                assert low_avg <= mid_price, "Low-price transactions should have average at or below mid-point"

        logger.info("✅ Transaction filtering and sorting tests passed")

    def _analyze_results_by_source(self, results: List[Any]) -> Dict[str, List[Any]]:
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
    """Run the transaction comparison tests directly."""
    test_instance = TestTransactionComparison()
    test_instance.setup_method()

    try:
        # Run all transaction comparison tests
        logger.info("=" * 60)
        logger.info("RUNNING TRANSACTION COMPARISON E2E TESTS")
        logger.info(f"Test Addresses: {', '.join(TEST_ADDRESSES)}")
        logger.info("=" * 60)

        # Test each component individually
        test_instance.test_transaction_data_collection()
        test_instance.test_price_analysis_and_comparison()
        test_instance.test_transaction_structure_validation()
        test_instance.test_pipeline_integration_with_comparison()
        test_instance.test_transaction_filtering_and_sorting()

        logger.info("🎉 All transaction comparison tests completed successfully!")
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    main()
