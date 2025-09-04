"""
Search result caching service for YouTrack MCP server
Reduces API calls by caching search results with TTL
"""
import hashlib
import json
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()

@dataclass
class CacheEntry:
    """Represents a cached search result"""
    data: Dict[str, Any]
    created_at: datetime
    ttl_seconds: int
    query_hash: str
    query: str
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat()
        }

class SearchResultCache:
    """In-memory cache for YouTrack search results with TTL support"""
    
    def __init__(self, default_ttl_seconds: int = 300, max_entries: int = 1000):
        self.default_ttl_seconds = default_ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, CacheEntry] = {}
        self._query_hashes: Set[str] = set()  # Track all query hashes
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Initialized search result cache", 
                   default_ttl_seconds=default_ttl_seconds,
                   max_entries=max_entries)
    
    def _generate_query_hash(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate a hash for query + parameters"""
        cache_key = {
            "query": query,
            "params": params or {}
        }
        # Sort params for consistent hashing
        if params:
            cache_key["params"] = dict(sorted(params.items()))
        
        key_str = json.dumps(cache_key, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(
        self, 
        query: str, 
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached search result if available and not expired"""
        query_hash = self._generate_query_hash(query, params)
        
        if query_hash not in self._cache:
            logger.debug("Cache miss", query_hash=query_hash[:8], query=query[:50])
            return None
        
        entry = self._cache[query_hash]
        
        if entry.is_expired():
            logger.debug("Cache expired", query_hash=query_hash[:8], 
                        age_seconds=(datetime.now() - entry.created_at).total_seconds())
            # Remove expired entry
            del self._cache[query_hash]
            self._query_hashes.discard(query_hash)
            return None
        
        logger.info("Cache hit", query_hash=query_hash[:8], 
                   age_seconds=(datetime.now() - entry.created_at).total_seconds())
        
        return entry.data
    
    async def set(
        self,
        query: str,
        data: Dict[str, Any],
        params: Dict[str, Any] = None,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """Store search result in cache"""
        query_hash = self._generate_query_hash(query, params)
        ttl = ttl_seconds or self.default_ttl_seconds
        
        # Check if we need to evict old entries
        if len(self._cache) >= self.max_entries and query_hash not in self._cache:
            await self._evict_oldest()
        
        entry = CacheEntry(
            data=data,
            created_at=datetime.now(),
            ttl_seconds=ttl,
            query_hash=query_hash,
            query=query
        )
        
        self._cache[query_hash] = entry
        self._query_hashes.add(query_hash)
        
        logger.info("Cached search result", 
                   query_hash=query_hash[:8],
                   data_size=len(json.dumps(data)),
                   ttl_seconds=ttl)
        
        return query_hash
    
    async def invalidate(self, query: str, params: Dict[str, Any] = None) -> bool:
        """Invalidate a specific cached entry"""
        query_hash = self._generate_query_hash(query, params)
        
        if query_hash in self._cache:
            del self._cache[query_hash]
            self._query_hashes.discard(query_hash)
            logger.info("Invalidated cache entry", query_hash=query_hash[:8])
            return True
        
        return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching a query pattern (simple substring match)"""
        invalidated = 0
        
        # Find matching entries
        to_remove = []
        for query_hash, entry in self._cache.items():
            if pattern.lower() in entry.query.lower():
                to_remove.append(query_hash)
        
        # Remove them
        for query_hash in to_remove:
            del self._cache[query_hash]
            self._query_hashes.discard(query_hash)
            invalidated += 1
        
        if invalidated > 0:
            logger.info("Invalidated cache entries by pattern", 
                       pattern=pattern, count=invalidated)
        
        return invalidated
    
    async def clear(self) -> int:
        """Clear all cached entries"""
        count = len(self._cache)
        self._cache.clear()
        self._query_hashes.clear()
        
        logger.info("Cleared all cache entries", count=count)
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        expired_count = 0
        total_size = 0
        
        for entry in self._cache.values():
            if entry.is_expired():
                expired_count += 1
            total_size += len(json.dumps(entry.data))
        
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "total_size_bytes": total_size,
            "max_entries": self.max_entries,
            "default_ttl_seconds": self.default_ttl_seconds,
            "hit_ratio": getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
        }
    
    async def _evict_oldest(self) -> None:
        """Evict the oldest cache entry to make room"""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_hash = min(self._cache.keys(), 
                         key=lambda k: self._cache[k].created_at)
        
        del self._cache[oldest_hash]
        self._query_hashes.discard(oldest_hash)
        
        logger.debug("Evicted oldest cache entry", query_hash=oldest_hash[:8])
    
    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                
                expired_hashes = []
                for query_hash, entry in self._cache.items():
                    if entry.is_expired():
                        expired_hashes.append(query_hash)
                
                for query_hash in expired_hashes:
                    del self._cache[query_hash]
                    self._query_hashes.discard(query_hash)
                
                if expired_hashes:
                    logger.debug("Cleaned up expired cache entries", count=len(expired_hashes))
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cache cleanup", error=str(e))
    
    async def shutdown(self) -> None:
        """Shutdown the cache and cleanup task"""
        if hasattr(self, '_cleanup_task'):
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()
        logger.info("Cache shutdown complete")

# Global cache instance
_global_cache: Optional[SearchResultCache] = None

def get_cache() -> SearchResultCache:
    """Get or create the global cache instance"""
    global _global_cache
    
    if _global_cache is None:
        _global_cache = SearchResultCache(
            default_ttl_seconds=300,  # 5 minutes default TTL
            max_entries=1000
        )
    
    return _global_cache

async def shutdown_cache() -> None:
    """Shutdown the global cache"""
    global _global_cache
    
    if _global_cache is not None:
        await _global_cache.shutdown()
        _global_cache = None

# Smart caching strategies for different query types
class SmartCacheStrategy:
    """Intelligent caching strategies for different types of YouTrack queries"""
    
    @staticmethod
    def get_ttl_for_query(query: str, results_count: int = 0) -> int:
        """Determine appropriate TTL based on query characteristics"""
        query_lower = query.lower()
        
        # Recent queries (today, this week) - shorter TTL
        if any(term in query_lower for term in ['today', 'this week', '{today}']):
            return 60  # 1 minute
        
        # General searches - medium TTL
        if any(term in query_lower for term in ['project:', '#unresolved', 'summary:']):
            return 300  # 5 minutes
        
        # Specific issue queries - longer TTL
        if 'id:' in query_lower or results_count <= 5:
            return 900  # 15 minutes
        
        # Large result sets - shorter TTL to avoid stale data
        if results_count > 50:
            return 180  # 3 minutes
        
        # Default
        return 300  # 5 minutes
    
    @staticmethod  
    def should_cache_query(query: str, results_count: int = 0) -> bool:
        """Determine if a query result should be cached"""
        query_lower = query.lower()
        
        # Don't cache very specific queries that are unlikely to be repeated
        if len(query) > 200:
            return False
        
        # Don't cache queries with very few results (likely very specific)
        if results_count == 1:
            return False
        
        # Don't cache empty results
        if results_count == 0:
            return False
        
        # Cache most other queries
        return True