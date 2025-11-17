"""
平台抽象基类
定义统一的平台接口和返回格式
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from .keyword_registry import get_registry


class MediaType(Enum):
    """媒体类型枚举"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ALL = "all"


class MediaResource:
    """媒体资源统一返回格式"""
    
    def __init__(
        self,
        url: str,
        media_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        thumbnail: Optional[str] = None,
        duration: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        self.media_type = media_type
        self.title = title
        self.description = description
        self.thumbnail = thumbnail
        self.duration = duration
        self.width = width
        self.height = height
        self.size = size
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "url": self.url,
            "type": self.media_type,
            "metadata": self.metadata
        }
        
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.thumbnail:
            result["thumbnail"] = self.thumbnail
        if self.duration is not None:
            result["duration"] = self.duration
        if self.width is not None:
            result["width"] = self.width
        if self.height is not None:
            result["height"] = self.height
        if self.size is not None:
            result["size"] = self.size
        
        return result


class PlatformBase(ABC):
    """平台抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
        self._keywords_registered = False
    
    def register_apis_from_map(self, api_map: Dict[str, tuple]):
        """
        从api_map自动注册所有API到全局注册表
        
        api_map格式：{api_id: (url, title, media_type), ...}
        
        Args:
            api_map: API映射字典
        """
        registry = get_registry()
        for api_id, api_info in api_map.items():
            if len(api_info) >= 3:
                url, title, media_type = api_info[0], api_info[1], api_info[2]
                # 使用标题作为关键词注册
                registry.register(self.name, title, api_id, media_type)
        self._keywords_registered = True
    
    def get_keywords(self) -> List[str]:
        """
        获取平台已注册的关键词
        
        Returns:
            关键词列表
        """
        registry = get_registry()
        return registry.get_keywords_for_platform(self.name)
    
    def get_supported_media_types(self) -> List[str]:
        """
        返回平台支持的媒体类型列表
        
        子类可以重写此方法，或者通过api_map自动推导
        
        Returns:
            支持的媒体类型列表，例如：["image", "video"]
        """
        # 默认返回所有类型，子类可以重写
        return ["image", "video", "audio"]
    
    @abstractmethod
    async def search_media(
        self,
        query: str,
        media_type: str = "all",
        config: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[MediaResource]:
        """
        搜索媒体资源
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型 (image/video/audio/all)
            config: 平台配置（包含api_key等）
            limit: 返回结果数量限制
        
        Returns:
            媒体资源列表
        """
        pass
    
    @abstractmethod
    async def get_media_by_id(
        self,
        media_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaResource]:
        """
        根据ID获取媒体资源
        
        Args:
            media_id: 媒体ID
            config: 平台配置（包含api_key等）
        
        Returns:
            媒体资源，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_available_apis(self) -> List[str]:
        """
        返回该平台提供的API列表
        
        标准API名称：
        - "search": 搜索媒体资源（必需，所有平台都应该实现）
        - "get_by_id": 根据ID获取媒体资源（可选）
        - "download": 下载媒体资源（可选）
        - 其他平台特定API名称
        
        Returns:
            API名称列表，例如：["search", "get_by_id", "download"]
        
        注意：
        - 所有平台必须至少提供"search" API
        - API名称用于配置中的禁用规则（格式：平台名:API名）
        """
        pass
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        验证配置是否有效（可选实现）
        
        Args:
            config: 平台配置
        
        Returns:
            配置是否有效
        """
        return True  # 默认不验证，按需求

