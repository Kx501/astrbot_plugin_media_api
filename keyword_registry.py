"""
关键词注册表模块
管理平台到关键词的映射，提供BM25算法匹配功能
支持注册(关键词, api_id, media_type)三元组
"""
from typing import Dict, List, Set, Tuple, Optional
from threading import RLock
import re


class KeywordRegistry:
    """关键词注册表"""
    
    def __init__(self, similarity_threshold: float = 0.3, k1: float = 1.5, b: float = 0.75):
        """
        初始化关键词注册表
        
        Args:
            similarity_threshold: BM25得分阈值，默认0.3
            k1: BM25参数k1，控制词频饱和度，默认1.5
            b: BM25参数b，控制文档长度归一化，默认0.75
        """
        # 平台 -> [(关键词, api_id, media_type), ...]
        self._platform_apis: Dict[str, List[Tuple[str, str, str]]] = {}
        # 所有关键词的集合（用于快速查找和错误提示）
        self._all_keywords: Set[str] = set()
        self._lock = RLock()
        self.similarity_threshold = similarity_threshold
        self.k1 = k1
        self.b = b
        # 缓存：关键词 -> 分词列表
        self._keyword_tokens_cache: Dict[str, List[str]] = {}
    
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
    
    def _tokenize(self, text: str) -> List[str]:
        """
        对中文文本进行分词（简化版：字符级+词级）
        
        Args:
            text: 输入文本
        
        Returns:
            分词列表
        """
        text = text.lower().strip()
        if not text:
            return []
        
        # 如果已缓存，直接返回
        if text in self._keyword_tokens_cache:
            return self._keyword_tokens_cache[text]
        
        tokens = []
        # 提取所有中文字符和连续的非中文字符
        # 匹配中文字符、英文单词、数字
        pattern = r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+'
        matches = re.findall(pattern, text)
        
        # 对于中文和英文，同时添加字符级和词级token
        for match in matches:
            if re.match(r'[\u4e00-\u9fff]+', match):
                # 中文：添加完整词 + 每个字符
                tokens.append(match)  # 完整词
                # 对于短词（<=4），也添加字符级token以提高匹配度
                if len(match) <= 4:
                    for char in match:
                        tokens.append(char)
            elif re.match(r'[a-zA-Z]+', match):
                # 英文：添加完整单词
                tokens.append(match.lower())  # 完整单词（转小写）
                # 对于短单词（<=5），也添加所有可能的子串以提高部分匹配
                # 例如："cosxl" -> ["cosxl", "cosx", "cos", "osxl", "sxl", "xl"]
                if len(match) <= 5:
                    match_lower = match.lower()
                    # 添加所有长度>=2的前缀（用于部分匹配）
                    for i in range(2, len(match_lower)):
                        prefix = match_lower[:i]
                        if prefix not in tokens:
                            tokens.append(prefix)
            else:
                # 数字：作为整体添加
                tokens.append(match)
        
        # 缓存结果
        self._keyword_tokens_cache[text] = tokens
        return tokens
    
    def _calculate_bm25_score(self, query: str, keyword: str) -> float:
        """
        使用BM25算法计算查询和关键词的匹配得分
        
        Args:
            query: 查询字符串
            keyword: 关键词
        
        Returns:
            BM25得分（越高越匹配）
        """
        query_tokens = self._tokenize(query)
        keyword_tokens = self._tokenize(keyword)
        
        if not query_tokens or not keyword_tokens:
            return 0.0
        
        # 计算IDF（逆文档频率）
        # 简化版：使用词在关键词中的频率
        keyword_token_set = set(keyword_tokens)
        keyword_length = len(keyword_tokens)
        
        score = 0.0
        for token in query_tokens:
            if token in keyword_token_set:
                # 计算词频（TF）
                tf = keyword_tokens.count(token)
                
                # 简化的IDF：如果词在关键词中出现，给予较高权重
                # 对于完全匹配的词，给予更高权重
                if token == query or token == keyword:
                    idf = 2.0  # 完全匹配的权重
                elif len(token) >= 2:
                    idf = 1.5  # 多字符词的权重
                else:
                    idf = 0.5  # 单字符的权重
                
                # BM25公式（简化版，针对短文本优化）
                # score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (keyword_length / avg_length)))
                # 对于短文本，简化公式
                avg_length = 5  # 假设平均关键词长度为5
                normalization = 1 - self.b + self.b * (keyword_length / avg_length)
                bm25_tf = (tf * (self.k1 + 1)) / (tf + self.k1 * normalization)
                score += idf * bm25_tf
        
        # 归一化得分（除以查询词数量）
        if len(query_tokens) > 0:
            score = score / len(query_tokens)
        
        # 额外奖励：如果查询完全包含在关键词中，给予大幅加分
        query_lower = query.lower()
        keyword_lower = keyword.lower()
        if query_lower in keyword_lower:
            # 计算包含比例
            contain_ratio = len(query_lower) / len(keyword_lower)
            # 如果查询是关键词的主要部分（>=50%），给予大幅加分
            if contain_ratio >= 0.5:
                score += 2.0  # 大幅加分，确保能匹配到
            else:
                score += contain_ratio * 1.0  # 较小加分
        
        # 精确匹配给予最高分
        if query_lower == keyword_lower:
            score = 10.0
        
        return score
    
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
                    
                    # 使用BM25算法计算匹配得分
                    score = self._calculate_bm25_score(query, keyword)
                    
                    # 如果得分达到阈值，添加到匹配列表
                    if score >= self.similarity_threshold:
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

