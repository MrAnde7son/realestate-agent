# -*- coding: utf-8 -*-
"""
OAuth 2.0 utilities for authentication flows.

Provides helper functions for OAuth 2.0 Authorization Code flow with PKCE support.
Used by OAuth endpoints for MCP server, API clients, and other integrations.
"""
import hashlib
import base64


def generate_code_challenge(code_verifier, method='S256'):
    """Generate PKCE code challenge from verifier.
    
    Args:
        code_verifier: The code verifier string
        method: Challenge method ('S256' or 'plain')
    
    Returns:
        Code challenge string
    
    Raises:
        ValueError: If method is not supported
    """
    if method == 'S256':
        verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(verifier_hash).decode().rstrip('=')
    elif method == 'plain':
        return code_verifier
    else:
        raise ValueError(f"Unsupported code challenge method: {method}")

