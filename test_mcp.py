"""
MCP服务器测试脚本
用于直接测试MCP工具调用
"""
import asyncio
import json
import sys
import os

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_tool():
    """测试MCP工具调用"""
    # 配置服务器参数（通过stdio启动Python脚本）
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    # 创建客户端会话
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()
            
            print("=" * 60)
            print("MCP服务器连接成功！")
            print("=" * 60)
            
            # 1. 列出所有可用工具
            print("\n[1] 列出可用工具...")
            tools = await session.list_tools()
            print(f"找到 {len(tools.tools)} 个工具:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
                print(f"    参数: {json.dumps(tool.inputSchema, ensure_ascii=False, indent=4)}")
            
            # 2. 测试工具调用
            print("\n" + "=" * 60)
            print("[2] 测试工具调用")
            print("=" * 60)
            
            # 测试用例列表
            test_cases = [
                {
                    "name": "测试1: 获取自拍图片",
                    "query": "自拍",
                    "media_type": "image"
                },
                {
                    "name": "测试2: 获取热舞视频",
                    "query": "热舞",
                    "media_type": "video"
                },
                {
                    "name": "测试3: 获取黑丝视频",
                    "query": "黑丝",
                    "media_type": "video"
                },
                {
                    "name": "测试4: 测试无效关键词",
                    "query": "无效关键词123",
                    "media_type": "all"
                },
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{test_case['name']}")
                print(f"参数: query='{test_case['query']}', media_type='{test_case['media_type']}'")
                
                try:
                    # 调用工具
                    result = await session.call_tool(
                        "get_media",
                        arguments={
                            "query": test_case["query"],
                            "media_type": test_case["media_type"]
                        }
                    )
                    
                    # 解析结果
                    if result.content:
                        result_text = result.content[0].text
                        result_data = json.loads(result_text)
                        
                        print("结果:")
                        print(json.dumps(result_data, ensure_ascii=False, indent=2))
                        
                        if "error" in result_data:
                            print(f"[错误] {result_data['error']}")
                        else:
                            url = result_data.get('url', 'N/A')
                            url_preview = url[:80] + '...' if len(url) > 80 else url
                            print(f"[成功] URL={url_preview}, Type={result_data.get('type', 'N/A')}")
                    else:
                        print("[错误] 无返回内容")
                        
                except Exception as e:
                    print(f"[调用失败] {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                # 测试调用间冷却（避免请求过于频繁）
                if i < len(test_cases):
                    print("\n等待3秒后继续下一个测试...")
                    await asyncio.sleep(3)
            
            print("\n" + "=" * 60)
            print("测试完成！")
            print("=" * 60)


if __name__ == "__main__":
    print("开始测试MCP服务器...")
    print("确保已安装依赖: pip install mcp httpx watchdog")
    print()
    
    try:
        asyncio.run(test_mcp_tool())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[测试失败] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

