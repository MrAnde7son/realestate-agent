# -*- coding: utf-8 -*-
"""
Nadlan API Client - Direct API access to nadlan.gov.il without browser automation.

This client provides direct access to the Nadlan API endpoints, bypassing the need
for browser automation tools like Playwright or Selenium.
"""

import json
import base64
import gzip
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import requests

from .models import Deal, NeighborhoodInfo
from .exceptions import NadlanAPIError, NadlanConfigError, NadlanDecodeError


@dataclass
class NadlanConfig:
    """Configuration for Nadlan API endpoints."""

    # Base URLs - these are fallbacks if config.json is not accessible
    config_url: str = "https://www.nadlan.gov.il/config.json"

    # URLs from config.json (when available)
    autocomplete_url: Optional[str] = None
    deals_url: Optional[str] = None
    neighborhood_info_url: Optional[str] = None

    # Additional URLs that might be in config.json
    api_base: Optional[str] = None
    s3_deals_base: Optional[str] = None
    search_base_url: Optional[str] = None

    @classmethod
    def from_config_data(cls, config_data: Dict[str, Any]) -> "NadlanConfig":
        """Create config from API config.json response."""
        return cls(
            autocomplete_url=config_data.get("autocompleteUrl"),
            deals_url=config_data.get("dealsUrl"),
            neighborhood_info_url=config_data.get("neighborhoodInfoUrl"),
            api_base=config_data.get("apiBase"),
            s3_deals_base=config_data.get("s3DealsBase"),
            search_base_url=config_data.get("searchBaseUrl"),
        )

    def get_neighborhood_url(self, neighborhood_id: str) -> str:
        """Get the URL for neighborhood data, using config if available."""
        if self.api_base:
            return f"{self.api_base}/pages/neighborhood/buy/{neighborhood_id}.json"
        return f"https://d30nq1hiio0r3z.cloudfront.net/api/pages/neighborhood/buy/{neighborhood_id}.json"

    def get_neighborhoods_index_url(self) -> str:
        """Get the URL for neighborhoods index, using config if available."""
        if self.api_base:
            return f"{self.api_base}/index/neigh.json"
        return "https://d30nq1hiio0r3z.cloudfront.net/api/index/neigh.json"


