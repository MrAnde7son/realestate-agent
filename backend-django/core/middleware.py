"""Middleware for tracking API performance metrics."""
import time
from django.utils.deprecation import MiddlewareMixin
from .analytics import track_performance


class APIPerformanceMiddleware(MiddlewareMixin):
    """Middleware to track API response times."""
    
    def process_request(self, request):
        """Store the start time for the request."""
        # Only track API requests (those starting with /api/)
        if request.path.startswith('/api/'):
            request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Track the response time for API requests."""
        # Only track API requests
        if hasattr(request, '_start_time') and request.path.startswith('/api/'):
            response_time = time.time() - request._start_time
            
            # Track API response time (only for non-analytics endpoints to avoid recursion)
            if not request.path.startswith('/api/analytics/'):
                track_performance(
                    metric='api_response_time',
                    value=response_time,
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    meta={
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                    }
                )
        
        return response

