"""
AstrBot专用MCP服务器入口
"""
import json
import random
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

from config_manager import ConfigManager
from cache_manager import CacheManager
from failure_tracker import FailureTracker
from keyword_registry import get_registry
from platforms import get_platform


class MediaApiTool(Star):
    """
    AstrBot 媒体API工具插件
    提供多平台媒体资源获取功能（图片/视频/音频）
    """
    def __init__(self, context: Context, config: AstrBotConfig = None):
        """插件初始化"""
        super().__init__(context)
        
        # 初始化全局管理器
        self.config_manager = ConfigManager()
        self.cache_manager = CacheManager()
        self.failure_tracker = FailureTracker(self.config_manager)
        self.keyword_registry = get_registry()
        
        logger.info("媒体API工具插件已加载")

    @filter.llm_tool(name="get_media")
    async def get_media(self, event: AstrMessageEvent, query: str, media_type: str = "all") -> str:
        """
        获取媒体资源的LLM工具，支持通过关键词搜索图片、视频、音频等媒体资源。
        工具会自动匹配关键词，从可用的平台中随机选择一个API来获取媒体资源。
        
        Args:
            query(string): 搜索关键词，例如"猫猫"、"风景"、"音乐"等
            media_type(string): 媒体类型，可选值："image"/"video"/"audio"/"all"，默认为"all"
        
        Returns:
            返回JSON字符串，成功时包含url和type字段，失败时包含error字段
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
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"获取媒体资源时发生错误: {e}，耗时 {elapsed_time:.2f}s", exc_info=True)
            return json.dumps({"error": f"获取媒体资源时发生内部错误: {str(e)}"}, ensure_ascii=False)

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
                    keywords_str = "、".join(all_keywords[:20])  # 最多显示20个关键词
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

    @filter.command("测试媒体", alias={"test_media"})
    async def test_media(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """测试指令：手动触发媒体API查询"""
        start_time = time.time()
        
        # 从消息中提取参数（简单示例，实际可能需要更复杂的解析）
        message_text = event.get_message_text() if hasattr(event, 'get_message_text') else ""
        
        # 简单解析：假设格式为 "测试媒体 关键词 [类型]"
        parts = message_text.split()
        if len(parts) < 2:
            yield event.plain_result("用法：测试媒体 <关键词> [类型]\n例如：测试媒体 猫猫 image")
            return
        
        query = parts[1]
        media_type = parts[2] if len(parts) > 2 else "all"
        
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
                yield event.plain_result(f"查询失败: {result['error']}\n耗时 {elapsed_time:.2f}s")
            else:
                result_text = f"查询成功（耗时 {elapsed_time:.2f}s）:\n"
                result_text += f"类型: {result.get('type', '未知')}\n"
                result_text += f"URL: {result.get('url', '未知')}"
                yield event.plain_result(result_text)
        except Exception as e:
            yield event.plain_result(f"处理结果时发生错误: {str(e)}")

    async def terminate(self) -> None:
        """插件卸载时调用"""
        # 停止配置管理器监控
        if hasattr(self.config_manager, 'stop_watching'):
            self.config_manager.stop_watching()
        logger.info("媒体API工具插件已卸载")

