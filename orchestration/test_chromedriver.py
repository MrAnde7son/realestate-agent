#!/usr/bin/env python3
"""Test script to verify ChromeDriver installation and Selenium functionality."""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend-django"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chromedriver_installation():
    """Test if ChromeDriver is installed and accessible."""
    logger.info("Testing ChromeDriver installation...")
    
    # Check environment variable
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    if chromedriver_path:
        logger.info(f"CHROMEDRIVER_PATH is set to: {chromedriver_path}")
        if os.path.isfile(chromedriver_path):
            logger.info(f"✓ ChromeDriver found at {chromedriver_path}")
            if os.access(chromedriver_path, os.X_OK):
                logger.info(f"✓ ChromeDriver is executable")
            else:
                logger.error(f"✗ ChromeDriver is not executable")
                return False
        else:
            logger.error(f"✗ ChromeDriver not found at {chromedriver_path}")
            return False
    else:
        logger.info("CHROMEDRIVER_PATH not set, checking common locations...")
    
    # Check common locations
    common_paths = [
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/opt/chromedriver/chromedriver',
    ]
    
    found = False
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            logger.info(f"✓ ChromeDriver found at: {path}")
            found = True
            break
    
    if not found:
        logger.warning("ChromeDriver not found in common locations")
        # Try to find it in PATH
        import shutil
        chromedriver_in_path = shutil.which('chromedriver')
        if chromedriver_in_path:
            logger.info(f"✓ ChromeDriver found in PATH: {chromedriver_in_path}")
            found = True
    
    if not found:
        logger.error("✗ ChromeDriver not found anywhere")
        return False
    
    # Try to get version
    try:
        import subprocess
        result = subprocess.run(
            ['chromedriver', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"✓ ChromeDriver version: {result.stdout.strip()}")
        else:
            logger.warning(f"ChromeDriver version check failed: {result.stderr}")
    except Exception as e:
        logger.warning(f"Could not get ChromeDriver version: {e}")
    
    return True


def test_chrome_installation():
    """Test if Chrome is installed and accessible."""
    logger.info("Testing Chrome installation...")
    
    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin:
        logger.info(f"CHROME_BIN is set to: {chrome_bin}")
        if os.path.isfile(chrome_bin):
            logger.info(f"✓ Chrome found at {chrome_bin}")
        else:
            logger.error(f"✗ Chrome not found at {chrome_bin}")
            return False
    else:
        logger.info("CHROME_BIN not set, checking common locations...")
    
    # Check common locations
    common_paths = [
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
    ]
    
    found = False
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            logger.info(f"✓ Chrome found at: {path}")
            found = True
            break
    
    if not found:
        logger.error("✗ Chrome not found in common locations")
        return False
    
    # Try to get version
    try:
        import subprocess
        result = subprocess.run(
            [chrome_bin or 'google-chrome-stable', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"✓ Chrome version: {result.stdout.strip()}")
        else:
            logger.warning(f"Chrome version check failed: {result.stderr}")
    except Exception as e:
        logger.warning(f"Could not get Chrome version: {e}")
    
    return True


def test_selenium_import():
    """Test if Selenium can be imported."""
    logger.info("Testing Selenium import...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        logger.info("✓ Selenium imported successfully")
        logger.info(f"  Selenium version: {webdriver.__version__ if hasattr(webdriver, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import Selenium: {e}")
        return False


def test_selenium_chrome_connection():
    """Test if Selenium can create a Chrome WebDriver session."""
    logger.info("Testing Selenium Chrome WebDriver connection...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        import os
        
        # Find ChromeDriver
        chromedriver_path = None
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        if chromedriver_path and os.path.isfile(chromedriver_path) and os.access(chromedriver_path, os.X_OK):
            logger.info(f"Using ChromeDriver from CHROMEDRIVER_PATH: {chromedriver_path}")
        else:
            common_chromedriver_paths = [
                '/usr/local/bin/chromedriver',
                '/usr/bin/chromedriver',
                '/opt/chromedriver/chromedriver',
            ]
            for path in common_chromedriver_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    logger.info(f"Using ChromeDriver from common location: {chromedriver_path}")
                    break
        
        # Find Chrome binary
        chrome_binary = os.environ.get('CHROME_BIN')
        if not chrome_binary or not os.path.isfile(chrome_binary):
            common_chrome_paths = [
                '/usr/bin/google-chrome-stable',
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
            ]
            for path in common_chrome_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    chrome_binary = path
                    break
        
        # Configure Chrome options
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--window-size=1280,720')
        
        if chrome_binary:
            opts.binary_location = chrome_binary
            logger.info(f"Using Chrome binary at: {chrome_binary}")
        
        # Create service
        if chromedriver_path:
            service = Service(executable_path=chromedriver_path)
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
        else:
            service = Service()
            logger.info("Using Selenium Manager to find ChromeDriver")
        
        # Try to create driver
        logger.info("Attempting to create Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=opts)
        logger.info("✓ Chrome WebDriver created successfully")
        
        # Test basic functionality
        logger.info("Testing basic WebDriver functionality...")
        driver.get("https://www.google.com")
        title = driver.title
        logger.info(f"✓ Successfully loaded page, title: {title}")
        
        # Cleanup
        driver.quit()
        logger.info("✓ WebDriver closed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create Chrome WebDriver session: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_nadlan_scraper():
    """Test the Nadlan scraper initialization."""
    logger.info("Testing Nadlan scraper initialization...")
    
    try:
        from gov.nadlan.scraper_selenium import NadlanDealsScraper
        
        scraper = NadlanDealsScraper(headless=True)
        logger.info("✓ Nadlan scraper initialized successfully")
        
        # Try to initialize driver (this will test ChromeDriver connection)
        logger.info("Testing driver initialization...")
        scraper._init_driver()
        logger.info("✓ Driver initialized successfully")
        
        # Cleanup
        scraper._cleanup_driver()
        logger.info("✓ Driver cleaned up successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Nadlan scraper test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("ChromeDriver Installation Test Suite")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: ChromeDriver installation
    logger.info("\n[Test 1] ChromeDriver Installation")
    logger.info("-" * 60)
    results.append(("ChromeDriver Installation", test_chromedriver_installation()))
    
    # Test 2: Chrome installation
    logger.info("\n[Test 2] Chrome Installation")
    logger.info("-" * 60)
    results.append(("Chrome Installation", test_chrome_installation()))
    
    # Test 3: Selenium import
    logger.info("\n[Test 3] Selenium Import")
    logger.info("-" * 60)
    results.append(("Selenium Import", test_selenium_import()))
    
    # Test 4: Selenium Chrome connection
    logger.info("\n[Test 4] Selenium Chrome WebDriver Connection")
    logger.info("-" * 60)
    results.append(("Selenium Chrome Connection", test_selenium_chrome_connection()))
    
    # Test 5: Nadlan scraper
    logger.info("\n[Test 5] Nadlan Scraper Initialization")
    logger.info("-" * 60)
    results.append(("Nadlan Scraper", test_nadlan_scraper()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

