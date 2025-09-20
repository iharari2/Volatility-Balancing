# =========================
# backend/infrastructure/cache/simulation_cache.py
# =========================
"""
Simulation result caching for performance optimization.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading

# Import SimulationResult locally to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from application.use_cases.simulation_uc import SimulationResult


@dataclass
class CacheEntry:
    """A cached simulation result."""
    result: 'SimulationResult'
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0


class SimulationCache:
    """Thread-safe cache for simulation results."""
    
    def __init__(self, max_size: int = 100, default_ttl_hours: int = 24):
        self.max_size = max_size
        self.default_ttl_hours = default_ttl_hours
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._access_order: list = []  # For LRU eviction
    
    def _generate_key(self, config: Dict[str, Any]) -> str:
        """Generate a cache key from simulation configuration."""
        # Create a normalized version of the config for consistent hashing
        normalized_config = {
            'ticker': config.get('ticker', '').upper(),
            'start_date': config.get('start_date', ''),
            'end_date': config.get('end_date', ''),
            'initial_cash': config.get('initial_cash', 0),
            'initial_asset_value': config.get('initial_asset_value', 0),
            'initial_asset_units': config.get('initial_asset_units', 0),
            'position_config': config.get('position_config', {}),
            'include_after_hours': config.get('include_after_hours', False),
        }
        
        # Sort the config to ensure consistent hashing
        config_str = json.dumps(normalized_config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def get(self, config: Dict[str, Any]) -> Optional['SimulationResult']:
        """Get a cached simulation result."""
        with self._lock:
            key = self._generate_key(config)
            
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if datetime.now() > entry.expires_at:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return None
            
            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            # Update hit count
            entry.hit_count += 1
            
            return entry.result
    
    def put(self, config: Dict[str, Any], result: 'SimulationResult', ttl_hours: Optional[int] = None) -> None:
        """Cache a simulation result."""
        with self._lock:
            key = self._generate_key(config)
            ttl = ttl_hours or self.default_ttl_hours
            
            # Create cache entry
            now = datetime.now()
            entry = CacheEntry(
                result=result,
                created_at=now,
                expires_at=now + timedelta(hours=ttl),
                hit_count=0
            )
            
            # Evict if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Store the entry
            self._cache[key] = entry
            if key not in self._access_order:
                self._access_order.append(key)
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._access_order:
            return
        
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def clear_expired(self) -> None:
        """Remove all expired entries."""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            now = datetime.now()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if now > entry.expires_at
            )
            
            total_hits = sum(entry.hit_count for entry in self._cache.values())
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'total_hits': total_hits,
                'max_size': self.max_size,
                'hit_rate': total_hits / max(total_entries, 1)
            }


# Global simulation cache
simulation_cache = SimulationCache(max_size=50, default_ttl_hours=12)
