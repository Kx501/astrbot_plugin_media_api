"""
通用MCP服务器主入口
提供多平台媒体API的MCP工具
"""
import asyncio
import json
import random
import logging
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from config_manager import ConfigManager
from cache_manager import CacheManager
from failure_tracker import FailureTracker
from keyword_registry import get_registry
from platforms import get_platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局管理器
config_manager = ConfigManager()
cache_manager = CacheManager()
failure_tracker = FailureTracker(config_manager)
keyword_registry = get_registry()
logger.info("Global managers initialized successfully")


async def get_media(
    query: str,
    media_type: str = "all",
    group_id: Optional[str] = None
) -> dict:
    """
    获取媒体资源（核心工具）
    
    Args:
        query: 搜索关键词
        media_type: 媒体类型，默认"all"
        group_id: 群组ID（可选，不在schema中声明）
    
    Returns:
        结果字典，包含url和type，或error
    """
    logger.info(f"get_media called: query={query}, media_type={media_type}, group_id={group_id}")
    
    try:
        # 1. 预处理：按权限过滤平台
        all_available_platforms = config_manager.get_available_platforms(group_id)
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
        matching_apis = keyword_registry.find_matching_apis(
            query=query,
            available_platforms=type_filtered_platforms,
            media_type=media_type
        )
        
        if not matching_apis:
            # 匹配失败，返回错误提示
            all_keywords = keyword_registry.get_all_keywords()
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
            if config_manager.is_api_enabled(group_id, platform, api_id):
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
        platform_config = config_manager.get_platform_config(platform)
        
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
            cache_manager.set_cache(query, media_type, platform, result)
            logger.info(f"Successfully got media from {platform}, cached")
            
            # 11. 重置失败计数（使用api_id）
            failure_tracker.reset_failure(platform, api_id, group_id)
            
            return result
            
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            logger.error(f"{platform} API error: {error_msg}")
            
            # 12. 记录失败（使用api_id）
            failure_tracker.record_failure(platform, api_id, group_id)
            
            # 13. 尝试使用缓存（失败时的备用方案）
            cached_result = cache_manager.get_cache(query, media_type, platform)
            if cached_result:
                logger.info(f"Using cached result after failure")
                return cached_result
            
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"获取媒体资源失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


# 创建MCP服务器
server = Server("media-api-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具（只有一个工具）"""
    logger.info("list_tools called, returning get_media tool")
    tool = Tool(
        name="get_media",
        description="通过API获取各种媒体资源（图片/视频/音频）",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "media_type": {
                    "type": "string",
                    "description": "媒体类型：image/video/audio/all",
                    "default": "all"
                }
            },
            "required": ["query"]
        }
    )
    logger.info(f"Tool registered: {tool.name}")
    return [tool]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "get_media":
            # group_id不在schema中声明，由astrbot框架根据消息上下文自动注入
            # LLM不会看到此参数，也不会尝试填充
            result = await get_media(
                query=arguments.get("query"),
                media_type=arguments.get("media_type", "all"),
                group_id=arguments.get("group_id")  # 由框架自动注入，不在schema中
            )
            
            # 返回JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            return [TextContent(type="text", text=result_json)]
        else:
            error_result = {"error": f"未知工具: {name}"}
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
    except Exception as e:
        error_result = {"error": f"工具调用失败: {str(e)}"}
        logger.error(f"Tool call error: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]


async def main():
    """主函数"""
    logger.info("Starting MCP server...")
    logger.info(f"Server name: {server.name}")
    
    # 验证工具注册
    try:
        tools = await server.list_tools()
        logger.info(f"Registered {len(tools)} tool(s): {[t.name for t in tools]}")
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
