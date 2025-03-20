import time
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.core.settings import settings

class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, replace with Redis-based implementation.
    """
    def __init__(self, rate_limit: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            rate_limit: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
        
    def is_rate_limited(self, key: str) -> bool:
        """
        Check if a key is rate limited.
        
        Args:
            key: Unique identifier (IP address, user ID, etc.)
            
        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # Initialize if key not in requests
        if key not in self.requests:
            self.requests[key] = []
            
        # Clean up old requests
        self.requests[key] = [t for t in self.requests[key] 
                             if current_time - t < self.time_window]
        
        # Check if rate limit exceeded
        if len(self.requests[key]) >= self.rate_limit:
            return True
            
        # Add current request
        self.requests[key].append(current_time)
        return False


# Create rate limiters for different endpoints
login_limiter = RateLimiter(5, 60)  # 5 attempts per minute
signup_limiter = RateLimiter(10, 3600)  # 10 attempts per hour

async def rate_limit_login(request: Request):
    """
    Rate limit middleware for login endpoint.
    """
    client_ip = request.client.host
    
    if login_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )