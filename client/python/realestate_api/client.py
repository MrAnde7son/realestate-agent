"""
Real Estate API Client

A simple Python client for the Real Estate API.
"""

import requests
import json
from typing import Dict, Any, Optional, List
from .exceptions import APIException, AuthenticationError, ValidationError, NotFoundError, ServerError


class RealEstateAPIClient:
    """
    Client for the Real Estate API.
    
    Provides methods to interact with the Real Estate API including
    authentication, asset management, and data retrieval.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api", token: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API
            token: JWT access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if token:
            self.set_token(token)
    
    def set_token(self, token: str) -> None:
        """Set the JWT access token for authentication."""
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response data
            
        Raises:
            APIException: For various API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle different status codes
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please check your token.")
            elif response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code == 400:
                raise ValidationError(f"Validation error: {response.text}")
            elif response.status_code >= 500:
                raise ServerError(f"Server error: {response.text}")
            elif not response.ok:
                raise APIException(f"API error {response.status_code}: {response.text}")
            
            # Return JSON if available, otherwise return text
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}
                
        except requests.exceptions.RequestException as e:
            raise APIException(f"Request failed: {str(e)}")
    
    # Authentication methods
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Login response with access and refresh tokens
        """
        data = {"email": email, "password": password}
        response = self._make_request("POST", "/auth/login/", json=data)
        
        # Set token if provided
        if "access" in response:
            self.set_token(response["access"])
        
        return response
    
    def register(self, email: str, password: str, username: str, **kwargs) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            username: Username
            **kwargs: Additional user data (first_name, last_name, etc.)
            
        Returns:
            Registration response
        """
        data = {
            "email": email,
            "password": password,
            "username": username,
            **kwargs
        }
        return self._make_request("POST", "/auth/register/", json=data)
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access and refresh tokens
        """
        data = {"refresh": refresh_token}
        response = self._make_request("POST", "/auth/refresh/", json=data)
        
        # Update token if provided
        if "access" in response:
            self.set_token(response["access"])
        
        return response
    
    def logout(self) -> Dict[str, Any]:
        """Logout the current user."""
        return self._make_request("POST", "/auth/logout/")
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        return self._make_request("GET", "/auth/profile/")
    
    def update_profile(self, **kwargs) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            **kwargs: Profile data to update
            
        Returns:
            Updated profile data
        """
        return self._make_request("PUT", "/auth/update-profile/", json=kwargs)
    
    # Asset methods
    def get_assets(self, **params) -> Dict[str, Any]:
        """
        Get list of assets.
        
        Args:
            **params: Query parameters (page, limit, etc.)
            
        Returns:
            List of assets
        """
        return self._make_request("GET", "/assets/", params=params)
    
    def get_asset(self, asset_id: int) -> Dict[str, Any]:
        """
        Get asset by ID.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Asset data
        """
        return self._make_request("GET", f"/assets/{asset_id}/")
    
    def create_asset(self, **data) -> Dict[str, Any]:
        """
        Create a new asset.
        
        Args:
            **data: Asset data
            
        Returns:
            Created asset data
        """
        return self._make_request("POST", "/assets/", json=data)
    
    def update_asset(self, asset_id: int, **data) -> Dict[str, Any]:
        """
        Update an asset.
        
        Args:
            asset_id: Asset ID
            **data: Asset data to update
            
        Returns:
            Updated asset data
        """
        return self._make_request("PUT", f"/assets/{asset_id}/", json=data)
    
    def delete_asset(self, asset_id: int) -> Dict[str, Any]:
        """
        Delete an asset.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Deletion confirmation
        """
        return self._make_request("DELETE", f"/assets/{asset_id}/")
    
    def get_asset_stats(self) -> Dict[str, Any]:
        """Get asset statistics."""
        return self._make_request("GET", "/assets/stats/")
    
    # Permit methods
    def get_permits(self, **params) -> Dict[str, Any]:
        """Get list of permits."""
        return self._make_request("GET", "/permits/", params=params)
    
    def get_permit(self, permit_id: int) -> Dict[str, Any]:
        """Get permit by ID."""
        return self._make_request("GET", f"/permits/{permit_id}/")
    
    def create_permit(self, **data) -> Dict[str, Any]:
        """Create a new permit."""
        return self._make_request("POST", "/permits/", json=data)
    
    def update_permit(self, permit_id: int, **data) -> Dict[str, Any]:
        """Update a permit."""
        return self._make_request("PUT", f"/permits/{permit_id}/", json=data)
    
    def delete_permit(self, permit_id: int) -> Dict[str, Any]:
        """Delete a permit."""
        return self._make_request("DELETE", f"/permits/{permit_id}/")
    
    # Plan methods
    def get_plans(self, **params) -> Dict[str, Any]:
        """Get list of plans."""
        return self._make_request("GET", "/plans/", params=params)
    
    def get_plan(self, plan_id: int) -> Dict[str, Any]:
        """Get plan by ID."""
        return self._make_request("GET", f"/plans/{plan_id}/")
    
    def create_plan(self, **data) -> Dict[str, Any]:
        """Create a new plan."""
        return self._make_request("POST", "/plans/", json=data)
    
    def update_plan(self, plan_id: int, **data) -> Dict[str, Any]:
        """Update a plan."""
        return self._make_request("PUT", f"/plans/{plan_id}/", json=data)
    
    def delete_plan(self, plan_id: int) -> Dict[str, Any]:
        """Delete a plan."""
        return self._make_request("DELETE", f"/plans/{plan_id}/")
    
    # Additional methods
    def analyze_mortgage(self, **data) -> Dict[str, Any]:
        """Analyze mortgage data."""
        return self._make_request("POST", "/mortgage-analyze/", json=data)
    
    def sync_address(self, **data) -> Dict[str, Any]:
        """Sync address data."""
        return self._make_request("POST", "/sync-address/", json=data)
    
    def get_tabu(self, **params) -> Dict[str, Any]:
        """Get tabu information."""
        return self._make_request("GET", "/tabu/", params=params)
    
    def get_reports(self, **params) -> Dict[str, Any]:
        """Get reports."""
        return self._make_request("GET", "/reports/", params=params)
    
    def get_alerts(self) -> Dict[str, Any]:
        """Get alerts."""
        return self._make_request("GET", "/alerts/")
    
    def create_alert(self, **data) -> Dict[str, Any]:
        """Create an alert."""
        return self._make_request("POST", "/alerts/", json=data)
    
    def get_analytics_timeseries(self, **params) -> Dict[str, Any]:
        """Get analytics timeseries data."""
        return self._make_request("GET", "/analytics/timeseries", params=params)
