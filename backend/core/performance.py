"""
Performance-optimized CLI utilities for Casper.

This module provides caching, async I/O, and performance monitoring
for the Casper CLI.
"""

import functools
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar
from dataclasses import dataclass
import logging

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheConfig:
    """Configuration for the caching system."""
    enabled: bool = True
    ttl: int = 300  # 5 minutes in seconds
    max_size: int = 1000
    cache_dir: Path = Path.home() / ".casper_cache"


class ResponseCache:
    """Simple file-based cache for API responses."""
    
    def __init__(self, config: CacheConfig = CacheConfig()):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_dir = config.cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(self, key: str) -> str:
        """Generate a consistent cache key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache entry."""
        cache_key = self._get_cache_key(key)
        return self._cache_dir / f"{cache_key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.config.enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                
                # Check TTL
                if time.time() - data.get('timestamp', 0) < self.config.ttl:
                    logger.debug(f"Cache hit for key: {key}")
                    return data.get('value')
                else:
                    logger.debug(f"Cache expired for key: {key}")
                    cache_path.unlink()
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Error reading cache for {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        if not self.config.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        data = {
            'value': value,
            'timestamp': time.time()
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cached value for key: {key}")
        except OSError as e:
            logger.warning(f"Error writing cache for {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        for cache_file in self._cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError:
                pass
        self._cache.clear()


# Global cache instance
cache = ResponseCache()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (overrides global config)
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{frozenset(kwargs.items())}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Store in cache
            original_ttl = cache.config.ttl
            if ttl is not None:
                cache.config.ttl = ttl
            cache.set(cache_key, result)
            cache.config.ttl = original_ttl
            
            return result
        return wrapper
    return decorator


async def async_request_with_retry(
    func: Callable[..., Any],
    max_retries: int = 3,
    retry_delay: float = 1.0,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Execute an async request with retry logic.
    
    Args:
        func: The async function to call
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        The result of the function call
    
    Raises:
        Exception: If all retries fail
    """
    import asyncio
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (attempt + 1))
    
    raise last_exception


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start a timer for an operation."""
        self._metrics[operation] = {
            'start': time.time(),
            'count': self._metrics.get(operation, {}).get('count', 0) + 1
        }
    
    def end_timer(self, operation: str, success: bool = True) -> float:
        """End a timer and record the duration."""
        if operation not in self._metrics:
            return 0.0
        
        duration = time.time() - self._metrics[operation]['start']
        
        if operation not in self._metrics:
            self._metrics[operation] = {}
        
        self._metrics[operation]['total_time'] =             self._metrics[operation].get('total_time', 0.0) + duration
        self._metrics[operation]['success_count'] =             self._metrics[operation].get('success_count', 0) + (1 if success else 0)
        self._metrics[operation]['failure_count'] =             self._metrics[operation].get('failure_count', 0) + (0 if success else 1)
        
        return duration
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all collected metrics."""
        return self._metrics.copy()
    
    def get_average_time(self, operation: str) -> float:
        """Get average execution time for an operation."""
        if operation not in self._metrics:
            return 0.0
        
        metrics = self._metrics[operation]
        count = metrics.get('count', 0)
        total = metrics.get('total_time', 0.0)
        
        return total / count if count > 0 else 0.0


# Global performance monitor
performance_monitor = PerformanceMonitor()


__all__ = [
    'cache',
    'cached',
    'async_request_with_retry',
    'performance_monitor',
    'PerformanceMonitor',
    'ResponseCache',
    'CacheConfig'
]
