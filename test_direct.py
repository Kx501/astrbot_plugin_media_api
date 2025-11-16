"""
直接测试脚本 - 不通过MCP协议，直接调用函数
用于快速测试和调试
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

from mcp_server import get_media


async def test_direct():
    """直接测试get_media函数"""
    print("=" * 60)
    print("直接测试MCP服务器核心功能")
    print("=" * 60)
    
    # 测试用例列表
    test_cases = [
        {
            "name": "测试1: 获取自拍图片（精确匹配）",
            "query": "自拍",
            "media_type": "image",
            "group_id": None
        },
        {
            "name": "测试2: 获取自拍图片（部分匹配）",
            "query": "随机自拍图片",
            "media_type": "image",
            "group_id": None
        },
        {
            "name": "测试3: 获取黑丝视频（相似度匹配）",
            "query": "黑丝",
            "media_type": "video",
            "group_id": None
        },
        {
            "name": "测试4: 获取小姐姐视频（lolimi平台）",
            "query": "小姐姐",
            "media_type": "video",
            "group_id": None
        },
        {
            "name": "测试5: 测试无效关键词",
            "query": "无效关键词123",
            "media_type": "all",
            "group_id": None
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{test_case['name']}")
        print(f"参数: query='{test_case['query']}', media_type='{test_case['media_type']}'")
        
        try:
            # 直接调用函数
            result = await get_media(
                query=test_case["query"],
                media_type=test_case["media_type"],
                group_id=test_case["group_id"]
            )
            
            print("结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if "error" in result:
                print(f"[错误] {result['error']}")
            else:
                url = result.get('url', 'N/A')
                url_preview = url[:80] + '...' if len(url) > 80 else url
                print(f"[成功] URL={url_preview}, Type={result.get('type', 'N/A')}")
                
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
    print("开始直接测试MCP服务器核心功能...")
    print("确保已安装依赖: pip install -r requirements.txt")
    print("确保已配置config/config.json")
    print()
    
    try:
        asyncio.run(test_direct())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[测试失败] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
