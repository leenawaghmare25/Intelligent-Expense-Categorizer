"""
Rate limiting decorator for delete operations to prevent abuse.
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import time
from collections import defaultdict, deque

# In-memory rate limiter (in production, use Redis)
rate_limit_storage = defaultdict(lambda: deque())

def rate_limit(max_requests=10, window_seconds=60, per_user=True):
    """
    Rate limiting decorator for delete operations.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        per_user: If True, limit per user; if False, limit per IP
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier (user ID or IP)
            if per_user and current_user.is_authenticated:
                identifier = f"user_{current_user.id}"
            else:
                identifier = f"ip_{request.remote_addr}"
            
            # Get current time
            now = time.time()
            
            # Clean old requests outside the window
            user_requests = rate_limit_storage[identifier]
            while user_requests and user_requests[0] < now - window_seconds:
                user_requests.popleft()
            
            # Check if limit exceeded
            if len(user_requests) >= max_requests:
                if request.is_json:
                    return jsonify({
                        'error': 'Rate limit exceeded. Please try again later.',
                        'retry_after': window_seconds
                    }), 429
                else:
                    return "Rate limit exceeded. Please try again later.", 429
            
            # Add current request
            user_requests.append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator