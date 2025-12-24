#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure Internet Fetcher for Agent

Provides sandboxed, scoped Internet access with strict guardrails:
- Domain whitelist only
- GET requests only
- HTML to text conversion (no JS execution)
- Size limits
- Rate limiting
- Injection filters
- Caching with ETag support
"""

import re
import hashlib
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Allowed domains whitelist
# NOTE: Sites with dedicated MCP servers (yad2, mavat, govmap, nadlan, madlan) are NOT included here.
# Use the MCP servers instead - they provide better parsing, structured data, and error handling.
# This fetcher is for sites WITHOUT MCP servers or one-off lookups.
ALLOWED_DOMAINS = {
    # Bank of Israel - interest rates, mortgage data
    "boi.org.il",
    # Internal application domains
    "nadlaner.com",
    "api.nadlaner.com",
}

# Allowed domain patterns (for wildcard matching)
# All .gov.il subdomains are allowed (Israeli government sites)
ALLOWED_DOMAIN_PATTERNS = [
    ".gov.il",  # Matches any subdomain of gov.il (e.g., data.gov.il, mavat.iplan.gov.il, etc.)
]

# Size limits
MAX_RESPONSE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_TEXT_LENGTH = 50000  # Truncate to top 50k characters

# Rate limiting: 5 requests per minute per session
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW = 60  # seconds

# Cache TTL: 1 hour
CACHE_TTL = 3600


class RateLimiter:
    """Rate limiter for Internet requests."""

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times = deque()
        self._lock = False  # Simple lock flag

    def acquire(self) -> bool:
        """Try to acquire permission for a request. Returns True if allowed."""
        now = time.time()

        # Remove old requests outside the window
        while self.request_times and self.request_times[0] < now - self.window_seconds:
            self.request_times.popleft()

        # Check if we're at the limit
        if len(self.request_times) >= self.max_requests:
            return False

        # Add current request
        self.request_times.append(now)
        return True

    def get_wait_time(self) -> float:
        """Get seconds to wait before next request is allowed."""
        if not self.request_times:
            return 0.0

        now = time.time()
        oldest = self.request_times[0]
        wait = self.window_seconds - (now - oldest)
        return max(0.0, wait)


class InternetFetcher:
    """Secure Internet fetcher with guardrails."""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; RealEstateAgent/1.0; +https://nadlaner.com)",
            }
        )

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is in whitelist or matches allowed patterns."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check exact match in whitelist
            if domain in ALLOWED_DOMAINS:
                return True

            # Check domain patterns (e.g., .gov.il for all government sites)
            for pattern in ALLOWED_DOMAIN_PATTERNS:
                if domain.endswith(pattern) or domain == pattern.lstrip("."):
                    return True

            # Also check without www. prefix
            domain_no_www = domain[4:] if domain.startswith("www.") else domain
            if domain_no_www in ALLOWED_DOMAINS:
                return True

            for pattern in ALLOWED_DOMAIN_PATTERNS:
                if domain_no_www.endswith(pattern) or domain_no_www == pattern.lstrip(
                    "."
                ):
                    return True

            return False
        except Exception as e:
            logger.warning("Error parsing URL %s: %s", url, e)
            return False

    def _filter_injection_attempts(self, html: str) -> str:
        """Remove potential injection vectors from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script tags
        for script in soup.find_all("script"):
            script.decompose()

        # Remove meta refresh tags
        for meta in soup.find_all(
            "meta", attrs={"http-equiv": re.compile(r"refresh", re.I)}
        ):
            meta.decompose()

        # Remove data: URLs from links and images
        for tag in soup.find_all(["a", "img", "iframe", "embed", "object"]):
            for attr in ["href", "src", "data-src"]:
                if tag.get(attr) and tag[attr].startswith("data:"):
                    tag[attr] = "#"

        # Remove on* event handlers
        for tag in soup.find_all(True):
            attrs_to_remove = []
            for attr in tag.attrs:
                if attr.startswith("on") and len(attr) > 2:
                    attrs_to_remove.append(attr)
            for attr in attrs_to_remove:
                del tag[attr]

        return str(soup)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text using BeautifulSoup."""
        try:
            # Filter injection attempts first
            filtered_html = self._filter_injection_attempts(html)
            soup = BeautifulSoup(filtered_html, "html.parser")

            # Remove style and script tags (should already be removed, but double-check)
            for tag in soup(["script", "style", "meta", "link"]):
                tag.decompose()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text)
            text = text.strip()

            # Truncate if too long
            if len(text) > MAX_TEXT_LENGTH:
                text = text[:MAX_TEXT_LENGTH] + "... [truncated]"

            return text
        except Exception as e:
            logger.error("Error converting HTML to text: %s", e)
            return "[Error: Could not extract text content]"

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_cache(
        self, url: str, etag: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Check cache for URL. Returns cached data if valid, None otherwise."""
        cache_key = self._get_cache_key(url)
        cached = self.cache.get(cache_key)

        if not cached:
            return None

        # Check TTL
        if time.time() - cached["timestamp"] > CACHE_TTL:
            del self.cache[cache_key]
            return None

        # If ETag provided, check if content changed
        if etag and cached.get("etag") != etag:
            return None

        return cached

    def _store_cache(self, url: str, content: str, etag: Optional[str] = None):
        """Store content in cache."""
        cache_key = self._get_cache_key(url)
        self.cache[cache_key] = {
            "content": content,
            "etag": etag,
            "timestamp": time.time(),
            "url": url,
        }

        # Clean old cache entries (simple cleanup)
        if len(self.cache) > 1000:
            # Remove oldest 100 entries
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1]["timestamp"])
            for key, _ in sorted_items[:100]:
                del self.cache[key]

    def fetch(self, url: str, scope: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch URL with all guardrails.

        Args:
            url: URL to fetch
            scope: Optional scope description (for logging)

        Returns:
            Dict with 'success', 'content', 'url', 'error' keys
        """
        # Check rate limit
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.get_wait_time()
            return {
                "success": False,
                "error": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.",
                "url": url,
            }

        # Validate URL
        if not url.startswith(("http://", "https://")):
            return {
                "success": False,
                "error": "URL must start with http:// or https://",
                "url": url,
            }

        # Check domain whitelist
        if not self._is_allowed_domain(url):
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            allowed_list = sorted(ALLOWED_DOMAINS) + [
                f"*.{pattern.lstrip('.')}" for pattern in ALLOWED_DOMAIN_PATTERNS
            ]
            return {
                "success": False,
                "error": f"Domain {domain} is not in allowed whitelist. Allowed domains: {', '.join(allowed_list)}",
                "url": url,
            }

        # Check cache
        cached = self._check_cache(url)
        if cached:
            logger.info("Cache hit for URL: %s", url)
            return {
                "success": True,
                "content": cached["content"],
                "url": url,
                "cached": True,
            }

        try:
            # Fetch with GET only
            logger.info("Fetching URL: %s (scope: %s)", url, scope)
            response = self.session.get(
                url, timeout=30, allow_redirects=True, stream=True
            )

            # Check final URL after redirects (must still be allowed)
            final_url = response.url
            if not self._is_allowed_domain(final_url):
                parsed = urlparse(final_url)
                domain = parsed.netloc.lower()
                return {
                    "success": False,
                    "error": f"Redirected to non-allowed domain: {domain}",
                    "url": final_url,
                }

            # Check status code
            response.raise_for_status()

            # Check content size
            content_length = response.headers.get("Content-Length")
            if content_length:
                size = int(content_length)
                if size > MAX_RESPONSE_SIZE:
                    return {
                        "success": False,
                        "error": f"Response too large: {size} bytes (max: {MAX_RESPONSE_SIZE} bytes)",
                        "url": final_url,
                    }

            # Read content with size limit
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_RESPONSE_SIZE:
                    return {
                        "success": False,
                        "error": f"Response exceeds size limit: {MAX_RESPONSE_SIZE} bytes",
                        "url": final_url,
                    }

            # Get ETag for caching
            etag = response.headers.get("ETag")

            # Convert HTML to text
            html_content = content.decode("utf-8", errors="ignore")
            text_content = self._html_to_text(html_content)

            # Store in cache
            self._store_cache(final_url, text_content, etag)

            return {
                "success": True,
                "content": text_content,
                "url": final_url,
                "cached": False,
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out",
                "url": url,
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "url": url,
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "url": url,
            }
        except Exception as e:
            logger.exception("Unexpected error fetching URL %s: %s", url, e)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "url": url,
            }


# Global fetcher instance
_fetcher = None


def get_fetcher() -> InternetFetcher:
    """Get or create global fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = InternetFetcher()
    return _fetcher


def reset_fetcher():
    """Reset global fetcher (useful for testing)."""
    global _fetcher
    _fetcher = None
