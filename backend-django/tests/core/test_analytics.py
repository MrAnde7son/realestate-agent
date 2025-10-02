#!/usr/bin/env python3
"""
Test script to generate analytics events for testing
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the backend-django directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend-django'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
django.setup()

from core.analytics import track, track_page_view, track_search, track_feature_usage, track_performance, rollup_day
from core.models import User, AnalyticsEvent, AnalyticsDaily
from django.utils import timezone

def create_test_events():
    """Create test analytics events"""
    print("Creating test analytics events...")
    
    # Create some test users
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'username': 'testuser', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Track various events
    track('user_signup', user=user)
    track('asset_create', user=user, asset_id=1)
    track('report_success', user=user, asset_id=1)
    track('alert_rule_create', user=user, asset_id=1)
    
    # Track page views
    track_page_view(
        session_id='test_session_1',
        page_path='/assets',
        user=user,
        page_title='Assets Page',
        load_time=1.5,
        duration=30.0,
        meta={'user_agent': 'test', 'ip_address': '127.0.0.1'}
    )
    
    track_page_view(
        session_id='test_session_2',
        page_path='/assets/1',
        user=user,
        page_title='Asset Detail',
        load_time=2.1,
        duration=45.0,
        meta={'user_agent': 'test', 'ip_address': '127.0.0.1'}
    )
    
    # Track searches
    track_search('apartment tel aviv', user=user, results_count=5)
    track_search('house jerusalem', user=user, results_count=3)
    track_search('villa haifa', user=user, results_count=2)
    
    # Track feature usage
    track_feature_usage('filter', user=user, asset_id=1, meta={'filter_type': 'city', 'value': 'tel_aviv'})
    track_feature_usage('filter', user=user, asset_id=1, meta={'filter_type': 'price_min', 'value': 1000000})
    track_feature_usage('export', user=user, asset_id=1, meta={'export_type': 'csv', 'asset_count': 1})
    track_feature_usage('marketing_message', user=user, asset_id=1, meta={'message_type': 'share_message', 'language': 'he'})
    
    # Track performance metrics
    track_performance('page_load_time', 1.2, user=user)
    track_performance('api_response_time', 0.8, user=user)
    
    print(f"Created {AnalyticsEvent.objects.count()} analytics events")
    
    # Rollup today's data
    today = timezone.now().date()
    rollup_day(today)
    print(f"Rolled up analytics for {today}")
    
    # Check the results
    daily = AnalyticsDaily.objects.get(date=today)
    print(f"\nAnalytics for {today}:")
    print(f"Page views: {daily.page_views}")
    print(f"Unique visitors: {daily.unique_visitors}")
    print(f"Searches performed: {daily.searches_performed}")
    print(f"Marketing messages created: {daily.marketing_messages_created}")
    print(f"Filters applied: {daily.filters_applied}")
    print(f"Exports downloaded: {daily.exports_downloaded}")
    print(f"Avg page load time: {daily.avg_page_load_time}")
    print(f"API response time avg: {daily.api_response_time_avg}")

if __name__ == '__main__':
    create_test_events()
