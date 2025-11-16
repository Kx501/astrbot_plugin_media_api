# MCP服务器测试指南

## 一、启动和配置MCP服务器

### 1. 安装依赖

首先确保已安装所有必需的Python包：

```bash
pip install -r requirements.txt
```

如果`requirements.txt`为空，需要手动安装：

```bash
pip install mcp httpx watchdog
```

### 2. 配置服务器

如果 `config/config.json` 不存在，先复制模板：

```bash
# Windows PowerShell
Copy-Item config\config.json.example config\config.json

# Linux/Mac
cp config/config.json.example config/config.json
```

然后编辑 `config/config.json` 文件，配置平台参数：

```json
{
  "global": {
    "disabled_platforms": [],
    "disabled_apis": []
  },
  "groups": {},
  "platforms": {
    "ak317": {
      "ckey": "YOUR_CKEY_HERE"
    },
    "xingchenfu": {},
    "lolimi": {}
  }
}
```

**配置说明**：
- `ak317`平台需要配置`ckey`参数（替换`YOUR_CKEY_HERE`为实际值）
- `xingchenfu`和`lolimi`平台无需配置参数
- `global.disabled_platforms`: 全局禁用的平台列表
- `global.disabled_apis`: 全局禁用的API列表（格式：`"平台名:api_id"`，如 `"ak317:hssp"`）
- `groups`: 群组特定配置（可选）

**重要**：`config/config.json` 包含敏感信息，已被 `.gitignore` 忽略，不会提交到版本控制。

### 3. 启动MCP服务器

MCP服务器通过stdio通信，有两种使用方式：

#### 方式1: 直接运行（用于测试）

```bash
python mcp_server.py
```

服务器会通过标准输入/输出进行通信。这种方式主要用于调试。

#### 方式2: 作为MCP服务器运行（推荐）

在支持MCP的客户端（如Claude Desktop、Cursor等）中配置：

**Claude Desktop配置示例** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "media-api": {
      "command": "python",
      "args": ["C:/Users/Hua/Desktop/work/PyProjects/media_api/mcp_server.py"],
      "cwd": "C:/Users/Hua/Desktop/work/PyProjects/media_api"
    }
  }
}
```

**Cursor配置示例** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "media-api": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "C:/Users/Hua/Desktop/work/PyProjects/media_api"
    }
  }
}
```

## 二、使用测试脚本进行自测

### 方式1: 直接测试（推荐，快速）

直接调用核心函数，不通过MCP协议：

```bash
python test_direct.py
```

**优点**：
- 快速，无需MCP协议通信
- 直接测试核心逻辑
- 适合开发和调试

**测试用例**：
- 获取自拍图片
- 获取热舞视频
- 获取黑丝视频
- 测试无效关键词（验证错误处理）
- 测试lolimi平台（任意关键词）

### 方式2: MCP协议测试（完整测试）

通过MCP协议完整测试：

```bash
python test_mcp.py
```

**优点**：
- 完整测试MCP协议通信
- 验证工具列表功能
- 模拟真实使用场景

**测试内容**：
1. 连接到MCP服务器
2. 列出所有可用工具
3. 执行多个测试用例（同方式1）

### 测试输出示例

```
============================================================
MCP服务器连接成功！
============================================================

[1] 列出可用工具...
找到 1 个工具:
  - get_media: 获取媒体资源（图片/视频/音频）
    参数: {
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

============================================================
[2] 测试工具调用
============================================================

测试1: 获取自拍图片
参数: query='自拍', media_type='image'
结果:
{
  "url": "https://example.com/image.jpg",
  "type": "image"
}
✅ 成功: URL=https://example.com/image.jpg, Type=image
```

## 三、手动测试（使用Python交互式调用）

你也可以在Python中直接调用MCP工具函数进行测试：

```python
import asyncio
from mcp_server import get_media

async def test():
    # 测试获取自拍图片
    result = await get_media("自拍", "image")
    print(result)
    
    # 测试获取热舞视频
    result = await get_media("热舞", "video")
    print(result)

asyncio.run(test())
```

## 四、常见问题排查

### 1. 连接失败

- 检查Python路径是否正确
- 确保所有依赖已安装
- 检查`mcp_server.py`文件是否存在语法错误

### 2. 工具调用返回错误

- 检查`config/config.json`配置是否正确
- 查看服务器日志输出
- 确认平台API密钥（如ak317的ckey）是否有效

### 3. 关键词匹配失败

- 查看`keyword_registry.py`中注册的关键词
- 确保query参数使用正确的中文关键词
- 参考README.md中每个平台支持的关键词列表

### 4. 平台不可用

- 检查`config/config.json`中的`disabled_platforms`配置
- 查看失败追踪日志，确认平台是否被自动禁用
- 检查平台配置是否完整（如ak317需要ckey）

## 五、日志查看

MCP服务器会输出详细日志，包括：
- 工具调用参数
- 平台选择过程
- API调用结果
- 缓存命中/未命中
- 错误信息

日志格式：
```
2024-01-01 12:00:00 - __main__ - INFO - get_media called: query=自拍, media_type=image, group_id=None
2024-01-01 12:00:00 - __main__ - INFO - Selected platform: ak317
2024-01-01 12:00:00 - __main__ - INFO - Successfully got media from ak317, cached
```

## 六、下一步

测试通过后，你可以：
1. 在QQ Bot中集成MCP服务器
2. 配置群组权限（在`groups`字段中添加群组ID）
3. 添加更多平台支持
4. 调整缓存和失败追踪参数

