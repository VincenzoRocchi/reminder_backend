from typing import Optional
import redis
import logging
from app.core.settings import settings
from app.core.exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisConnection:
    """
    Manages Redis connections with proper error handling and connection pooling.
    """
    
    _instance: Optional['RedisConnection'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_client is None:
            try:
                # Get Redis configuration from settings
                redis_url = settings.REDIS_URL
                redis_password = settings.REDIS_PASSWORD
                
                # Create Redis connection pool
                self._redis_client = redis.from_url(
                    redis_url,
                    password=redis_password,
                    decode_responses=True,  # Automatically decode responses to strings
                    socket_timeout=5,  # 5 seconds timeout
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                self._redis_client.ping()
                logger.info("Successfully connected to Redis")
                
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise RedisError(f"Redis connection failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {str(e)}")
                raise RedisError(f"Redis initialization failed: {str(e)}")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._redis_client is None:
            raise RedisError("Redis client not initialized")
        return self._redis_client
    
    def close(self):
        """Close Redis connection"""
        if self._redis_client:
            try:
                self._redis_client.close()
                self._redis_client = None
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
                raise RedisError(f"Failed to close Redis connection: {str(e)}")

# Create singleton instance
redis_connection = RedisConnection() 