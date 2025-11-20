"""
缓存管理模块
负责缓存API响应结果，失败时使用缓存
支持本地文件持久化，按关键词分类存储
"""
import time
import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
from threading import RLock
from astrbot.api import logger


class CacheManager:
    """缓存管理器（支持本地文件持久化）"""
    
    def __init__(self, default_ttl: int = 3600, cache_dir: Optional[str] = None):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认缓存过期时间（秒），默认1小时
            cache_dir: 缓存目录路径，如果为None则使用默认路径
        """
        self._cache: Dict[str, Dict[str, Any]] = {}  # 内存缓存，用于快速访问
        self._lock = RLock()
        self.default_ttl = default_ttl
        
        # 设置缓存目录
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # 默认使用插件目录下的 cache 文件夹
            plugin_dir = Path(__file__).parent
            self.cache_dir = plugin_dir / "cache"
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已有缓存到内存
        self._load_cache_from_disk()
    
    def _get_cache_key(self, query: str, media_type: str, platform: str) -> str:
        """生成缓存key"""
        return f"{query}:{media_type}:{platform}"
    
    def _sanitize_filename(self, text: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            text: 原始文本
        
        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')
        # 限制长度，避免文件名过长
        if len(text) > 100:
            # 如果太长，使用哈希值
            text = hashlib.md5(text.encode('utf-8')).hexdigest()
        return text
    
    def _get_cache_file_path(self, query: str, media_type: str, platform: str) -> Path:
        """
        获取缓存文件路径（按关键词分类）
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
        
        Returns:
            缓存文件路径
        """
        # 按关键词创建子目录
        query_dir = self._sanitize_filename(query)
        query_cache_dir = self.cache_dir / query_dir
        query_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件名：{media_type}_{platform}.json
        filename = f"{media_type}_{platform}.json"
        return query_cache_dir / filename
    
    def _load_cache_from_disk(self):
        """从磁盘加载所有缓存到内存"""
        if not self.cache_dir.exists():
            return
        
        current_time = time.time()
        loaded_count = 0
        
        # 遍历所有关键词目录
        for query_dir in self.cache_dir.iterdir():
            if not query_dir.is_dir():
                continue
            
            # 遍历该关键词目录下的所有缓存文件
            for cache_file in query_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)
                    
                    # 检查是否过期
                    expires_at = cache_entry.get("expires_at", 0)
                    if current_time > expires_at:
                        # 过期，删除文件
                        cache_file.unlink()
                        continue
                    
                    # 从缓存文件中读取 query（保存时已添加）
                    query = cache_entry.get("query")
                    if not query:
                        # 如果没有 query 字段，从目录名解析（兼容旧格式）
                        query = query_dir.name
                    
                    # 从文件名解析 media_type 和 platform
                    filename = cache_file.stem  # 去掉 .json
                    parts = filename.split('_', 1)
                    if len(parts) == 2:
                        media_type, platform = parts
                        key = self._get_cache_key(query, media_type, platform)
                        self._cache[key] = cache_entry
                        loaded_count += 1
                except Exception as e:
                    # 文件损坏，删除
                    try:
                        cache_file.unlink()
                    except:
                        pass
        
        if loaded_count > 0:
            logger.info(f"已从磁盘加载 {loaded_count} 个缓存项")
    
    def _save_cache_to_disk(self, query: str, media_type: str, platform: str, cache_entry: Dict[str, Any]):
        """
        保存缓存到磁盘
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
            cache_entry: 缓存条目
        """
        cache_file = self._get_cache_file_path(query, media_type, platform)
        
        try:
            # 在缓存条目中添加 query 信息，方便后续读取
            cache_entry_with_query = cache_entry.copy()
            cache_entry_with_query["query"] = query
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry_with_query, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 保存失败，记录错误但不影响功能
            logger.warning(f"保存缓存到磁盘失败: {e}")
    
    def _delete_cache_file(self, query: str, media_type: str, platform: str):
        """
        删除缓存文件
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
        """
        cache_file = self._get_cache_file_path(query, media_type, platform)
        try:
            if cache_file.exists():
                cache_file.unlink()
                # 如果目录为空，也删除目录
                try:
                    if cache_file.parent.exists() and not any(cache_file.parent.iterdir()):
                        cache_file.parent.rmdir()
                except:
                    pass
        except Exception as e:
            logger.warning(f"删除缓存文件失败: {e}")
    
    def has_cache(self, query: str, media_type: str, platform: str) -> bool:
        """
        检查是否有缓存（先检查内存，再检查磁盘）
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
        
        Returns:
            是否有有效缓存
        """
        key = self._get_cache_key(query, media_type, platform)
        current_time = time.time()
        
        with self._lock:
            # 先检查内存缓存
            if key in self._cache:
                cache_entry = self._cache[key]
                # 检查是否过期
                if current_time > cache_entry.get("expires_at", 0):
                    del self._cache[key]
                    self._delete_cache_file(query, media_type, platform)
                    return False
                return True
            
            # 内存中没有，检查磁盘
            cache_file = self._get_cache_file_path(query, media_type, platform)
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)
                    
                    # 检查是否过期
                    if current_time > cache_entry.get("expires_at", 0):
                        self._delete_cache_file(query, media_type, platform)
                        return False
                    
                    # 未过期，加载到内存
                    self._cache[key] = cache_entry
                    return True
                except Exception:
                    # 文件损坏，删除
                    self._delete_cache_file(query, media_type, platform)
                    return False
            
            return False
    
    def get_cache(self, query: str, media_type: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果（从内存或磁盘）
        
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
            
            # has_cache 已经确保缓存存在且未过期
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
        设置缓存（同时保存到内存和磁盘）
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            platform: 平台名称
            data: 要缓存的数据
            ttl: 缓存过期时间（秒），如果为None则使用默认值
        """
        key = self._get_cache_key(query, media_type, platform)
        ttl = ttl or self.default_ttl
        
        cache_entry = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
        
        with self._lock:
            # 保存到内存
            self._cache[key] = cache_entry
            # 保存到磁盘
            self._save_cache_to_disk(query, media_type, platform, cache_entry)
    
    def clear_cache(self):
        """清空所有缓存（内存和磁盘）"""
        with self._lock:
            # 清空内存缓存
            self._cache.clear()
            
            # 删除所有缓存文件
            if self.cache_dir.exists():
                for item in self.cache_dir.iterdir():
                    if item.is_dir():
                        # 删除目录及其内容
                        import shutil
                        try:
                            shutil.rmtree(item)
                        except Exception as e:
                            logger.warning(f"删除缓存目录失败 {item}: {e}")
    
    def clear_expired(self):
        """清理过期的缓存（内存和磁盘）"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            # 清理内存中的过期缓存
            for key, entry in list(self._cache.items()):
                if current_time > entry.get("expires_at", 0):
                    expired_keys.append(key)
                    del self._cache[key]
        
        # 清理磁盘中的过期缓存
        if self.cache_dir.exists():
            for query_dir in self.cache_dir.iterdir():
                if not query_dir.is_dir():
                    continue
                
                for cache_file in query_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_entry = json.load(f)
                        
                        if current_time > cache_entry.get("expires_at", 0):
                            # 过期，删除文件
                            cache_file.unlink()
                            # 如果目录为空，删除目录
                            try:
                                if not any(query_dir.iterdir()):
                                    query_dir.rmdir()
                            except:
                                pass
                    except Exception:
                        # 文件损坏，删除
                        try:
                            cache_file.unlink()
                        except:
                            pass

