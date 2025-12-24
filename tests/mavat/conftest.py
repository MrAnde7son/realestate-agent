#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest fixtures for Mavat tests."""

from unittest.mock import Mock
import pytest


@pytest.fixture
def mock_requests_session():
    """Mocked requests.Session object for MavatAPIClient tests.

    Provides mocked attributes/methods accessed by the client:
    - headers.update
    - cookies.update
    - get / post
    - close
    """
    session = Mock(name="requests.Session")

    # headers and cookies with update()
    session.headers = Mock()
    session.headers.update = Mock()
    session.cookies = Mock()
    session.cookies.update = Mock()

    # HTTP verbs
    session.get = Mock()
    session.post = Mock()

    # Close
    session.close = Mock()

    return session
