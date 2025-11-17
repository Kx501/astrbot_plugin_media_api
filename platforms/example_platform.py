"""
示例平台实现
作为其他平台实现的模板
"""
import httpx
from typing import List, Optional, Dict, Any
from ..platform_base import PlatformBase, MediaResource, MediaType


class ExamplePlatform(PlatformBase):
    """示例平台实现"""
    
    def __init__(self):
        super().__init__("example")
        self.base_url = "https://api.example.com"
        
        # API映射：API标识 -> (URL, 标题, 媒体类型)
        self.api_map = {
            "search_image": (f"{self.base_url}/search", "示例图片搜索", "image"),
            "search_video": (f"{self.base_url}/search", "示例视频搜索", "video"),
            "search_all": (f"{self.base_url}/search", "示例媒体搜索", "all")
        }
        
        # 从api_map自动注册所有API到全局注册表
        self.register_apis_from_map(self.api_map)
    
    async def search_media(
        self,
        query: str,
        media_type: str = "all",
        config: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        api_id: Optional[str] = None
    ) -> List[MediaResource]:
        """
        搜索媒体资源示例
        
        注意：这是一个模板实现，实际使用时需要替换为真实的API调用
        
        Args:
            query: 搜索关键词（保留用于日志）
            media_type: 媒体类型
            config: 平台配置
            limit: 返回结果数量限制
            api_id: API标识（由MCP服务器传入，如果为None则抛出异常）
        """
        if not api_id or api_id not in self.api_map:
            available_apis = "、".join([title for _, title, _ in self.api_map.values()])
            raise Exception(f"平台{self.name}未找到API标识{api_id}，可用API：{available_apis}")
        
        config = config or {}
        api_key = config.get("api_key", "")
        
        # 获取API信息
        api_url, title, api_media_type = self.api_map[api_id]
        
        # 构建请求参数
        params = {
            "q": query,
            "type": media_type if media_type != "all" else "",
            "limit": limit
        }
        
        if api_key:
            params["api_key"] = api_key
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    api_url,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # 解析响应并转换为MediaResource列表
                results = []
                for item in data.get("results", [])[:limit]:
                    media_resource = MediaResource(
                        url=item.get("url", ""),
                        media_type=item.get("type", api_media_type),
                        title=item.get("title"),
                        description=item.get("description"),
                        thumbnail=item.get("thumbnail"),
                        width=item.get("width"),
                        height=item.get("height"),
                        metadata=item.get("metadata", {})
                    )
                    results.append(media_resource)
                
                return results
        except httpx.HTTPError as e:
            # 处理HTTP错误
            raise Exception(f"API请求失败: {str(e)}")
        except Exception as e:
            # 处理其他错误
            raise Exception(f"搜索媒体失败: {str(e)}")
    
    async def get_media_by_id(
        self,
        media_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaResource]:
        """
        根据ID获取媒体资源示例
        """
        config = config or {}
        api_key = config.get("api_key", "")
        
        params = {}
        if api_key:
            params["api_key"] = api_key
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/media/{media_id}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # 转换为MediaResource
                return MediaResource(
                    url=data.get("url", ""),
                    media_type=data.get("type", "image"),
                    title=data.get("title"),
                    description=data.get("description"),
                    thumbnail=data.get("thumbnail"),
                    width=data.get("width"),
                    height=data.get("height"),
                    metadata=data.get("metadata", {})
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"API请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取媒体失败: {str(e)}")
    
    def get_available_apis(self) -> List[str]:
        """
        返回该平台提供的API列表
        
        标准API名称：
        - "search": 搜索媒体资源（必需）
        - "get_by_id": 根据ID获取媒体资源（可选）
        - "download": 下载媒体资源（可选）
        
        注意：
        - 所有平台必须至少提供"search" API
        - API名称用于配置中的禁用规则（格式：平台名:api_id）
        - 例如：在配置中禁用该平台的search_image API，使用"example:search_image"
        
        Returns:
            API名称列表
        """
        return ["search", "get_by_id"]
    
    def get_supported_media_types(self) -> List[str]:
        """
        返回平台支持的媒体类型列表
        
        Returns:
            支持的媒体类型列表
        """
        # 从api_map中提取所有唯一的媒体类型
        media_types = set()
        for _, _, api_media_type in self.api_map.values():
            if api_media_type != "all":
                media_types.add(api_media_type)
        # 如果没有特定类型，返回所有类型
        return list(media_types) if media_types else ["image", "video", "audio"]

