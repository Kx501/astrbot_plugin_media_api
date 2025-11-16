# 多平台媒体API MCP服务器

一个用于QQ AI群聊bot的多平台媒体API集合MCP服务器，支持音视频和图片资源的获取。

## 功能特性

- ✅ **减少token消耗**：只有一个工具，返回格式最简化，只返回第一个结果
- ✅ **智能平台选择**：先按类型过滤，再相似度匹配关键词，最后随机选择
- ✅ **灵活的权限控制**：支持全局和群组两级禁用配置，可精确到单个API
- ✅ **高可靠性**：缓存机制和自动禁用机制
- ✅ **通用性**：支持非QQ Bot场景（group_id可选）
- ✅ **配置文件热重载**：修改配置后自动生效
- ✅ **详细日志**：方便调试和监控
- ✅ **相似度匹配**：支持精确匹配、部分匹配和模糊匹配

## 项目结构

```
media_api/
├── mcp_server.py          # MCP服务器主入口
├── config_manager.py       # 配置管理模块（支持热重载、全局/群组权限检查）
├── platform_base.py        # 平台抽象基类
├── cache_manager.py        # 缓存管理模块（成功缓存、失败回退）
├── failure_tracker.py     # 失败追踪模块（自动禁用机制）
├── keyword_registry.py    # 关键词注册表（相似度匹配）
├── platforms/              # 各平台API客户端
│   ├── __init__.py
│   ├── ak317_platform.py  # AK317平台实现
│   ├── xingchenfu_platform.py # 星晨福平台实现
│   ├── lolimi_platform.py # Lolimi平台实现
│   └── example_platform.py # 示例平台实现
├── config/                 # 配置文件目录
│   └── config.json         # 统一配置文件
├── requirements.txt        # Python依赖
├── README.md              # 项目文档
└── DESIGN.md              # 完整设计文档
```

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置

1. 复制配置文件模板：
```bash
cp config/config.json.example config/config.json
```

2. 编辑 `config/config.json`，填入你的API密钥：

```json
{
  "global": {
    "disabled_platforms": [],
    "disabled_apis": []
  },
  "groups": {},
  "platforms": {
    "ak317": {
      "ckey": "your-ckey-here"
    },
    "xingchenfu": {},
    "lolimi": {}
  }
}
```

**注意**：`config/config.json` 包含敏感信息，已被 `.gitignore` 忽略，不会提交到版本控制。

### 运行

```bash
python mcp_server.py
```

## 配置说明

### 配置文件结构

配置文件采用三层结构：

- **global**: 全局配置，影响所有群组

  - `disabled_platforms`: 全局禁用的平台列表
  - `disabled_apis`: 全局禁用的API列表（格式：`"平台名:api_id"`，如 `"ak317:hssp"`）
- **groups**: 群组配置，key为群组ID

  - `disabled_platforms`: 该群组额外禁用的平台列表
  - `disabled_apis`: 该群组额外禁用的API列表
- **platforms**: 平台配置，key为平台名称

  - `api_key`: API密钥（可选）

### 权限检查优先级

1. 全局禁用检查
2. 群组禁用检查（如果提供了group_id）
3. 平台是否已配置
4. 如果都通过，允许使用

详细配置说明请参考 [DESIGN.md](DESIGN.md)

## MCP工具

### get_media

获取媒体资源（唯一工具）

**参数**：

- `query`（必需）：搜索关键词
- `media_type`（可选）：媒体类型，默认"all"
  - 可选值：`"image"` / `"video"` / `"audio"` / `"all"`

**参数（不在schema中声明，但支持）**：

- `group_id`（可选）：群组ID，用于权限检查

**返回格式**：

```json
{
  "url": "https://example.com/image.jpg",
  "type": "image"
}
```

或错误：

```json
{
  "error": "错误信息"
}
```

## 已实现平台

### AK317平台

支持随机自拍图片和多个视频系列API。

**配置**：

```json
{
  "platforms": {
    "ak317": {
      "ckey": "你的CKEY值"
    }
  }
}
```

**使用方式**：

- 通过query参数匹配API标题（相似度匹配）：
  - **图片API**：`"自拍"` 或 `"随机自拍图片"` → 随机自拍图片
  - **视频API**（共25个）：
    - `"倾梦"`、`"猫系"`、`"少萝"`、`"女大学生"`、`"穿搭"`、`"热舞"`、`"双尾马"`、`"渔网"`、`"少萝妹妹"`、`"纯情女高"`
    - `"极品狱卒"`、`"玉足美腿"`、`"清纯"`、`"COS"`、`"萝莉"`、`"完美身材"`、`"蹲下变装"`、`"吊带"`、`"黑丝"`、`"女仆"`
    - `"又纯又欲"`、`"甩裙"`、`"白丝"`、`"黑白双煞"`、`"慢摇"`
- 支持相似度匹配，如 `"黑丝视频"` 可以匹配到 `"黑丝系列视频"`
- 如果未匹配到关键词，将返回错误提示并列出可用关键词

**示例**：

