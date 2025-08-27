"""Pytest configuration for Mavat tests."""

import pytest
import sys
import os

# Add the mavat package to the path for imports
mavat_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mavat')
if mavat_path not in sys.path:
    sys.path.insert(0, mavat_path)

# Configure pytest for async tests
pytest_plugins = ['pytest_asyncio']


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_playwright_available():
    """Mock Playwright as available for testing."""
    import mavat.scrapers.mavat_scraper as mavat_module
    
    # Store original value
    original_sync_playwright = mavat_module.sync_playwright
    
    # Mock as available
    mock_playwright = pytest.Mock()
    mavat_module.sync_playwright = mock_playwright
    
    yield mock_playwright
    
    # Restore original value
    mavat_module.sync_playwright = original_sync_playwright


@pytest.fixture
def mock_playwright_unavailable():
    """Mock Playwright as unavailable for testing."""
    import mavat.scrapers.mavat_scraper as mavat_module
    
    # Store original value
    original_sync_playwright = mavat_module.sync_playwright
    
    # Mock as unavailable
    mavat_module.sync_playwright = None
    
    yield
    
    # Restore original value
    mavat_module.sync_playwright = original_sync_playwright

