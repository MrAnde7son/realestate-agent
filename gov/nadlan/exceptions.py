# -*- coding: utf-8 -*-
class NadlanError(Exception):
    """Base exception for Nadlan package."""

class NadlanConfigError(NadlanError):
    """Raised when config.json cannot be fetched or parsed."""

class NadlanAPIError(NadlanError):
    """Raised for HTTP/API related errors."""

class NadlanDecodeError(NadlanError):
    """Raised when decoding API responses fails."""
