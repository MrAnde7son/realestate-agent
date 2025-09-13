"""
Custom exceptions for the Real Estate API client.
"""


class APIException(Exception):
    """Base exception for API-related errors."""
    pass


class AuthenticationError(APIException):
    """Raised when authentication fails."""
    pass


class ValidationError(APIException):
    """Raised when request validation fails."""
    pass


class NotFoundError(APIException):
    """Raised when a resource is not found."""
    pass


class ServerError(APIException):
    """Raised when the server returns an error."""
    pass
