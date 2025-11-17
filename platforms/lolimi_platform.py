"""
Lolimi平台实现
提供随机视频API
"""
import httpx
from typing import List, Optional, Dict, Any
from ..platform_base import PlatformBase, MediaResource


# API错误码映射
ERROR_CODES = {
    400: "请求错误！",
    403: "请求被服务器拒绝！",
    404: "接口不存在！",
    405: "客户端请求的方法被禁止！",
    408: "请求时间过长！",
    500: "服务器内部出现错误！",
    501: "服务器不支持请求的功能，无法完成请求！",
    503: "系统维护中！"
}


class LolimiPlatform(PlatformBase):
    """Lolimi平台实现"""
    
    def __init__(self):
        super().__init__("lolimi")
        
        # API映射：API标识 -> (URL, 标题, 媒体类型)
        self.api_map = {
            "xjj": ("https://api.lolimi.cn/API/xjj/xjj.php", "高质量小姐姐视频", "video")
        }
        
        # 从api_map自动注册所有API到全局注册表
        self.register_apis_from_map(self.api_map)
    
    def _parse_error_response(self, response: httpx.Response) -> str:
        """
        解析错误响应
        
        Args:
            response: HTTP响应对象
        
        Returns:
            错误信息字符串
        """
        status_code = response.status_code
        if status_code in ERROR_CODES:
            return f"[错误码 {status_code}] {ERROR_CODES[status_code]}"
        
        # 尝试解析响应文本
        try:
            text = response.text[:200]
            if text:
                return f"HTTP {status_code}: {text}"
        except:
            pass
        
        return f"HTTP {status_code}: 请求失败"
    
    async def _get_random_video(self, api_url: str) -> MediaResource:
        """
        获取随机视频
        
        Args:
            api_url: API地址
        
        Returns:
            MediaResource对象
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # 使用GET方法请求（也支持POST，但GET更简单）
            response = await client.get(api_url)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = self._parse_error_response(response)
                raise Exception(f"视频API请求失败: {error_msg}")
            
            # 检查Content-Type
            content_type = response.headers.get("content-type", "").lower()
            
            # 如果返回的是视频文件（二进制数据）
            if "video" in content_type or "mp4" in content_type:
                # 使用请求URL作为视频URL
                video_url = str(response.url)
                return MediaResource(
                    url=video_url,
                    media_type="video",
                    title="随机视频",
                    metadata={
                        "source": "lolimi",
                        "api": "xjj",
                        "content_type": content_type,
                        "size": len(response.content) if response.content else None
                    }
                )
            
            # 如果返回的是错误响应（JSON或文本）
            if "application/json" in content_type or "text" in content_type:
                try:
                    data = response.json()
                    error_msg = data.get("error") or data.get("message") or str(data)
                    raise Exception(f"API返回错误: {error_msg}")
                except (ValueError, KeyError):
                    error_text = response.text[:200]
                    raise Exception(f"API返回错误: {error_text}")
            
            # 如果无法确定类型，尝试使用响应URL
            video_url = str(response.url)
            return MediaResource(
                url=video_url,
                media_type="video",
                title="随机视频",
                metadata={
                    "source": "lolimi",
                    "api": "xjj",
                    "content_type": content_type
                }
            )
    
    async def search_media(
        self,
        query: str,
        media_type: str = "all",
        config: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        api_id: Optional[str] = None
    ) -> List[MediaResource]:
        """
        搜索媒体资源
        
        注意：关键词匹配已由全局KeywordRegistry处理，api_id由MCP服务器传入。
        
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
        
        # 获取API信息
        api_url, title, api_media_type = self.api_map[api_id]
        
        # 检查媒体类型是否匹配
        if media_type != "all" and media_type != api_media_type:
            raise Exception(f"API '{title}'对应{api_media_type}类型，但请求的是{media_type}类型")
        
        # 调用对应的API
        try:
            result = await self._get_random_video(api_url)
            # 更新标题为匹配到的API标题
            result.title = title
            return [result]
        except httpx.HTTPStatusError as e:
            error_msg = self._parse_error_response(e.response)
            raise Exception(f"API请求失败: {error_msg}")
        except httpx.HTTPError as e:
            raise Exception(f"API请求失败: {str(e)}")
        except Exception as e:
            # 如果已经是我们自定义的异常，直接抛出
            if isinstance(e, Exception) and ("API" in str(e) or "关键词" in str(e) or "不支持" in str(e)):
                raise
            raise Exception(f"获取媒体资源失败: {str(e)}")
    
    async def get_media_by_id(
        self,
        media_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaResource]:
        """
        根据ID获取媒体资源
        
        注意：此API不支持根据ID获取，总是返回None
        """
        return None
    
    def get_available_apis(self) -> List[str]:
        """
        返回该平台提供的API列表
        
        Returns:
            API名称列表
        """
        return ["search"]
    
    def get_supported_media_types(self) -> List[str]:
        """
        返回平台支持的媒体类型列表
        
        Returns:
            支持的媒体类型列表
        """
        # 从api_map中提取所有唯一的媒体类型
        media_types = set()
        for _, _, media_type in self.api_map.values():
            media_types.add(media_type)
        return list(media_types)

