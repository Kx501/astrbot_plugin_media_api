"""
缓存管理模块
负责缓存API响应结果，失败时使用缓存
"""
import time
from typing import Dict, Optional, Any
from threading import RLock


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认缓存过期时间（秒），默认1小时
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()
        self.default_ttl = default_ttl
    
    def _get_cache_key(self, query: str, media_type: str, platform: str) -> str:
        """生成缓存key"""
        return f"{query}:{media_type}:{platform}"
    
    def has_cache(self, query: str, media_type: str, platform: str) -> bool:
        """
        检查是否有缓存
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
        
        Returns:
            是否有有效缓存
        """
        key = self._get_cache_key(query, media_type, platform)
        with self._lock:
            if key not in self._cache:
                return False
            
            cache_entry = self._cache[key]
            # 检查是否过期
            if time.time() > cache_entry.get("expires_at", 0):
                del self._cache[key]
                return False
            
            return True
    
    def get_cache(self, query: str, media_type: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
        
        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        key = self._get_cache_key(query, media_type, platform)
        with self._lock:
            if not self.has_cache(query, media_type, platform):
                return None
            
            return self._cache[key].get("data")
    
    def set_cache(
        self,
        query: str,
        media_type: str,
        platform: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        设置缓存
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
            data: 要缓存的数据
            ttl: 缓存过期时间（秒），如果为None则使用默认值
        """
        key = self._get_cache_key(query, media_type, platform)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            self._cache[key] = {
                "data": data,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
    
    def clear_cache(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def clear_expired(self):
        """清理过期的缓存"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry.get("expires_at", 0)
            ]
            for key in expired_keys:
                del self._cache[key]

