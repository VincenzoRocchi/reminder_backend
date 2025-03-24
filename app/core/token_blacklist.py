from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class InMemoryTokenBlacklist:
    """
    In-memory implementation of token blacklist.
    
    In production, consider using Redis or another shared cache.
    """
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}
        
    def add_token(self, jti: str, expires_at: datetime) -> None:
        """Add a token to the blacklist"""
        self._blacklist[jti] = expires_at
        
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted"""
        # Clean expired tokens occasionally
        self._clean_expired()
        
        return jti in self._blacklist
        
    def _clean_expired(self) -> None:
        """Remove expired tokens from blacklist"""
        now = datetime.utcnow()
        expired_tokens = [jti for jti, expires_at in self._blacklist.items() 
                        if expires_at < now]
        
        for jti in expired_tokens:
            del self._blacklist[jti]
            
    # For debugging
    def __str__(self):
        return f"Token Blacklist ({len(self._blacklist)} tokens)"

    def __repr__(self):
        return f"<InMemoryTokenBlacklist tokens={len(self._blacklist)}>"     

# For production, implement a Redis-based blacklist:
# class RedisTokenBlacklist:
#     """Redis-based token blacklist"""
#     def __init__(self, redis_url: str):
#         self.redis = redis.from_url(redis_url)
#     
#     def add_token(self, jti: str, expires_at: datetime) -> None:
#         """Add a token to the blacklist with expiration"""
#         ttl = int((expires_at - datetime.utcnow()).total_seconds())
#         if ttl > 0:
#             self.redis.setex(f"blacklist:{jti}", ttl, "1")
#     
#     def is_blacklisted(self, jti: str) -> bool:
#         """Check if a token is blacklisted"""
#         return bool(self.redis.get(f"blacklist:{jti}"))


# Use in-memory for development, Redis for production
token_blacklist = InMemoryTokenBlacklist()
# token_blacklist = RedisTokenBlacklist(settings.REDIS_URL) # For production