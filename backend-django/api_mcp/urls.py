# -*- coding: utf-8 -*-
"""
URL patterns for the MCP server endpoint.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.mcp_endpoint, name='mcp_endpoint'),
]

