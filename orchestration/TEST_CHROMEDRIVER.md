# ChromeDriver Testing Guide

This guide explains how to verify that ChromeDriver is properly installed and working in the Celery worker.

## Quick Test Methods

### 1. Local Docker Build Test

Build the Docker image locally to verify the Dockerfile changes work:

```bash
# From the project root
cd orchestration

# Build the celery-worker image
docker build -f Dockerfile.celery --target celery-worker -t celery-worker-test .

# Check build logs for ChromeDriver installation
# Look for: "ChromeDriver installed successfully at /usr/local/bin/chromedriver"
```

### 2. Test ChromeDriver in Container

Run the container and test ChromeDriver directly:

```bash
# Run the container interactively
docker run -it --rm celery-worker-test /bin/bash

# Inside the container, test ChromeDriver
chromedriver --version
which chromedriver

# Test Chrome
google-chrome-stable --version

# Test Selenium (if Python is available)
python -c "from selenium import webdriver; from selenium.webdriver.chrome.service import Service; print('Selenium OK')"
```

### 3. Run Automated Test Script

Use the provided test script:

```bash
# Option A: Run in local Docker container
docker run -it --rm celery-worker-test python /app/orchestration/test_chromedriver.py

# Option B: Run locally (if you have Chrome/ChromeDriver installed)
python orchestration/test_chromedriver.py
```

### 4. Test Nadlan Scraper Directly

Test the actual scraper that was failing:

```bash
# In Docker container
docker run -it --rm celery-worker-test python -c "
from gov.nadlan.scraper_selenium import NadlanDealsScraper
scraper = NadlanDealsScraper(headless=True)
scraper._init_driver()
print('✓ Driver initialized successfully')
scraper._cleanup_driver()
"
```

## Render Deployment Verification

### 1. Build Logs Check

After deploying to Render, check the build logs for:

- ✅ `ChromeDriver version: X.X.X.X`
- ✅ `ChromeDriver installed successfully at /usr/local/bin/chromedriver`
- ✅ `ChromeDriver is not executable` should NOT appear

### 2. Runtime Logs Check

After deployment, check the Celery worker logs for:

- ✅ No errors about "Failed to create Chrome WebDriver session"
- ✅ Look for debug messages like: `Using ChromeDriver from CHROMEDRIVER_PATH: /usr/local/bin/chromedriver`
- ✅ Successful asset creation without ChromeDriver errors

### 3. Test Asset Creation

Create a new asset and monitor logs:

```bash
# Watch Render logs in real-time
# Look for successful Nadlan transaction fetch
```

Expected success log:
```
INFO: Nadlan transaction fetch successful for address [address]
```

Expected failure (if still broken):
```
ERROR: Failed to create Chrome WebDriver session...
```

### 4. Manual Test via Celery Task

You can trigger a test task directly:

```python
# In Django shell or via API
from gov.nadlan.scraper_selenium import NadlanDealsScraper

scraper = NadlanDealsScraper(headless=True)
try:
    deals = scraper.get_deals_by_address("באכר 10 תל אביב - יפו")
    print(f"✓ Successfully fetched {len(deals)} deals")
except Exception as e:
    print(f"✗ Failed: {e}")
```

## Troubleshooting

### If ChromeDriver is not found:

1. **Check environment variable:**
   ```bash
   echo $CHROMEDRIVER_PATH
   # Should output: /usr/local/bin/chromedriver
   ```

2. **Check file exists:**
   ```bash
   ls -la /usr/local/bin/chromedriver
   # Should show executable file
   ```

3. **Check permissions:**
   ```bash
   ls -la /usr/local/bin/chromedriver
   # Should show: -rwxr-xr-x (executable)
   ```

### If version mismatch:

1. **Check Chrome version:**
   ```bash
   google-chrome-stable --version
   ```

2. **Check ChromeDriver version:**
   ```bash
   chromedriver --version
   ```

3. **Versions should match major version number** (e.g., Chrome 131.x.x.x should work with ChromeDriver 131.x.x.x)

### If Selenium Manager is still being used:

Check logs for:
- `Using ChromeDriver from CHROMEDRIVER_PATH` or `Using ChromeDriver from common location`
- If you see `Using Selenium Manager to find ChromeDriver`, the explicit path wasn't found

## Expected Test Results

When everything works correctly, you should see:

```
[Test 1] ChromeDriver Installation
✓ ChromeDriver found at: /usr/local/bin/chromedriver
✓ ChromeDriver is executable
✓ ChromeDriver version: ChromeDriver 131.0.6778.85

[Test 2] Chrome Installation
✓ Chrome found at: /usr/bin/google-chrome-stable
✓ Chrome version: Google Chrome 131.0.6778.85

[Test 3] Selenium Import
✓ Selenium imported successfully

[Test 4] Selenium Chrome WebDriver Connection
✓ Chrome WebDriver created successfully
✓ Successfully loaded page, title: Google
✓ WebDriver closed successfully

[Test 5] Nadlan Scraper Initialization
✓ Nadlan scraper initialized successfully
✓ Driver initialized successfully
```

## Quick Verification Checklist

- [ ] Docker build completes without errors
- [ ] ChromeDriver is installed at `/usr/local/bin/chromedriver`
- [ ] ChromeDriver is executable
- [ ] ChromeDriver version matches Chrome major version
- [ ] Test script passes all tests
- [ ] Nadlan scraper can initialize driver
- [ ] Render deployment succeeds
- [ ] Asset creation works without ChromeDriver errors

