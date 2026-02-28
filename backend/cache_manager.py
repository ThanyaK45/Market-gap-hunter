import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class CacheManager:
    """Simple file-based cache manager for API responses"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _generate_key(self, **kwargs) -> str:
        """Generate cache key from parameters"""
        # Sort keys for consistent hashing
        sorted_params = sorted(kwargs.items())
        param_string = json.dumps(sorted_params, sort_keys=True)
        return hashlib.sha256(param_string.encode()).hexdigest()
    
    def get(self, **kwargs) -> Optional[Dict[Any, Any]]:
        """Get cached data if exists and not expired"""
        cache_key = self._generate_key(**kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_file.unlink()  # Delete expired cache
                return None
            
            return cached_data['data']
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    def set(self, data: Dict[Any, Any], **kwargs) -> None:
        """Save data to cache"""
        cache_key = self._generate_key(**kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'params': kwargs,
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def clear_expired(self) -> int:
        """Clear all expired cache files"""
        cleared = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    cleared += 1
            except Exception:
                pass
        
        return cleared
    
    def clear_all(self) -> int:
        """Clear all cache files"""
        cleared = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                cleared += 1
            except Exception:
                pass
        
        return cleared
