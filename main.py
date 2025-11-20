"""
AstrBot专用MCP服务器入口
"""
import json
import random
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp
from .config_manager import ConfigManager
from .cache_manager import CacheManager
from .failure_tracker import FailureTracker
from .keyword_registry import get_registry
from .platforms import get_platform


@register("media_api", "Kx501", "媒体资源获取工具，用于调用第三方api获取资源，返回给LLM的工具", "v1.0.0", "https://github.com/Kx501/media_api")
class MediaApiTool(Star):
    """
    AstrBot 媒体API工具插件
    提供多平台媒体资源获取功能（图片/视频/音频）
    """
    def __init__(self, context: Context, config: AstrBotConfig = None):
        """插件初始化"""
        super().__init__(context)
        
        # 获取插件目录路径，用于配置文件路径
        plugin_dir = Path(__file__).parent
        config_path = plugin_dir / "config" / "config.json"
        
        # 初始化全局管理器
        self.config_manager = ConfigManager(str(config_path))
        self.cache_manager = CacheManager()
        self.failure_tracker = FailureTracker(self.config_manager)
        self.keyword_registry = get_registry()
        
        logger.info("媒体API工具插件已加载")

    @filter.llm_tool(name="get_media")
    async def get_media(self, event: AstrMessageEvent, query: str, media_type: str = "all") -> AsyncGenerator[MessageEventResult, None]:
        """
        用户想要图片/视频/音频时必须调用此工具，通过第三方API搜索并直接发送一条媒体资源。
        
        Args:
            query(string): 关键词，如"黑丝"、"cos"
            media_type(string): image/video/audio/all
        
        注意：此工具会直接发送媒体文件，而不是返回链接。
        """
        start_time = time.time()
        
        try:
            # 获取群组ID（如果存在）
            group_id = event.get_group_id()
            if group_id:
                group_id = str(group_id)
            else:
                group_id = None
            
            # 调用内部方法获取媒体资源
            result = await self._get_media_internal(query, media_type, group_id)
            
            elapsed_time = time.time() - start_time
            logger.info(f"媒体API工具调用完成，耗时 {elapsed_time:.2f}s")
            
            # 如果成功，发送媒体文件
            if "error" not in result:
                media_chain = []
                self._add_media_component(media_chain, result)
                if media_chain:  # 只有当媒体组件添加成功时才发送
                    yield event.chain_result(media_chain)
            else:
                # 如果失败，发送错误消息
                yield event.plain_result(f"获取媒体资源失败: {result['error']}")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"获取媒体资源时发生错误: {e}，耗时 {elapsed_time:.2f}s", exc_info=True)
            yield event.plain_result(f"获取媒体资源时发生内部错误: {str(e)}")

    async def _get_media_internal(
        self,
        query: str,
        media_type: str = "all",
        group_id: Optional[str] = None
    ) -> dict:
        """
        内部函数，用于获取媒体资源
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型，默认"all"
            group_id: 群组ID（可选）
        
        Returns:
            结果字典，包含url和type，或error
        """
        logger.info(f"get_media called: query={query}, media_type={media_type}, group_id={group_id}")
        
        try:
            # 1. 预处理：按权限过滤平台
            all_available_platforms = self.config_manager.get_available_platforms(group_id)
            if not all_available_platforms:
                error_msg = "没有可用的平台"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            logger.info(f"Available platforms after permission check: {all_available_platforms}")
            
            # 2. 过滤类型：只保留支持指定media_type的平台
            type_filtered_platforms = []
            for platform_name in all_available_platforms:
                platform_instance = get_platform(platform_name)
                if not platform_instance:
                    continue
                
                supported_types = platform_instance.get_supported_media_types()
                if media_type == "all" or media_type in supported_types:
                    type_filtered_platforms.append(platform_name)
            
            if not type_filtered_platforms:
                error_msg = f"没有支持{media_type}类型的平台"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            logger.info(f"Platforms after type filter ({media_type}): {type_filtered_platforms}")
            
            # 3. 匹配关键词（相似度匹配，返回(platform, api_id, media_type)三元组）
            matching_apis = self.keyword_registry.find_matching_apis(
                query=query,
                available_platforms=type_filtered_platforms,
                media_type=media_type
            )
            
            if not matching_apis:
                # 匹配失败，返回错误提示
                all_keywords = self.keyword_registry.get_all_keywords()
                if all_keywords:
                    # 如果关键词太多（超过20个），生成图片
                    if len(all_keywords) > 20:
                        # 关键词过多，返回关键词列表供文本显示
                        return {
                            "error": "未匹配到关键词",
                            "keywords": all_keywords,
                            "keywords_count": len(all_keywords)
                        }
                    
                    # 关键词较少时，使用文本
                    keywords_str = "、".join(all_keywords[:20])
                    if len(all_keywords) > 20:
                        keywords_str += f"等{len(all_keywords)}个关键词"
                    error_msg = f"未匹配到关键词，可用关键词：{keywords_str}"
                else:
                    error_msg = "未匹配到关键词，且没有已注册的关键词"
                logger.warning(f"Keyword matching failed for '{query}': {error_msg}")
                return {"error": error_msg}
            
            logger.info(f"Matched APIs: {matching_apis}")
            
            # 4. 过滤被禁用的API
            enabled_apis = []
            for platform, api_id, api_media_type in matching_apis:
                if self.config_manager.is_api_enabled(group_id, platform, api_id):
                    enabled_apis.append((platform, api_id, api_media_type))
            
            if not enabled_apis:
                error_msg = "所有匹配的API都已被禁用"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            logger.info(f"Enabled APIs after filter: {enabled_apis}")
            
            # 5. 随机选择一个API（全部平级）
            platform, api_id, api_media_type = random.choice(enabled_apis)
            logger.info(f"Selected: platform={platform}, api_id={api_id} (from {len(enabled_apis)} matched APIs)")
            
            # 6. 获取平台实例
            platform_instance = get_platform(platform)
            if not platform_instance:
                error_msg = f"平台 {platform} 不存在"
                logger.error(error_msg)
                return {"error": error_msg}
            
            # 7. 获取平台配置
            platform_config = self.config_manager.get_platform_config(platform)
            
            # 8. 调用平台API（传入api_id）
            try:
                results = await platform_instance.search_media(
                    query=query,
                    media_type=media_type,
                    config=platform_config,
                    limit=1,  # 只获取第一个结果
                    api_id=api_id  # 传入匹配到的api_id
                )
                
                if not results:
                    raise Exception("未找到结果")
                
                # 9. 只返回第一个结果（最简化格式）
                first_result = results[0]
                result = {
                    "url": first_result.url,
                    "type": first_result.media_type
                }
                
                # 10. 缓存结果（用于失败时的备用方案）
                self.cache_manager.set_cache(query, media_type, platform, result)
                logger.info(f"Successfully got media from {platform}, cached")
                
                # 11. 重置失败计数（使用api_id）
                self.failure_tracker.reset_failure(platform, api_id, group_id)
                
                return result
                
            except Exception as e:
                error_msg = f"API调用失败: {str(e)}"
                logger.error(f"{platform} API error: {error_msg}")
                
                # 12. 记录失败（使用api_id）
                self.failure_tracker.record_failure(platform, api_id, group_id)
                
                # 13. 尝试使用缓存（失败时的备用方案）
                cached_result = self.cache_manager.get_cache(query, media_type, platform)
                if cached_result:
                    logger.info(f"Using cached result after failure")
                    return cached_result
                
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"获取媒体资源失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    def _add_media_component(self, result_chain: List, media_data: dict):
        """
        添加媒体组件到消息链
        
        Args:
            result_chain: 消息链列表
            media_data: 包含 url 和 type 的字典
        """
        if "error" in media_data or "url" not in media_data or "type" not in media_data:
            return
        
        url_or_path = media_data["url"]
        media_type = media_data["type"]
        
        # 判断是 URL 还是文件路径
        is_url = url_or_path.startswith(("http://", "https://", "ftp://"))
        is_file = Path(url_or_path).exists() if not is_url else False
        
        # 根据类型和来源添加媒体组件
        try:
            if media_type == "image":
                if is_url:
                    result_chain.append(Comp.Image.fromURL(url_or_path))
                    logger.info(f"添加图片(URL): {url_or_path}")
                elif is_file:
                    result_chain.append(Comp.Image.fromFileSystem(url_or_path))
                    logger.info(f"添加图片(文件): {url_or_path}")
                else:
                    # 尝试作为 URL 处理（可能是相对路径或其他格式）
                    result_chain.append(Comp.Image.fromURL(url_or_path))
                    logger.info(f"添加图片(尝试URL): {url_or_path}")
            elif media_type == "video":
                if is_url:
                    result_chain.append(Comp.Video.fromURL(url_or_path))
                    logger.info(f"添加视频(URL): {url_or_path}")
                elif is_file:
                    result_chain.append(Comp.Video.fromFileSystem(path=url_or_path))
                    logger.info(f"添加视频(文件): {url_or_path}")
                else:
                    # 尝试作为 URL 处理
                    result_chain.append(Comp.Video.fromURL(url_or_path))
                    logger.info(f"添加视频(尝试URL): {url_or_path}")
            elif media_type == "audio":
                if is_url:
                    result_chain.append(Comp.Record(url=url_or_path, file=url_or_path))
                    logger.info(f"添加音频(URL): {url_or_path}")
                elif is_file:
                    result_chain.append(Comp.Record(file=url_or_path, url=url_or_path))
                    logger.info(f"添加音频(文件): {url_or_path}")
                else:
                    # 尝试作为 URL 处理
                    result_chain.append(Comp.Record(url=url_or_path, file=url_or_path))
                    logger.info(f"添加音频(尝试URL): {url_or_path}")
        except Exception as e:
            logger.error(f"添加媒体组件时发生错误: {e}", exc_info=True)

    @filter.command("测试媒体", alias={"test_media"})
    async def test_media(self, event: AstrMessageEvent, query: str, media_type: str = "all") -> AsyncGenerator[MessageEventResult, None]:
        """测试指令：手动触发媒体API查询"""
        start_time = time.time()
        
        group_id = event.get_group_id()
        if group_id:
            group_id = str(group_id)
        else:
            group_id = None
        
        logger.info(f"手动触发媒体API查询: query={query}, media_type={media_type}")
        result = await self._get_media_internal(query, media_type, group_id)
        
        elapsed_time = time.time() - start_time
        
        try:
            if "error" in result:
                # 构建错误消息
                error_msg = f"查询失败: {result['error']}\n耗时 {elapsed_time:.2f}s"
                
                # 如果有可用关键词，添加到消息中
                if result.get("keywords") and len(result['keywords']) > 0:
                    keywords_str = "、".join(result['keywords'][:20])
                    if len(result['keywords']) > 20:
                        keywords_str += f"等{result['keywords_count']}个关键词"
                    error_msg += f"\n\n可用关键词：{keywords_str}"
                
                yield event.plain_result(error_msg)
            else:
                # 先发送文本消息（包含耗时信息）
                yield event.plain_result(f"查询成功（耗时 {elapsed_time:.2f}s）")
                # 然后单独发送媒体资源（某些平台不支持文本和媒体混合发送）
                media_chain = []
                self._add_media_component(media_chain, result)
                if media_chain:  # 只有当媒体组件添加成功时才发送
                    yield event.chain_result(media_chain)
        except Exception as e:
            yield event.plain_result(f"处理结果时发生错误: {str(e)}")


    async def terminate(self) -> None:
        """插件卸载时调用"""
        # 停止配置管理器监控
        if hasattr(self.config_manager, 'stop_watching'):
            self.config_manager.stop_watching()
        logger.info("媒体API工具插件已卸载")