- query="自拍", media_type="image" → 返回随机自拍图片
- query="倾梦", media_type="video" → 返回倾梦推荐视频
- query="热舞", media_type="video" → 返回热舞系列视频
- query="黑丝", media_type="video" → 返回黑丝系列视频

### 星晨福平台

支持多个视频和图片API。

**配置**：

```json
{
  "platforms": {
    "xingchenfu": {}
  }
}
```

注意：此平台无需配置参数，可直接使用。

**使用方式**：

- 通过query参数匹配API标题（相似度匹配）：
  - **视频API**：
    - `"女大"` 或 `"女大学生"` → 女大学生视频
    - `"黑丝"` → 黑丝视频
    - `"白丝"` → 白丝视频
    - `"小姐姐"` → 小姐姐视频
    - `"jk"` 或 `"JK"` → JK视频
    - `"cos"` 或 `"COS"` → COS视频
  - **图片API**：
    - `"黑丝图片"` → 黑丝图片
    - `"美腿"` → 美腿图片
    - `"cosplay"` 或 `"cos图片"` → 随机cosplay图片
- 支持相似度匹配，如 `"黑丝"` 可以匹配到 `"黑丝视频"` 或 `"黑丝图片"`
- 如果未匹配到关键词，将返回错误提示并列出可用关键词

**示例**：

- query="女大", media_type="video" → 返回女大视频
- query="黑丝", media_type="video" → 返回黑丝视频
- query="jk", media_type="video" → 返回JK视频
- query="美腿", media_type="image" → 返回美腿图片
- query="cosplay", media_type="image" → 返回随机cosplay图片

### Lolimi平台

支持随机小姐姐视频API。

**配置**：

```json
{
  "platforms": {
    "lolimi": {}
  }
}
```

注意：此平台无需配置参数，可直接使用。

**使用方式**：

- 通过query参数匹配API标题（相似度匹配）：
  - `"小姐姐"` 或 `"高质量小姐姐视频"` → 高质量小姐姐视频
- 只支持video类型，不支持image或audio类型

**示例**：

- query="", media_type="video" → 返回随机视频
- query="小姐姐", media_type="video" → 返回随机视频

## 添加新平台

1. 在 `platforms/` 目录下创建新文件
2. 实现 `PlatformBase` 抽象类
3. 在 `platforms/__init__.py` 中注册平台

示例：

```python
from platform_base import PlatformBase, MediaResource

class MyPlatform(PlatformBase):
    def __init__(self):
        super().__init__("my_platform")
        
        # API映射：API标识 -> (URL, 标题, 媒体类型)
        self.api_map = {
            "api1": ("https://api.example.com/v1", "示例图片", "image"),
            "api2": ("https://api.example.com/v2", "示例视频", "video")
        }
        
        # 从api_map自动注册所有API到全局注册表
        self.register_apis_from_map(self.api_map)
  
    async def search_media(self, query, media_type="all", config=None, limit=10, api_id=None):
        # api_id由MCP服务器传入，根据api_id调用对应的API
        if not api_id or api_id not in self.api_map:
            raise Exception(f"未找到API标识{api_id}")
        
        api_url, title, api_media_type = self.api_map[api_id]
        # 实现搜索逻辑
        return [MediaResource(url="...", media_type=api_media_type)]
  
    async def get_media_by_id(self, media_id, config=None):
        # 可选实现
        return None
  
    def get_available_apis(self):
        return ["search"]  # 必须包含"search"
    
    def get_supported_media_types(self):
        # 从api_map中提取所有唯一的媒体类型
        media_types = set()
        for _, _, media_type in self.api_map.values():
            media_types.add(media_type)
        return list(media_types)
```

然后在 `platforms/__init__.py` 中注册：

```python
from .my_platform import MyPlatform

PLATFORMS = {
    "my_platform": MyPlatform,
}
```

## 核心机制

### 匹配流程

1. **权限过滤**：检查平台是否被禁用
2. **类型过滤**：检查平台是否支持请求的媒体类型
3. **关键词匹配**：使用相似度匹配找到匹配的API（返回 `platform, api_id, media_type`）
4. **API禁用检查**：检查匹配到的API是否被禁用（格式：`platform:api_id`）
5. **随机选择**：从匹配且启用的API中随机选择一个
6. **调用API**：传入 `api_id` 调用平台API

### 缓存机制

- 成功时缓存API响应结果
- 失败时使用缓存结果响应
- 缓存key：`query + media_type + platform`
- 默认过期时间：1小时

### 自动禁用机制

- 连续失败N次（默认3次）后自动禁用
- 禁用格式：`platform:api_id`（如 `"ak317:hssp"`）
- 自动禁用只影响群组配置，不会修改全局配置

### 日志系统

记录关键信息：

- 工具调用（参数、选择的平台）
- API调用（成功/失败）
- 缓存命中/未命中
- 自动禁用事件

## 技术栈

- Python 3.8+
- `mcp` SDK（MCP协议实现）
- `httpx`（异步HTTP请求）
- `watchdog`（配置文件热重载监控）

## 详细文档

完整的设计文档请参考 [DESIGN.md](DESIGN.md)

## 许可证

MIT
