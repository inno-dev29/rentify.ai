"""
Simple caching mechanism for LLM responses.
Helps reduce API costs by caching responses for identical prompts.
"""

import json
import hashlib
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from django.conf import settings

class LLMResponseCache:
    """
    A file-based cache for LLM responses.
    Reduces API costs by storing responses locally.
    """
    
    def __init__(self, cache_dir: str = None, max_age_seconds: int = 86400 * 7):  # 7 days default
        """
        Initialize the cache with specified directory and TTL.
        
        Args:
            cache_dir: Directory to store cache files (default: project root / .llm_cache)
            max_age_seconds: Maximum age of cache entries before considered stale
        """
        self.max_age_seconds = max_age_seconds
        
        # If no cache directory specified, create one in the project root
        if cache_dir is None:
            from django.conf import settings
            base_dir = Path(settings.BASE_DIR)
            cache_dir = getattr(settings, 'LLM_CACHE_DIR', base_dir / '.llm_cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
    
    def get_cache_key(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """
        Generate a unique cache key based on the prompts and model.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            model: LLM model name
            
        Returns:
            A unique hash string to use as a filename
        """
        content = f"{system_prompt}|{user_prompt}|{model}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, system_prompt: str, user_prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if it exists and is not stale.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            model: LLM model name
            
        Returns:
            Cached response dict or None if not found/stale
        """
        key = self.get_cache_key(system_prompt, user_prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if the cache is stale
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.max_age_seconds:
            # Cache is stale, remove it
            cache_file.unlink(missing_ok=True)
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            # If there's an error reading the cache, consider it invalid
            cache_file.unlink(missing_ok=True)
            return None
    
    def set(self, system_prompt: str, user_prompt: str, model: str, response: Dict[str, Any]) -> None:
        """
        Store a response in the cache.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            model: LLM model name
            response: Response data to cache
        """
        key = self.get_cache_key(system_prompt, user_prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(response, f)
        except Exception as e:
            # Log but don't raise - caching errors shouldn't break the application
            from logging import getLogger
            logger = getLogger(__name__)
            logger.warning(f"Failed to cache LLM response: {str(e)}")
    
    def clear(self, max_age_seconds: Optional[int] = None) -> int:
        """
        Clear all cache entries or just the stale ones.
        
        Args:
            max_age_seconds: If provided, only clear entries older than this
            
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob('*.json'):
            if max_age_seconds is None or (current_time - cache_file.stat().st_mtime > max_age_seconds):
                cache_file.unlink(missing_ok=True)
                cleared_count += 1
        
        return cleared_count
    
    # Advanced caching methods for optimized DeepSeek client
    
    def get_advanced_cache_key(self, key_str: str) -> str:
        """
        Generate a unique cache key for advanced caching scenarios.
        
        Args:
            key_str: String to use for key generation
            
        Returns:
            A unique hash string to use as a filename
        """
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def get_advanced(self, key_str: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response using a pre-formatted key string.
        Useful for context-aware caching and multi-provider caching.
        
        Args:
            key_str: Formatted key string that uniquely identifies the cache entry
            
        Returns:
            Cached response dict or None if not found/stale
        """
        key = self.get_advanced_cache_key(key_str)
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if the cache is stale
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.max_age_seconds:
            # Cache is stale, remove it
            cache_file.unlink(missing_ok=True)
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            # If there's an error reading the cache, consider it invalid
            cache_file.unlink(missing_ok=True)
            return None
    
    def set_advanced(self, key_str: str, response: Dict[str, Any]) -> None:
        """
        Store a response in the cache using a pre-formatted key string.
        
        Args:
            key_str: Formatted key string that uniquely identifies the cache entry
            response: Response data to cache
        """
        key = self.get_advanced_cache_key(key_str)
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(response, f)
        except Exception as e:
            # Log but don't raise - caching errors shouldn't break the application
            from logging import getLogger
            logger = getLogger(__name__)
            logger.warning(f"Failed to cache LLM response with advanced key: {str(e)}")
    
    def get_cache_stats_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed cache statistics segmented by provider.
        
        Returns:
            Dictionary with statistics for each provider
        """
        if not os.path.exists(self.cache_dir):
            return {
                "total": {
                    "entry_count": 0,
                    "total_size": 0,
                    "oldest_entry": None,
                    "newest_entry": None
                },
                "providers": {
                    "deepseek": {"count": 0, "size": 0},
                    "claude": {"count": 0, "size": 0},
                    "unknown": {"count": 0, "size": 0}
                }
            }
        
        cache_files = list(Path(self.cache_dir).glob("*.json"))
        
        stats = {
            "total": {
                "entry_count": len(cache_files),
                "total_size": 0,
                "oldest_entry": float('inf'),
                "newest_entry": 0
            },
            "providers": {
                "deepseek": {"count": 0, "size": 0},
                "claude": {"count": 0, "size": 0},
                "unknown": {"count": 0, "size": 0}
            }
        }
        
        for file_path in cache_files:
            # Get file size
            file_size = os.path.getsize(file_path)
            stats["total"]["total_size"] += file_size
            
            # Get file modification time
            mod_time = os.path.getmtime(file_path)
            stats["total"]["oldest_entry"] = min(stats["total"]["oldest_entry"], mod_time)
            stats["total"]["newest_entry"] = max(stats["total"]["newest_entry"], mod_time)
            
            # Determine provider from model name in cache file
            try:
                with open(file_path, 'r') as f:
                    cache_data = json.load(f)
                    model = cache_data.get("model", "").lower()
                    
                    if "deepseek" in model:
                        provider = "deepseek"
                    elif "claude" in model:
                        provider = "claude"
                    else:
                        provider = "unknown"
                    
                    stats["providers"][provider]["count"] += 1
                    stats["providers"][provider]["size"] += file_size
            except:
                stats["providers"]["unknown"]["count"] += 1
                stats["providers"]["unknown"]["size"] += file_size
        
        # Convert inf to None if no files found
        if stats["total"]["oldest_entry"] == float('inf'):
            stats["total"]["oldest_entry"] = None
        
        # Convert 0 to None if no files found
        if stats["total"]["newest_entry"] == 0 and stats["total"]["entry_count"] == 0:
            stats["total"]["newest_entry"] = None
        
        return stats

# Create a global cache instance
llm_cache = LLMResponseCache() 