class NadlanAPIClient:
    """
    Direct API client for nadlan.gov.il.

    This client provides methods to interact with the Nadlan API without
    requiring browser automation.
    """

    def __init__(
        self,
        config: Optional[NadlanConfig] = None,
        session: Optional[requests.Session] = None,
    ):
        """
        Initialize the API client.

        Args:
            config: Optional configuration. If not provided, will fetch from API.
            session: Optional requests session for maintaining cookies and state.
        """
        self.config = config or NadlanConfig()
        self.session = session or requests.Session()
        self.session.headers.update(self._get_headers())

    def _decode_base64_gzip(self, data: str) -> str:
        """
        Decode base64-encoded gzipped data.

        Args:
            data: Base64-encoded gzipped string

        Returns:
            Decoded string

        Raises:
            NadlanDecodeError: If decoding fails
        """
        try:
            # Decode base64
            compressed_data = base64.b64decode(data)

            # Decompress gzip
            decompressed_data = gzip.decompress(compressed_data)

            # Decode to string
            return decompressed_data.decode("utf-8")

        except Exception as e:
            raise NadlanDecodeError(f"Failed to decode base64-gzipped data: {e}")

    def _decrypt_response(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt the encrypted response from the Nadlan API using pako-style decompression.
        
        Since the website uses pako (JavaScript zlib), we need to handle the same
        compression format that pako produces.
        
        Args:
            encrypted_data: The encrypted response string
            
        Returns:
            Decrypted JSON data as dictionary
        """
        import base64
        import zlib
        import json
        
        try:
            # First try to parse as JSON directly
            try:
                return json.loads(encrypted_data)
            except json.JSONDecodeError:
                pass
            
            # Try base64 decoding first
            try:
                # Add padding if needed
                if len(encrypted_data) % 4 != 0:
                    encrypted_data += "=" * (4 - len(encrypted_data) % 4)
                
                decoded = base64.b64decode(encrypted_data)
                
                # Try zlib decompression (pako uses zlib)
                try:
                    decompressed = zlib.decompress(decoded)
                    return json.loads(decompressed.decode('utf-8'))
                except zlib.error:
                    # Try gzip decompression as fallback
                    try:
                        import gzip
                        decompressed = gzip.decompress(decoded)
                        return json.loads(decompressed.decode('utf-8'))
                    except gzip.BadGzipFile:
                        # Try as plain text
                        try:
                            return json.loads(decoded.decode('utf-8'))
                        except:
                            pass
            except Exception:
                pass
            
            # Try splitting by dots (common encrypted format)
            try:
                parts = encrypted_data.split('.')
                if len(parts) >= 2:
                    # Try to decode each part
                    for part in parts:
                        try:
                            # Add padding if needed
                            if len(part) % 4 != 0:
                                part += "=" * (4 - len(part) % 4)
                            
                            decoded = base64.b64decode(part)
                            
                            # Try zlib decompression (pako style)
                            try:
                                decompressed = zlib.decompress(decoded)
                                data = json.loads(decompressed.decode('utf-8'))
                                if isinstance(data, dict) and ('items' in data or 'data' in data):
                                    return data
                            except zlib.error:
                                # Try gzip as fallback
                                try:
                                    import gzip
                                    decompressed = gzip.decompress(decoded)
                                    data = json.loads(decompressed.decode('utf-8'))
                                    if isinstance(data, dict) and ('items' in data or 'data' in data):
                                        return data
                                except:
                                    # Try as plain text
                                    try:
                                        data = json.loads(decoded.decode('utf-8'))
                                        if isinstance(data, dict) and ('items' in data or 'data' in data):
                                            return data
                                    except:
                                        continue
                        except:
                            continue
            except Exception:
                pass
            
            # If all else fails, return the raw data for debugging
            return {"error": "Could not decrypt response", "raw_data": encrypted_data[:200]}
            
        except Exception as e:
            return {"error": f"Decryption failed: {e}", "raw_data": encrypted_data[:200]}

    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "he,en;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "referer": "https://www.nadlan.gov.il/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }

    def establish_session(self) -> None:
        """
        Establish a session by visiting the main website and a neighborhood page.

        This helps acquire necessary cookies and establish proper session context.
        """
        try:
            # Visit main website
            response = self.session.get("https://www.nadlan.gov.il/", timeout=30)
            response.raise_for_status()

            # Visit a neighborhood page to get additional cookies
            response = self.session.get(
                "https://www.nadlan.gov.il/?view=neighborhood&id=65210036&page=deals",
                timeout=30,
            )
            response.raise_for_status()

        except Exception as e:
            # Don't raise error, just log - session establishment is best effort
            print(f"Session establishment warning: {e}")

    def get_fresh_token(self) -> str:
        """
        Try to get a fresh JWT token from the website.
        
        Returns:
            Fresh JWT token or fallback to hardcoded token
        """
        try:
            # Visit the main page to get any tokens in cookies or HTML
            response = self.session.get("https://www.nadlan.gov.il/", timeout=30)
            response.raise_for_status()
            
            # Check cookies for any JWT-like tokens
            for cookie in self.session.cookies:
                if cookie.name and ('token' in cookie.name.lower() or 'jwt' in cookie.name.lower()):
                    print(f"Found potential token cookie: {cookie.name}")
                    return cookie.value
            
            # Check HTML for any embedded tokens
            html_content = response.text
            
            # Look for JWT patterns in the HTML
            import re
            jwt_pattern = r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
            matches = re.findall(jwt_pattern, html_content)
            
            if matches:
                print(f"Found {len(matches)} potential JWT tokens in HTML")
                # Return the first one that looks like a JWT
                for token in matches:
                    if len(token) > 50:  # JWT tokens are typically longer
                        print(f"Using token from HTML: {token[:50]}...")
                        return token
            
            # Try to get token from the reCAPTCHA endpoint mentioned in config
            config_data = self.load_config()
            recaptcha_token_url = config_data.get("recaptcha_token_url")
            
            if recaptcha_token_url:
                try:
                    token_response = self.session.get(recaptcha_token_url, timeout=10)
                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        if 'token' in token_data:
                            print(f"Got token from reCAPTCHA endpoint: {token_data['token'][:50]}...")
                            return token_data['token']
                except Exception as e:
                    print(f"Failed to get token from reCAPTCHA endpoint: {e}")
            
            print("No fresh token found, using hardcoded token")
            return "eyJhbGciOiJIUzI1NiJ9.eyJkb21haW4iOiJkZXYubmFkbGFuLmdvdi5pbCIsImV4cCI6MTcyOTQxOTY3NH0.nwjNBPOn2xKgtoREu2McVZjPRevomyAedyUrHav2wV4"
            
        except Exception as e:
            print(f"Error getting fresh token: {e}")
            return "eyJhbGciOiJIUzI1NiJ9.eyJkb21haW4iOiJkZXYubmFkbGFuLmdvdi5pbCIsImV4cCI6MTcyOTQxOTY3NH0.nwjNBPOn2xKgtoREu2McVZjPRevomyAedyUrHav2wV4"

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from nadlan.gov.il/config.json.

        Returns:
            Configuration dictionary

        Raises:
            NadlanConfigError: If config cannot be loaded
        """
        try:
            response = self.session.get(self.config.config_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise NadlanConfigError(
                f"Failed to load config from {self.config.config_url}: {e}"
            )

    def get_neighborhoods_index(self) -> Dict[str, Any]:
        """
        Get the neighborhoods index mapping.

        Returns:
            Dictionary mapping neighborhood IDs

        Raises:
            NadlanAPIError: If request fails
        """
        config_data = self.load_config()
        neigh_index_url = config_data.get(
            "neighbourhoods",
            "https://d30nq1hiio0r3z.cloudfront.net/api/index/neigh.json",
        )

        response = self.session.get(neigh_index_url)
        response.raise_for_status()
        return response.json()

    def get_neighborhood_data(self, neighborhood_id: str) -> Dict[str, Any]:
        """
        Get neighborhood data including trends and other information.

        Args:
            neighborhood_id: The neighborhood ID

        Returns:
            Dictionary with neighborhood data including trends, other neighborhoods, etc.

        Raises:
            NadlanAPIError: If request fails
        """
        # Use the correct endpoint with timestamp for cache busting
        import time

        config_data = self.load_config()
        s3_page_base = config_data.get(
            "s3_page_base", "https://d30nq1hiio0r3z.cloudfront.net/api/pages"
        )
        timestamp = int(time.time() * 1000)
        url = f"{s3_page_base}/neighborhood/buy/{neighborhood_id}.json?t={timestamp}"

        response = self.session.get(url)
        response.raise_for_status()

        # Try to parse as JSON first
        try:
            return response.json()
        except json.JSONDecodeError:
            # If not JSON, try to decode as base64-gzipped data
            try:
                decoded_text = self._decode_base64_gzip(response.text)
                return json.loads(decoded_text)
            except NadlanDecodeError:
                # If all else fails, raise the original JSON decode error
                raise NadlanAPIError(
                    f"Response is not valid JSON: {response.text[:200]}"
                )

    def get_deals_by_neighborhood_id(
        self, neighborhood_id: str, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get real estate deals for a neighborhood using the correct API endpoint.

        Based on the discovered working implementation, this method uses:
        POST https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal

        Args:
            neighborhood_id: The neighborhood ID
            limit: Maximum number of deals to return

        Returns:
            Raw deals data from API

        Raises:
            NadlanAPIError: If request fails
        """
        # Use the correct API endpoint and payload structure
        try:
            # First establish a session to get proper authentication
            self.establish_session()

            # Get configuration to use proper URLs
            config_data = self.load_config()

            # Use the correct API endpoint from config
            api_base = config_data.get(
                "api_base", "https://x4006fhmy5.execute-api.il-central-1.amazonaws.com"
            )
            # Remove trailing /api if present to avoid double /api/api/
            if api_base.endswith("/api"):
                api_base = api_base[:-4]
            api_url = f"{api_base}/api/deal"

            # Use empty token since the API seems to work without authentication
            auth_token = ""

            # Determine the appropriate base_name based on the ID type
            # Settlement IDs are typically 4 digits (1000-9999)
            # Neighborhood IDs are typically 8 digits (65210036, etc.)
            if len(neighborhood_id) == 4 and neighborhood_id.isdigit():
                base_name = "settlmentID"
                id_type = "settlement"
            else:
                base_name = "neigh_id"
                id_type = "neighborhood"
            
            print(f"Using {id_type} ID {neighborhood_id} with base_name '{base_name}'")
            
            # Prepare the payload based on the working implementation
            payload = {
                "base_id": neighborhood_id,
                "base_name": base_name,
                "fetch_number": "1",
                "type_order": "dealDate_down",
                "sk": auth_token
            }

            # Make the POST request with the correct format
            response = self.session.post(
                api_url,
                data=json.dumps(payload),
                headers={
                    "content-type": "text/plain",
                    "authority": "x4006fhmy5.execute-api.il-central-1.amazonaws.com",
                    "origin": "https://www.nadlan.gov.il",
                    "referer": "https://www.nadlan.gov.il/",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    **self._get_headers()
                },
            )
            response.raise_for_status()
            
            # Try to parse the response
            try:
                return response.json()
            except json.JSONDecodeError:
                # If not JSON, it might be encrypted/compressed data
                return self._decrypt_response(response.text)

        except Exception as e:
            raise NadlanAPIError(
                f"Could not fetch deals for neighborhood {neighborhood_id}: {e}"
            )
