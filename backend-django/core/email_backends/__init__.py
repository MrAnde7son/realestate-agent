"""Email backend implementations for the core Django app."""

from .resend_backend import ResendEmailBackend

__all__ = ["ResendEmailBackend"]
