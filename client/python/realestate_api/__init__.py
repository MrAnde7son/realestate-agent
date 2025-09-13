"""
Real Estate API Python Client

Auto-generated Python client for the Real Estate API.
"""

__version__ = "1.0.0"
__author__ = "Real Estate API Team"

from .client import RealEstateAPIClient
from .exceptions import APIException, AuthenticationError, ValidationError

__all__ = [
    "RealEstateAPIClient",
    "APIException", 
    "AuthenticationError",
    "ValidationError"
]
