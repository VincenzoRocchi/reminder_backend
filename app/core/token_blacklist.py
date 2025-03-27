from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
from jose import jwt, JWTError
from app.core.settings import settings
from app.core.redis import redis_connection
from app.core.exceptions import RedisError, TokenInvalidError
from app.core.security import get_signing_key

logger = logging.getLogger(__name__)

class TokenBlacklist:
    """
    Token blacklist implementation that uses Redis in production and in-memory storage in development.
    """
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}
        # Use Redis only in production, use in-memory for development and testing
        self._use_redis = settings.USE_REDIS
        
        if self._use_redis:
            try:
                # Test Redis connection
                redis_connection.client.ping()
                logger.info("Using Redis for token blacklist")
            except RedisError as e:
                # In production, we should fail if Redis is not available
                if settings.IS_PRODUCTION:
                    logger.error(f"Redis connection failed in production environment: {str(e)}")
                    raise RedisError(f"Redis is required in production mode: {str(e)}")
                else:
                    # In development, we can fall back to in-memory if USE_REDIS=True but Redis fails
                    logger.warning(f"Redis connection failed, falling back to in-memory storage: {str(e)}")
                    self._use_redis = False
        else:
            logger.info("Using in-memory token blacklist for development/testing")
    
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
            # In production, we should raise the error
            if settings.IS_PRODUCTION:
                logger.error(f"Failed to add token to Redis blacklist: {str(e)}")
                raise
            else:
                # In development, we can fall back to in-memory
                logger.error(f"Failed to add token to blacklist: {str(e)}")
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
            # In production, we should raise the error
            if settings.IS_PRODUCTION:
                logger.error(f"Failed to check Redis token blacklist: {str(e)}")
                raise
            else:
                # In development, we can fall back to in-memory
                logger.error(f"Failed to check token blacklist: {str(e)}")
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

def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    This is a wrapper around TokenBlacklist.is_blacklisted that can be imported directly.
    
    Args:
        token: The full JWT token to check
        
    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    try:
        # Decode the token to get the JTI claim
        # We use verify=False because we only need the JWT claims, not a full validation
        # The token validation is done elsewhere in the auth process
        payload = jwt.decode(
            token, 
            get_signing_key(), 
            algorithms=[settings.ALGORITHM], 
            options={"verify_signature": True}
        )
        
        # Get the JTI (JWT ID) claim
        jti = payload.get("jti")
        if not jti:
            logger.warning("Token has no JTI claim")
            return False
        
        # Check if the token is in the blacklist
        return token_blacklist.is_blacklisted(jti)
    except JWTError as e:
        # If token can't be decoded, log and return False to avoid blocking valid requests
        logger.warning(f"Could not decode token for blacklist check: {str(e)}")
        return False