"""
关键词注册表模块
管理平台到关键词的映射，提供相似度匹配功能
支持注册(关键词, api_id, media_type)三元组
"""
from typing import Dict, List, Set, Tuple, Optional
from difflib import SequenceMatcher
from threading import RLock


class KeywordRegistry:
    """关键词注册表"""
    
    def __init__(self, similarity_threshold: float = 0.5):
        """
        初始化关键词注册表
        
        Args:
            similarity_threshold: 相似度阈值，默认0.5（50%相似度）
        """
        # 平台 -> [(关键词, api_id, media_type), ...]
        self._platform_apis: Dict[str, List[Tuple[str, str, str]]] = {}
        # 所有关键词的集合（用于快速查找和错误提示）
        self._all_keywords: Set[str] = set()
        self._lock = RLock()
        self.similarity_threshold = similarity_threshold
    
    def register(self, platform: str, keyword: str, api_id: str, media_type: str):
        """
        平台注册关键词和API的关联
        
        Args:
            platform: 平台名称
            keyword: 关键词（通常是api_map中的标题）
            api_id: API标识
            media_type: 媒体类型（image/video/audio）
        """
        with self._lock:
            if platform not in self._platform_apis:
                self._platform_apis[platform] = []
            
            keyword = keyword.strip()
            if keyword:
                self._platform_apis[platform].append((keyword, api_id, media_type))
                self._all_keywords.add(keyword)
    
    def unregister(self, platform: str):
        """
        取消注册平台的所有关键词和API
        
        Args:
            platform: 平台名称
        """
        with self._lock:
            if platform in self._platform_apis:
                # 从所有关键词集合中移除该平台的关键词
                for keyword, _, _ in self._platform_apis[platform]:
                    # 检查是否还有其他平台使用该关键词
                    used_by_others = any(
                        any(k == keyword for k, _, _ in self._platform_apis[p])
                        for p in self._platform_apis
                        if p != platform
                    )
                    if not used_by_others:
                        self._all_keywords.discard(keyword)
                
                del self._platform_apis[platform]
    
    def _calculate_similarity(self, query: str, keyword: str) -> float:
        """
        计算两个字符串的相似度（支持部分匹配）
        
        Args:
            query: 查询字符串
            keyword: 关键词
        
        Returns:
            相似度（0.0-1.0）
        """
        query_lower = query.lower()
        keyword_lower = keyword.lower()
        
        # 1. 精确匹配
        if query_lower == keyword_lower:
            return 1.0
        
        # 2. 部分匹配：query包含keyword或keyword包含query
        if keyword_lower in query_lower:
            # query包含keyword（完整关键词），相似度 = keyword长度 / query长度，但至少0.8
            ratio = len(keyword_lower) / len(query_lower) if query_lower else 0.0
            return max(ratio, 0.8)  # 完整包含时给予高相似度
        
        if query_lower in keyword_lower:
            # keyword包含query（查询是关键词的一部分），这是最常见的情况
            # 相似度基于包含比例，但给予更高的权重
            base_ratio = len(query_lower) / len(keyword_lower) if keyword_lower else 0.0
            # 如果query长度>=2且包含在keyword中，至少给予0.7的相似度
            # 如果query长度>=3，给予0.8的相似度
            if len(query_lower) >= 3:
                return max(base_ratio, 0.8)
            elif len(query_lower) >= 2:
                return max(base_ratio, 0.7)
            else:
                # 单字符匹配，使用基础比例但至少0.5
                return max(base_ratio, 0.5)
        
        # 3. 使用SequenceMatcher计算整体相似度
        return SequenceMatcher(None, query_lower, keyword_lower).ratio()
    
    def find_matching_apis(
        self,
        query: str,
        available_platforms: List[str] = None,
        media_type: str = "all"
    ) -> List[Tuple[str, str, str]]:
        """
        查找匹配关键词的API列表（使用相似度匹配）
        
        Args:
            query: 查询字符串
            available_platforms: 可用的平台列表，如果为None则搜索所有平台
            media_type: 媒体类型过滤（image/video/audio/all）
        
        Returns:
            匹配的API列表，每个元素为(platform, api_id, media_type)三元组
        """
        with self._lock:
            query = query.strip().lower()
            if not query:
                return []
            
            # 如果指定了可用平台列表，只在这些平台中搜索
            platforms_to_search = available_platforms or list(self._platform_apis.keys())
            
            matching_apis = []
            
            for platform in platforms_to_search:
                if platform not in self._platform_apis:
                    continue
                
                # 遍历该平台的所有API
                for keyword, api_id, api_media_type in self._platform_apis[platform]:
                    # 检查媒体类型是否匹配
                    if media_type != "all" and media_type != api_media_type:
                        continue
                    
                    # 计算相似度
                    similarity = self._calculate_similarity(query, keyword)
                    
                    # 如果相似度达到阈值，添加到匹配列表
                    if similarity >= self.similarity_threshold:
                        matching_apis.append((platform, api_id, api_media_type))
            
            return matching_apis
    
    def get_keywords_for_platform(self, platform: str) -> List[str]:
        """
        获取指定平台的所有关键词
        
        Args:
            platform: 平台名称
        
        Returns:
            关键词列表
        """
        with self._lock:
            if platform not in self._platform_apis:
                return []
            return [keyword for keyword, _, _ in self._platform_apis[platform]]
    
    def get_all_keywords(self) -> List[str]:
        """
        获取所有已注册的关键词
        
        Returns:
            关键词列表
        """
        with self._lock:
            return list(self._all_keywords)
    
    def get_all_platforms(self) -> List[str]:
        """
        获取所有已注册的平台
        
        Returns:
            平台名称列表
        """
        with self._lock:
            return list(self._platform_apis.keys())
    
    def has_keywords(self, platform: str) -> bool:
        """
        检查平台是否已注册关键词
        
        Args:
            platform: 平台名称
        
        Returns:
            是否已注册
        """
        with self._lock:
            return platform in self._platform_apis and len(self._platform_apis[platform]) > 0


# 全局关键词注册表实例
_registry_instance: KeywordRegistry = None


def get_registry() -> KeywordRegistry:
    """获取全局关键词注册表实例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = KeywordRegistry()
    return _registry_instance

