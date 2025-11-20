"""
317AK平台实现
提供随机自拍图片和多个视频系列API
"""
import httpx
from typing import List, Optional, Dict, Any
from ..platform_base import PlatformBase, MediaResource


# API错误码映射
ERROR_CODES = {
    200: "请求成功",
    203: "秘钥错误或不存在",
    204: "服务器错误",
    211: "接口不存在",
    212: "当前接口已下架",
    213: "当前接口正处于审核期",
    214: "API本地文件不存在，请联系管理员检查",
    215: "管理员设置当前接口必须携带ckey请求！",
    216: "付费接口请携带ckey请求！",
    217: "ckey不存在！",
    218: "当前ckey无权限调用此接口，请将此接口添加到ckey调用能力中后重试！",
    219: "访问频率超过限制！请稍后重试！",
    220: "本地API逻辑错误！请联系管理员检查！",
    221: "状态码与管理员配置的状态码不一致，请联系管理员！",
    222: "禁止访问！请联系管理员 (已被加入黑名单)",
    223: "积分不足！请充值后重试",
    224: "余额不足！请充值后重试",
    225: "您已设置仅白名单ip访问！请将当前ip添加到白名单中"
}


class AK317Platform(PlatformBase):
    """317AK平台实现"""
    
    def __init__(self):
        super().__init__("ak317")
        
        # API映射：API标识 -> (URL, 标题, 媒体类型)
        self.api_map = {
            "zptp": ("https://api.317ak.cn/api/wztp/zptp", "随机自拍图片", "image"),
            "qmtj": ("http://api.317ak.cn/api/sp/qmtj", "倾梦推荐视频", "video"),
            "mxny": ("http://api.317ak.cn/api/sp/mxny", "猫系女友系列视频", "video"),
            "slxl": ("http://api.317ak.cn/api/sp/slxl", "少萝系列视频", "video"),
            "ndxl": ("http://api.317ak.cn/api/sp/ndxl", "女大学生系列视频", "video"),
            "mncd": ("http://api.317ak.cn/api/sp/mncd", "美女穿搭视频", "video"),
            "rwxl": ("http://api.317ak.cn/api/sp/rwxl", "热舞系列视频", "video"),
            "smwx": ("http://api.317ak.cn/api/sp/smwx", "双马尾系列视频", "video"),
            "ywxl": ("http://api.317ak.cn/api/sp/ywxl", "渔网系列视频", "video"),
            "slmm": ("http://api.317ak.cn/api/sp/slmm", "少萝妹妹系列视频", "video"),
            "cqng": ("http://api.317ak.cn/api/sp/cqng", "纯情女高系列视频", "video"),
            "jpyz": ("http://api.317ak.cn/api/sp/jpyz", "极品狱卒系列视频", "video"),
            "yzmt": ("http://api.317ak.cn/api/sp/yzmt", "玉足美腿系列视频", "video"),
            "qcxl": ("http://api.317ak.cn/api/sp/qcxl", "清纯系列视频", "video"),
            "cosxl": ("http://api.317ak.cn/api/sp/cosxl", "COS系列视频", "video"),
            "llxl": ("http://api.317ak.cn/api/sp/llxl", "萝莉系列视频", "video"),
            "wmsc": ("http://api.317ak.cn/api/sp/wmsc", "完美身材系列视频", "video"),
            "dxbz": ("http://api.317ak.cn/api/sp/dxbz", "蹲下变装系列视频", "video"),
            "ddxl": ("http://api.317ak.cn/api/sp/ddxl", "吊带系列视频", "video"),
            "hssp": ("http://api.317ak.cn/api/sp/hssp", "黑丝系列视频", "video"),
            "npxl": ("http://api.317ak.cn/api/sp/npxl", "女仆系列视频", "video"),
            "ycyy": ("http://api.317ak.cn/api/sp/ycyy", "又纯又欲系列视频", "video"),
            "sqxl": ("http://api.317ak.cn/api/sp/sqxl", "甩裙系列视频", "video"),
            "bssp": ("http://api.317ak.cn/api/sp/bssp", "白丝系列视频", "video"),
            "hbss": ("http://api.317ak.cn/api/sp/hbss", "黑白双煞系列视频", "video"),
            "myxl": ("http://api.317ak.cn/api/sp/myxl", "慢摇系列视频", "video")
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
        try:
            data = response.json()
            # 检查响应中是否有code字段
            code = data.get("code")
            if code and code in ERROR_CODES:
                return f"[错误码 {code}] {ERROR_CODES[code]}"
            # 检查是否有msg或message字段
            msg = data.get("msg") or data.get("message") or data.get("error")
            if msg:
                return f"API错误: {msg}"
        except (ValueError, KeyError):
            pass
        
        # 如果无法解析JSON，返回HTTP状态码信息
        return f"HTTP {response.status_code}: {response.text[:200]}"
    
    async def _get_random_image(self, ckey: str) -> MediaResource:
        """
        获取随机自拍图片
        
        Args:
            ckey: API密钥
        
        Returns:
            MediaResource对象
        """
        params = {
            "type": "json",
            "ckey": ckey
        }
        
        # 使用api_map中的zptp API
        api_url, title, _ = self.api_map["zptp"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                api_url,
                params=params
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = self._parse_error_response(response)
                raise Exception(f"图片API请求失败: {error_msg}")
            
            data = response.json()
            
            # 检查响应中的错误码
            code = data.get("code")
            if code and code != 200:
                error_msg = ERROR_CODES.get(code, f"未知错误码: {code}")
                raise Exception(f"[错误码 {code}] {error_msg}")
            
            # 解析响应
            image_url = data.get("text", "")
            if not image_url:
                raise Exception("API返回的图片URL为空")
            
            return MediaResource(
                url=image_url,
                media_type="image",
                title="随机自拍图片",
                metadata={"source": "ak317", "api": "zptp"}
            )
    
    async def _get_video_from_api(
        self,
        ckey: str,
        api_url: str,
        title: str,
        api_id: str
    ) -> MediaResource:
        """
        从指定API获取视频
        
        Args:
            ckey: API密钥
            api_url: API地址
            title: 视频标题
            api_id: API标识
        
        Returns:
            MediaResource对象
        """
        params = {
            "ckey": ckey
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                api_url,
                params=params
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = self._parse_error_response(response)
                raise Exception(f"视频API请求失败: {error_msg}")
            
            # 检查Content-Type
            content_type = response.headers.get("content-type", "").lower()
            
            # 如果返回的是JSON错误响应
            if "application/json" in content_type or "text/json" in content_type:
                try:
                    data = response.json()
                    code = data.get("code")
                    if code and code != 200:
                        error_msg = ERROR_CODES.get(code, f"未知错误码: {code}")
                        raise Exception(f"[错误码 {code}] {error_msg}")
                    # 如果JSON中有URL字段
                    video_url = data.get("url") or data.get("text") or data.get("video_url")
                    if video_url:
                        return MediaResource(
                            url=video_url,
                            media_type="video",
                            title=title,
                            metadata={"source": "ak317", "api": api_id}
                        )
                except (ValueError, KeyError):
                    pass
            
            # 如果返回的是视频文件（二进制数据）
            if "video" in content_type:
                # 使用请求URL作为视频URL（如果API支持直接访问）
                video_url = str(response.url)
                return MediaResource(
                    url=video_url,
                    media_type="video",
                    title=title,
                    metadata={
                        "source": "ak317",
                        "api": api_id,
                        "content_type": content_type,
                        "size": len(response.content)
                    }
                )
            
            # 如果无法确定类型，尝试使用响应URL
            video_url = str(response.url)
            return MediaResource(
                url=video_url,
                media_type="video",
                title=title,
                metadata={"source": "ak317", "api": api_id, "content_type": content_type}
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
        config = config or {}
        ckey = config.get("ckey", "")
        
        if not ckey:
            raise Exception("缺少必需的配置参数: ckey")
        
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
            if api_media_type == "image":
                result = await self._get_random_image(ckey)
            else:  # video
                result = await self._get_video_from_api(ckey, api_url, title, api_id)
            
            return [result]
        except httpx.HTTPStatusError as e:
            error_msg = self._parse_error_response(e.response)
            raise Exception(f"API请求失败: {error_msg}")
        except httpx.HTTPError as e:
            raise Exception(f"API请求失败: {str(e)}")
        except Exception as e:
            # 如果已经是我们自定义的异常，直接抛出
            if isinstance(e, Exception) and ("API" in str(e) or "关键词" in str(e)):
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

