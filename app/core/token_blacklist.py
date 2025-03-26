from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
from app.core.settings import settings
from app.core.redis import redis_connection
from app.core.exceptions import RedisError

logger = logging.getLogger(__name__)

class TokenBlacklist:
    """
    Token blacklist implementation that uses Redis in production and in-memory storage in development.
    """
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}
        self._use_redis = settings.IS_PRODUCTION
        
        if self._use_redis:
            try:
                # Test Redis connection
                redis_connection.client.ping()
                logger.info("Using Redis for token blacklist")
            except RedisError as e:
                logger.warning(f"Redis connection failed, falling back to in-memory storage: {str(e)}")
                self._use_redis = False
    
    def add_token(self, jti: str, expires_at: datetime) -> None:
        """Add a token to the blacklist"""
        try:
            if self._use_redis:
                # Calculate TTL in seconds
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    redis_connection.client.setex(
                        f"blacklist:{jti}",
                        ttl,
                        "1"
                    )
            else:
                self._blacklist[jti] = expires_at
                
        except RedisError as e:
            logger.error(f"Failed to add token to blacklist: {str(e)}")
            # Fall back to in-memory storage if Redis fails
            self._use_redis = False
            self._blacklist[jti] = expires_at
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted"""
        try:
            if self._use_redis:
                return bool(redis_connection.client.get(f"blacklist:{jti}"))
            else:
                # Clean expired tokens for in-memory storage
                self._clean_expired()
                return jti in self._blacklist
                
        except RedisError as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            # Fall back to in-memory storage if Redis fails
            self._use_redis = False
            self._clean_expired()
            return jti in self._blacklist
    
    def _clean_expired(self) -> None:
        """Remove expired tokens from in-memory blacklist"""
        if not self._use_redis:
            now = datetime.utcnow()
            expired_tokens = [
                jti for jti, expires_at in self._blacklist.items() 
                if expires_at < now
            ]
            for jti in expired_tokens:
                del self._blacklist[jti]
    
    def __str__(self):
        """String representation for debugging"""
        if self._use_redis:
            return "Token Blacklist (Redis)"
        return f"Token Blacklist (In-Memory, {len(self._blacklist)} tokens)"
    
    def __repr__(self):
        """Detailed representation for debugging"""
        if self._use_redis:
            return "<TokenBlacklist storage=redis>"
        return f"<TokenBlacklist storage=memory tokens={len(self._blacklist)}>"

# Create singleton instance
token_blacklist = TokenBlacklist()